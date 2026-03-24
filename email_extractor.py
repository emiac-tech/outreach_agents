import re
import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from playwright.async_api import async_playwright
import uvicorn

app = FastAPI(title="Email Extractor API", version="1.0.0")

# ── Pages to check for emails ────────────────────────────────────────────────
TARGET_PATHS = [
    "/",
    "/contact",
    "/contact-us",
    "/about",
    "/about-us",
    "/team",
    "/our-team",
    "/support",
    "/help",
    "/info",
    "/reach-us",
    "/get-in-touch",
    "/connect",
    "/privacy",
    "/privacy-policy",
    "/terms",
    "/sitemap.xml",
    # Write for us pages
    "/write-for-us",
    "/writing-for-us",
    "/contribute",
    "/contributors",
    "/submit",
    "/submit-article",
    "/guest-post",
    "/submissions",
    # Press / Media pages
    "/press",
    "/press-releases",
    "/press-release",
    "/media",
    "/media-kit",
    "/newsroom",
    "/news-room",
    # Letters / Editor pages
    "/letters",
    "/letters-editor",
    "/letters-to-the-editor",
    "/letter-to-editor",
    "/editorial",
    "/editor",
    # Advertising / Business
    "/advertise",
    "/advertise-with-us",
    "/advertising",
    "/partnerships",
    "/sponsors",
    "/careers",
    "/jobs",
    # Corporate pages
    "/corporate",
    "/corporate-and-sponsored-content",
]

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

BLACKLISTED_DOMAINS = {
    "example.com", "domain.com", "email.com", "yoursite.com",
    "sentry.io", "w3.org", "schema.org", "googleapis.com",
    "wixpress.com", "cloudflare.com", "amazonaws.com"
}

# Status codes that indicate the site is blocking us
BLOCKED_STATUS_CODES = {403, 429, 500, 502, 503, 521, 522, 523}

# Max concurrent requests
MAX_CONCURRENT = 10


class ExtractRequest(BaseModel):
    url: str
    deep_scan: Optional[bool] = False  # Kept for backward compatibility, but ignored


class EmailResult(BaseModel):
    url: str
    status: str  # "Found" | "No Email Found" | "Blocked" | "Unreachable"
    emails: List[str]
    pages_checked: List[str]
    total_found: int


def normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def extract_emails_from_text(text: str) -> set:
    """Extract emails from raw text using regex."""
    found = set(EMAIL_REGEX.findall(text))
    clean = set()
    for email in found:
        domain = email.split("@")[1].lower()
        if domain not in BLACKLISTED_DOMAINS and not domain.endswith(".png") \
                and not domain.endswith(".jpg") and not domain.endswith(".svg"):
            clean.add(email.lower())
    return clean


def extract_mailto_emails(html: str) -> set:
    """Extract emails from mailto: links in the HTML."""
    soup = BeautifulSoup(html, "html.parser")
    emails = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if href.lower().startswith("mailto:"):
            raw = href[7:].split("?")[0].strip()
            if raw and "@" in raw:
                domain = raw.split("@")[1].lower()
                if domain not in BLACKLISTED_DOMAINS:
                    emails.add(raw.lower())
    return emails


def extract_all_emails_from_html(html: str) -> set:
    """Extract emails from both raw text AND mailto: links."""
    emails = extract_emails_from_text(html)
    emails.update(extract_mailto_emails(html))
    return emails


def extract_internal_links(html: str, base_url: str, limit: int = 20) -> List[str]:
    """Find internal links on a page for deeper crawling."""
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc
    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
            clean = parsed.scheme + "://" + parsed.netloc + parsed.path
            links.add(clean.rstrip("/"))
    return list(links)[:limit]


# ── Fast httpx fetch ──────────────────────────────────────────────────────────
async def fetch_page_httpx(
    client: httpx.AsyncClient,
    url: str,
    semaphore: asyncio.Semaphore,
) -> tuple[Optional[str], Optional[int]]:
    """Fast fetch using httpx. Returns (html, status_code)."""
    async with semaphore:
        try:
            resp = await client.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text, 200
            return None, resp.status_code
        except Exception:
            return None, None


