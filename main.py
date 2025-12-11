from src.scrapers.base.base_scraper import BaseScraper


if __name__ == "__main__":
    scraper = BaseScraper(name="Airbnb", link="https://careers.airbnb.com/positions/", positions_selector="ul.job-list li")
    scraper.main()
