import argparse
import sys
import time
from urllib.parse import urlparse

import cloudscraper
import requests
from bs4 import BeautifulSoup


def is_http_url(value):
    try:
        result = urlparse(value)
        # Check that both scheme and network location (domain) are present
        return result.scheme in ("http", "https") and bool(result.netloc)
    except ValueError:
        return False


def make_scraper():
    return cloudscraper.create_scraper(
        # Challenge handling
        interpreter="js2py",  # Best compatibility for v3 challenges
        delay=5,  # Extra time for complex challenges
        # Stealth mode
        enable_stealth=True,
        stealth_options={
            "min_delay": 2.0,
            "max_delay": 6.0,
            "human_like_delays": True,
            "randomize_headers": True,
            "browser_quirks": True,
        },
        # Browser emulation
        browser="chrome",
    )


MAX_ATTEMPTS = 5
BASE_DELAY = 5  # seconds; doubles each attempt (5, 10, 20, 40)
RETRY_STATUSES = {403, 404, 408, 429, 500, 502, 503, 504}


def fetch(url, expect=None):
    """GET url, retrying transient failures with exponential backoff.

    Retries on connection errors, HTTP 403/404/408/429/5xx, and (when `expect`
    is given) a 200 response whose HTML has no element matching that CSS
    selector, e.g. a Cloudflare challenge page. A fresh session is used for
    every attempt. Returns the response.
    """
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = make_scraper().get(url, timeout=60)
            if response.status_code in RETRY_STATUSES:
                last_error = f"HTTP {response.status_code}"
            else:
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                if expect is None or soup.select_one(expect) is not None:
                    return soup
                last_error = f"response has no element matching {expect!r}"
        except requests.exceptions.RequestException as e:
            last_error = repr(e)
        if attempt < MAX_ATTEMPTS:
            delay = BASE_DELAY * 2 ** (attempt - 1)
            print(f"attempt {attempt}/{MAX_ATTEMPTS} failed for {url}: {last_error}; "
                  f"retrying in {delay}s", file=sys.stderr)
            time.sleep(delay)
    sys.exit(f"giving up on {url} after {MAX_ATTEMPTS} attempts: {last_error}")


def main():
    parser = argparse.ArgumentParser(description="Fetch a page past Cloudflare")
    parser.add_argument("url")
    parser.add_argument("--expect", metavar="CSS_SELECTOR",
                        help="treat a response without a matching element as a failure and retry")
    args = parser.parse_args()

    if not is_http_url(args.url):
        sys.exit(f"not an http(s) URL: {args.url}")
    print(fetch(args.url, args.expect).prettify())


if __name__ == "__main__":
    main()
