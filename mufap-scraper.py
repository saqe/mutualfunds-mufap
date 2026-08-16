import cloudscraper
scraper = cloudscraper.create_scraper()
print(scraper.get("https://www.mufap.com.pk/Industry/IndustryStatDaily?tab=1").text)
