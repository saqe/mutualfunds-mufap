from bs4 import BeautifulSoup
import cloudscraper
import requests
import sys
import time

from requests.adapters import HTTPAdapter
from requests.sessions import Session
from urllib3.util.retry import Retry

from urllib.parse import urlparse
from urllib3.util import Retry


def is_http_url(value):
    try:
        result = urlparse(value)
        # Check that both scheme and network location (domain) are present
        return result.scheme in ('http', 'https') and bool(result.netloc)
    except ValueError:
        return False
        
scraper: Session = cloudscraper.create_scraper(
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
# Add retry for the session if failed.
scraper.mount('https://', HTTPAdapter(max_retries=Retry(
    total=3, # Total number of retries to allow
    connect=3,                # How many connection errors to retry on
    read=3,
    backoff_factor=0.1,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(['GET']),
)))

MAX_ATTEMPTS = 5
BASE_DELAY = 5  # seconds; doubles each attempt (5, 10, 20, 40)
RETRY_STATUSES = {403, 404, 408, 429, 500, 502, 503, 504}


def fetch(url):
    """GET url, retrying transient failures (dropped connections, Cloudflare
    403s, flaky 404/5xx) with exponential backoff. Returns the response."""
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = scraper.get(url, timeout=60)
            if response.status_code not in RETRY_STATUSES:
                response.raise_for_status()
                return response
            last_error = f"HTTP {response.status_code}"
        except requests.exceptions.RequestException as e:
            last_error = repr(e)
        if attempt < MAX_ATTEMPTS:
            delay = BASE_DELAY * 2 ** (attempt - 1)
            print(f"attempt {attempt}/{MAX_ATTEMPTS} failed for {url}: {last_error}; "
                  f"retrying in {delay}s", file=sys.stderr)
            time.sleep(delay)
    sys.exit(f"giving up on {url} after {MAX_ATTEMPTS} attempts: {last_error}")


url = sys.argv[1]

if is_http_url(url):
    response = fetch(url)
    print(BeautifulSoup(response.content, 'html.parser').prettify())
