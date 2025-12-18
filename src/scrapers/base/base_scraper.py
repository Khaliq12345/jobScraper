from abc import abstractmethod
import httpx
from src.storage.database import Database
from src.storage.model import jobs
from src.utils import static
from functools import partial
from geopy.geocoders import Nominatim

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
        print(response.url)
        response.raise_for_status()
        return response.text


    @staticmethod
    def validate_data(job_details: dict):
        """Validate Scraped job info"""
        scraped_job = jobs(**job_details)
        geolocator = Nominatim(user_agent="my-app")
        geocode = partial(geolocator.geocode, language="en")

        # Job qualification
        if not scraped_job.jobqualifications:
            for qualification in static.qualifications:
                if qualification.lower() in scraped_job.jobdescription:
                    scraped_job.jobqualifications = qualification
                else:
                    scraped_job.jobqualifications = "General"

        # Job exprience
        if not scraped_job.jobexperience:
            for exprience in static.experienceLevels:
                if exprience.lower() in scraped_job.jobdescription:
                    scraped_job.jobexperience = exprience.replace(' ', '-')
                else:
                    scraped_job.jobexperience = "General"

        # Job pattern
        if not scraped_job.jobpattern:
            for pattern in static.workPatterns:
                if pattern.lower() in scraped_job.jobpattern:
                    scraped_job.jobpattern = pattern.replace(' ', '-')

                else:
                    scraped_job.jobpattern = "full-time"

        if not scraped_job.jobniche:
            scraped_job.jobniche = "Job"

        # Job salary
        if not scraped_job.jobsalary:
            scraped_job.jobsalary = static.jobSalary_default
            
        # country and state
        if job_details.get("parse_location"):
            country_raw = geocode(scraped_job.jobcountry)
            if not country_raw:
                scraped_job.jobaddress = "Same As Country"
                scraped_job.jobcountry = "Global"
            else:
                country_raw = country_raw.raw
                print(country_raw)
                if not country_raw.get("name"):
                    scraped_job.jobcountry = "Same As Address"
                    scraped_job.jobaddress = scraped_job.jobcountry
                else:
                    if country_raw.get("addresstype") == "country":
                        scraped_job.jobcountry = country_raw.get("name")
                        scraped_job.jobaddress = "Same As Country"
                    else:
                        scraped_job.jobaddress = country_raw.get("name")
                        if "," in country_raw.get("display_name"):
                            scraped_job.jobcountry = country_raw.get("display_name").split(",")[-1].strip()
                        else:
                            scraped_job.jobcountry = "Same As Address"

        scraped_job.jobsalary = scraped_job.jobsalary.replace("Salary:", "")

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

                # self.send_job(parsed_position)
            except Exception as e:
                print(f"ERROR - {str(e)}")

