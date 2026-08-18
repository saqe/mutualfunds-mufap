import cloudscraper

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

response = scraper.get("https://www.mufap.com.pk/Industry/IndustryStatDaily?tab=1")
response.raise_for_status()

print(response.text)