# ── Browser fetch for blocked sites ───────────────────────────────────────────
async def fetch_pages_with_browser(urls: List[str]) -> dict[str, Optional[str]]:
    """Use a real browser (Playwright) to load pages that httpx can't access."""
    results = {}
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=HEADERS["User-Agent"],
                ignore_https_errors=True,
            )

            # Process pages concurrently in batches
            semaphore = asyncio.Semaphore(3)  # 3 browser tabs at a time

            async def load_page(url: str):
                async with semaphore:
                    page = await context.new_page()
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        await page.wait_for_timeout(2000)  # Let JS render
                        html = await page.content()
                        results[url] = html
                    except Exception:
                        results[url] = None
                    finally:
                        await page.close()

            await asyncio.gather(*[load_page(url) for url in urls])
            await browser.close()
    except Exception:
        for url in urls:
            if url not in results:
                results[url] = None
    return results


@app.post("/extract-emails", response_model=EmailResult)
async def extract_emails(request: ExtractRequest):
    provided_url = normalize_url(request.url)
    parsed = urlparse(provided_url)
    domain_root = parsed.scheme + "://" + parsed.netloc
    all_emails = set()
    checked_pages = []
    blocked_urls = []  # URLs that httpx couldn't load (403/500/etc.)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # Build the full list of pages to check using the DOMAIN ROOT
    pages_to_check = [domain_root + path for path in TARGET_PATHS]

    # Also add the exact URL the user provided
    if provided_url not in pages_to_check:
        pages_to_check.insert(0, provided_url)

    async with httpx.AsyncClient(verify=False) as client:
        # ── STEP 1: Try all pages with fast httpx first ───────────────────
        # De-duplicate
        seen = set()
        unique_pages = []
        for page_url in pages_to_check:
            if page_url not in seen:
                seen.add(page_url)
                unique_pages.append(page_url)

        tasks = [fetch_page_httpx(client, url, semaphore) for url in unique_pages]
        results = await asyncio.gather(*tasks)

        for page_url, (html, status_code) in zip(unique_pages, results):
            if status_code in BLOCKED_STATUS_CODES:
                blocked_urls.append(page_url)
            elif html:
                emails = extract_all_emails_from_html(html)
                all_emails.update(emails)
                checked_pages.append(page_url)

                # Extract internal links from the first loaded page
                if len(checked_pages) == 1:
                    internal_links = extract_internal_links(html, domain_root, limit=15)
                    for link in internal_links:
                        if link not in seen:
                            seen.add(link)
                            # Fetch these extra links too
                            extra_html, extra_status = await fetch_page_httpx(
                                client, link, semaphore
                            )
                            if extra_status in BLOCKED_STATUS_CODES:
                                blocked_urls.append(link)
                            elif extra_html:
                                all_emails.update(extract_all_emails_from_html(extra_html))
                                checked_pages.append(link)

    # ── STEP 2: If httpx got blocked, retry blocked URLs with real browser ──
    if blocked_urls and not all_emails:
        # Limit browser retry to the most important pages
        priority_urls = []
        # Always include the provided URL
        if provided_url in blocked_urls:
            priority_urls.append(provided_url)
        # Add domain root pages
        for url in blocked_urls:
            if url not in priority_urls and len(priority_urls) < 15:
                priority_urls.append(url)

        browser_results = await fetch_pages_with_browser(priority_urls)

        for url, html in browser_results.items():
            if html:
                emails = extract_all_emails_from_html(html)
                all_emails.update(emails)
                checked_pages.append(url)

    # ── Determine status ──────────────────────────────────────────────────────
    if all_emails:
        status = "Found"
    elif blocked_urls and not checked_pages:
        status = "Blocked"
    elif not checked_pages:
        status = "Unreachable"
    else:
        status = "No Email Found"

    return EmailResult(
        url=provided_url,
        status=status,
        emails=sorted(all_emails),
        pages_checked=checked_pages,
        total_found=len(all_emails)
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("email_extractor:app", host="0.0.0.0", port=8000, reload=True)
