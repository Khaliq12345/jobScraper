from time import time_ns
import requests
from selectolax.parser import HTMLParser
from src.scrapers.base.base_scraper import BaseScraper
from urllib.parse import urlparse
import json
from country_named_entity_recognition import find_countries


class Lever(BaseScraper):
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
            name=f"Lever-{splits[-1]}",
            link=f"https://jobs.lever.co/{splits[-1]}",
            domain="",
            base_link=user_link,
            companyid=companyid,
            save=save,
            is_test=is_test,
            process_id=process_id,
        )

    def get_positions(self) -> list[str]:
        all_jobs = []
        # page = 0
        # while True:
        # print(f"PAGE - {page}")
        # link = f"{self.link}/api/more?page={page}"
        print(f"LINK = {self.link}")
        response = requests.get(self.link, timeout=60)
        soup = HTMLParser(response.text)
        jobs = soup.css('a[class="posting-title"]')
        for job in jobs:
            all_jobs.append(job.attributes.get("href"))

        print(f"FETCHED JOBS - {len(all_jobs)}")

        # if self.is_test:
        #     break
        #
        # page += 1

        return all_jobs

    def get_position_details(self, job_link: str) -> dict | None:
        response = requests.get(job_link)
        soup = HTMLParser(response.text)

        json_script = soup.css_first('script[type="application/ld+json"]')
        if not json_script:
            return None

        try:
            data = json.loads(json_script.text())
        except Exception:
            return None

        jobposition = data.get("title")
        jobpattern = data.get("employmentType")
        jobdate = data.get("datePosted")
        jobdescription = data.get("description")

        hiring_org = data.get("hiringOrganization", {})
        jobniche = hiring_org.get("name")

        address = data.get("jobLocation", {}).get("address", {})
        locality = address.get("addressLocality")
        region = address.get("addressRegion")
        country = address.get("addressCountry")
        postal = address.get("postalCode")
        country_finder = find_countries(locality)
        if not country_finder:
            country = country if country else "United States"
        else:
            country = country_finder[0][0].name
            if country in locality:
                country = country

        jobaddress = ", ".join(filter(None, [locality, region, postal]))

        job_dict = {
            "jobid": time_ns(),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobcountry": country,
            "jobaddress": jobaddress,
            "jobpattern": jobpattern,
            "scrapedsource": job_link,
            "jobnice": jobniche,
            "parse_location": True,
            "jobdate": jobdate,
        }
        return job_dict
