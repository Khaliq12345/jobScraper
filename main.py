from src.scrapers.base.base_scraper import BaseScraper


if __name__ == "__main__":
    # db = Database()
    # db.get_jobs()
    scraper = BaseScraper(name="Wise", link="https://wise.jobs/jobs", positions_selector="div.attrax-vacancy-tile", domain="https://wise.jobs")
    scraper.main()
