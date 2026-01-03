from country_named_entity_recognition import find_countries
from time import sleep, time

import httpx
from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Capgemini(BaseScraper):
    def __init__(self, save: bool) -> None:
        super().__init__(
            name="Capgemini",
            link="https://www.capgemini.com/wp-json/macs/v1/jobs?size=5000",
            domain="https://www.capgemini.com",
            companyid=47,
            save=save
        )


    def get_positions(self) -> list[str]:
        response = httpx.get(f"{self.link}", timeout=60)
        print(response)
        json_data = response.json()

        jobs = json_data["data"]
        print(f"ALL JOBS - {len(jobs)}") 

        return jobs

    def get_position_details(self, job: dict) -> dict:
        sleep(0.5)
        jobposition = job["title"]
        category = job["department"]
        country = job["location"]
        location = job["location"]

        country_finder = find_countries(location)
        jobcountry = ""
        if country_finder:
            country = country_finder[0][0].name
            if location.endswith(country):
                jobcountry = country



        job_description = HTMLParser(job["description"]).text()
        position_link = job["apply_job_url"]
        jobqualifications =  job["education_level"]
        jobexperience = job["experience_level"]
        jobpattern = job["contract_type"]
        job_dict = {
            "jobid": int(time()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": job_description,
            "jobniche": category,
            "jobcountry": jobcountry,
            "jobaddress": location,
            "jobqualifications": jobqualifications,
            "jobexperience": jobexperience,
            "jobpattern": jobpattern,
            "scrapedsource": position_link,
            "parse_location": True
        }
        return job_dict
