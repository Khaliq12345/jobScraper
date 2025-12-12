from src.scrapers.wise import Wise


if __name__ == "__main__":
    # db = Database()
    # db.get_jobs()
    scraper = Wise()
    scraper.main()
