import cloudscraper
import sys

from urllib.parse import urlparse

def is_http_url(value):
    try:
        result = urlparse(value)
        # Check that both scheme and network location (domain) are present
        return result.scheme in ('http', 'https') and bool(result.netloc)
    except ValueError:
        return False
        
scraper = cloudscraper.create_scraper(
    # Challenge handling
    interpreter='js2py',        # Best compatibility for v3 challenges
    delay=5,                    # Extra time for complex challenges

    # Stealth mode
    enable_stealth=True,
    stealth_options={
        'min_delay': 2.0,
        'max_delay': 6.0,
        'human_like_delays': True,
        'randomize_headers': True,
        'browser_quirks': True
    },

    # Browser emulation
    browser='chrome',
)

url = sys.argv[1]

if is_http_url(url):
    response = scraper.get(url)
    response.raise_for_status()
    print(response.text)
