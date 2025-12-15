from abc import abstractmethod
import httpx
from src.storage.database import Database
from src.storage.model import jobs


class BaseScraper(Database):
    def __init__(self, name: str, link: str,  companyid: int, domain: str = "") -> None:
        super().__init__()
        self.name = name
        self.link = link
        self.domain = domain
        self.companyid = companyid
        self.create_db_and_tables()


    @staticmethod
    def get_html(url: str) -> str:
        """Extract the html from a url"""
        response = httpx.get(url)
        print(response)
        response.raise_for_status()
        return response.text


    @staticmethod
    def validate_data(job_details: dict):
        """Validate Scraped job info"""
        scraped_job = jobs(**job_details)
        return scraped_job
    

    @abstractmethod
    def get_positions(self) -> list[str]:
        """Extract the position links"""
        pass

    @abstractmethod
    def get_position_details(self, position_link: str) -> dict:
        """Extract position details"""
        print(f"POSITION - {position_link}")
        pass


    def main(self) -> None:
        print(self.name)
        positions = self.get_positions()
        for position in positions:
            try:
                job_details = self.get_position_details(position)
                parsed_position = self.validate_data(job_details)
                print(parsed_position)

                self.send_job(parsed_position)
            except Exception as e:
                print(f"ERROR - {str(e)}")

