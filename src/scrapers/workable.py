from time import time_ns
import requests
from selectolax.parser import HTMLParser
from src.scrapers.base.base_scraper import BaseScraper
from urllib.parse import urlparse


class Workable(BaseScraper):
    def __init__(
        self,
        save: bool,
        name: str,
        user_link: str,
        companyid: int,
        process_id: int = 0,
        is_test: bool = False,
    ) -> None:
        parsed_url = urlparse(user_link)
        splits = parsed_url.path.split("/")
        super().__init__(
            name=f"Workable-{splits[-1]}",
            link=f"https://jobs.workable.com/api/v1/companies/{splits[-2]}",
            domain="",
            companyid=companyid,
            save=save,
            is_test=is_test,
            process_id=process_id,
        )

    def get_positions(self) -> list[str]:
        all_jobs = []
        page_token = ""
        page = 0
        while True:
            print(f"PAGE - {page} - PageToken - {page_token}")
            link = f"{self.link}?pageToken={page_token}" if page_token else self.link
            print(f"LINK = {link}")
            response = requests.get(link, timeout=60)
            json_data = response.json()
            jobs = json_data["jobs"]

            if len(jobs) == 0:
                break

            all_jobs.extend(jobs)

            print(f"FETCHED JOBS - {len(all_jobs)}")

            # Check if we've collected all jobs
            if not json_data.get("nextPageToken"):
                break

            if self.is_test:
                break

            page_token = json_data.get("nextPageToken")
            page += 1

        return all_jobs

    def get_position_details(self, job: dict) -> dict | None:
        jobposition = job["title"]
        jobdescription = HTMLParser(job["description"]).text(separator=" ")
        jobqualification = HTMLParser(job["requirementsSection"]).text(separator=" ")
        jobdescription = f"{jobdescription} {jobqualification}"
        jobpattern = job["employmentType"]
        joblink = job["url"]
        jobdate = job["created"]
        jobcountry = job["location"]["countryName"]
        jobaddress = job["location"]["city"]
        jobnice = job["department"]
        job_dict = {
            "jobid": time_ns(),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "jobpattern": jobpattern,
            "scrapedsource": joblink,
            "jobnice": jobnice,
            "parse_location": True,
            "jobdate": jobdate,
        }
        return job_dict
