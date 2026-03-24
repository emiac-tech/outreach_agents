import csv

input_file = '/Users/sakshiagarwal/Downloads/Rough Data for Agent Testing - Data from different Google Search.csv'
output_file = 'output_table.csv'

# Rules for categorization
def categorize(url, domain, niche):
    domain = domain.lower()
    
    # Community
    if 'forum' in url or 'sellercentral' in domain or 'arabiantalks' in domain or 'community' in url:
        return "community", "Discussion forum or community portal focused on user interactions."

    # Promotional (E-commerce / Corporate / Brands)
    if 'amazon' in domain or '.sa' in domain or 'guess.sa' in domain or 'gymshark' in domain or 'calvinklein' in domain or 'mamasandpapas' in domain or 'buffalowildwings' in domain or 'rustoleum' in domain or 'michaelkors' in domain:
        if 'investors' in domain or 'bsf.sa' in domain or 'seera.sa' in domain:
            return "promotional", "Government portal or corporate investor relations page, not a publishing site."
        return "promotional", "Corporate brand website or e-commerce store prioritizing product/service sales without publishing."

    # Services / SaaS / Agencies / Marketplaces
    if 'guestpost' in domain or 'seo' in domain or 'upwork.com' in domain or 'freelancer' in domain or 'scribd.com' in domain or 'collaborator.pro' in domain or 'semalt' in domain or 'prposting' in domain or 'marketing' in domain or 'digital' in domain or 'agency' in domain or 'techasoft' in domain or 'roimantra' in domain:
        return "service", "Offers digital marketing, SEO, guest posting services, or acts as a freelance/document marketplace."
        
    # Overlapping PR Posting logic (News / Publishable blogs)
    if niche in ['News'] or 'news' in domain or 'al-monitor' in domain or 'majalla' in domain or 'arabnews' in domain or 'aljazeera' in domain or 'bbc.com' in domain or 'khaleejtimes' in domain or 'thenationalnews' in domain or 'theguardian' in domain:
        return "PR posting", "Recognized news portal accepting PR/sponsored editorial submissions."
        
    if 'write-for-us' in url.lower() or 'contribute' in url.lower() or 'submission' in url.lower() or 'guest-post' in url.lower() or 'blog' in url.lower():
        return "PR posting", "Blog or online magazine explicitly offering guest post and contribution guidelines."
        
    # Default Service
    return "service", "Typical corporate agency or service provider portal."

table_rows = []
table_rows.append("Website Name,URL,Category,Reason")

seen = set()
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        url = row['Website URL']
        domain = row['Website Domain']
        niche = row['Niche']
        
        if not url or url in seen:
            continue
        seen.add(url)
        
        name = domain.replace('www.', '')
        cat, reason = categorize(url, domain, niche)
        # Escape for CSV
        reason = reason.replace('"', '""')
        table_rows.append(f'"{name}","{url}","{cat}","{reason}"')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(table_rows))
