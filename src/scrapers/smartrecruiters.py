from time import time_ns
import requests
from selectolax.parser import HTMLParser
from src.scrapers.base.base_scraper import BaseScraper
from urllib.parse import urlparse


class Smartrecruiters(BaseScraper):
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
            name=f"Smartrecruiters-{splits[-1]}",
            link=f"https://careers.smartrecruiters.com/{splits[-1]}",
            domain="",
            base_link=user_link,
            companyid=companyid,
            save=save,
            is_test=is_test,
            process_id=process_id,
        )

    def get_positions(self) -> list[str]:
        all_jobs = []
        page = 0
        while True:
            print(f"PAGE - {page}")
            link = f"{self.link}/api/more?page={page}"
            print(f"LINK = {link}")
            response = requests.get(link, timeout=60)
            soup = HTMLParser(response.text)
            jobs = soup.css('li[class="opening-job job column wide-1of2 medium-1of2"]')
            if len(jobs) == 0:
                break

            for job in jobs:
                job_node = job.css_first("li a")
                if job_node:
                    all_jobs.append(job_node.attributes.get("href"))

            print(f"FETCHED JOBS - {len(all_jobs)}")

            if self.is_test:
                break

            page += 1

        return all_jobs

    def get_position_details(self, job_link: str) -> dict | None:
        response = requests.get(job_link)
        soup = HTMLParser(response.text)
        jobposition = soup.css_first('h1[class="job-title"]')
        jobposition = jobposition.text() if jobposition else None
        jobpattern = soup.css_first('li[itemprop="employmentType"]')
        jobpattern = jobpattern.text() if jobpattern else None
        jobdescription = soup.css_first('section[id="st-jobDescription"]')
        jobdescription = jobdescription.text() if jobdescription else None
        jobqualification = soup.css_first('section[id="st-qualifications"]')
        jobqualification = jobqualification.text() if jobqualification else None
        jobdate = soup.css_first('meta[itemprop="datePosted"]')
        jobdate = jobdate.attributes.get("content") if jobdate else None
        joblocation = soup.css_first('span[class="c-spl-job-location__place"]')
        joblocation = joblocation.text() if joblocation else None
        jobniche = soup.css_first('meta[itemprop="industry"]')
        jobniche = jobniche.attributes.get("content") if jobniche else None
        jobcountry = soup.css_first('meta[itemprop="addressCountry"]')
        jobcountry = jobcountry.attributes.get("content") if jobcountry else None
        locality = soup.css_first('meta[itemprop="addressLocality"]')
        region = soup.css_first('meta[itemprop="addressRegion"]')
        street = soup.css_first('meta[itemprop="streetAddress"]')

        locality = locality.attributes.get("content") if locality else None
        region = region.attributes.get("content") if region else None
        street = street.attributes.get("content") if street else None

        jobaddress = ", ".join(filter(None, [street, locality, region]))
        job_dict = {
            "jobid": time_ns(),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "jobpattern": jobpattern,
            "scrapedsource": job_link,
            "jobnice": jobniche,
            "parse_location": True,
            "jobdate": jobdate,
        }
        print(job_dict)
        return job_dict
