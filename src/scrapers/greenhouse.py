from country_named_entity_recognition import find_countries
from time import sleep, time_ns
import requests
from selectolax.parser import HTMLParser
from config.config import PROXY_TOKEN
from src.scrapers.base.base_scraper import BaseScraper
from urllib.parse import urlparse
import pycountry
from src.utils.static import CAPITALS, US_STATES

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0",
    "Accept": "application/json",
    "Accept-Language": "en-US",
    "Content-Type": "application/json",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=4",
}


class GreenHouse(BaseScraper):
    def __init__(
        self,
        save: bool,
        name: str,
        user_link: str,
        companyid: int,
        process_id: int = 0,
        is_test: bool = False,
    ) -> None:
        name = urlparse(user_link).path.replace("/", "")
        super().__init__(
            name=f"Greenhouse-{name}",
            link=user_link,
            domain="",
            companyid=companyid,
            save=save,
            is_test=is_test,
            process_id=process_id,
        )

    def find_country_by_location(self, location_name: str):
        """
        Find country by capital city or US state name.

        Args:
            location_name: Name of capital city or US state

        Returns:
            Country name or None if not found
        """
        location_lower = location_name.lower().strip()

        # First check if it's a US state
        if location_lower in US_STATES:
            country_code = US_STATES[location_lower]
            country = pycountry.countries.get(alpha_2=country_code)
            return country.name if country else "United States"

        # Then check if it's a capital
        if location_lower in CAPITALS:
            country_code = CAPITALS[location_lower]
            country = pycountry.countries.get(alpha_2=country_code)
            return country.name if country else None

        return None

    def get_positions(self) -> list[dict]:
        print(f"LINK = {self.link} - Name - {self.name}")
        all_jobs = []
        page = 1

        while True:
            print(f"Page - {page}")
            params = {"_data": "routes/$url_token", "page": f"{page}"}
            proxyModeUrl = f"http://{PROXY_TOKEN}:@proxy.scrape.do:8080"
            proxies = {
                "http": proxyModeUrl,
                "https": proxyModeUrl,
            }
            response = requests.get(
                f"{self.link}?page={page}&_data=routes%2F%24url_token",
                proxies=proxies,
                verify=False,
            )
            response.raise_for_status()
            json_data = response.json()
            job_post = json_data["jobPosts"]
            jobs = job_post["data"]

            if len(jobs) == 0:
                break

            for job in jobs:
                department = job.get("department", {})
                job_info = {
                    "title": job["title"],
                    "location": job["location"],
                    "department": department.get("name") if department else None,
                    "url": job["absolute_url"],
                    "jobdate": job["published_at"],
                }
                all_jobs.append(job_info)

            if self.is_test:
                break

            page += 1

        return all_jobs

    def get_position_details(self, job_info: dict) -> dict | None:
        sleep(5)
        url = job_info["url"]
        proxyModeUrl = f"http://{PROXY_TOKEN}:@proxy.scrape.do:8080"
        proxies = {
            "http": proxyModeUrl,
            "https": proxyModeUrl,
        }
        response = requests.get(url, headers=headers, proxies=proxies, verify=False)
        soup = HTMLParser(response.text)
        jobsalary = None
        salary_node = soup.css('div[class="pay-range"] p.body')
        if salary_node:
            jobsalary = salary_node[-1].text()

        jobposition = job_info["title"]
        joblink = url
        jobdescription = ""
        jobdescription_node = soup.css_first('div[class="job__description body"]')
        if jobdescription_node:
            jobdescription = jobdescription_node.text()
        jobpattern = ""
        if (
            "full-time" in jobdescription.lower()
            or "full time" in jobdescription.lower()
        ):
            jobpattern = "Full time"
        elif (
            "part-time" in jobdescription.lower()
            or "part time" in jobdescription.lower()
        ):
            jobpattern = "Part time"

        try:
            location = job_info["location"]
            print(f"LOCATION - {location}")
            country = find_countries(location)[0][0].name
            jobaddress = location.replace(country, "").strip()
        except Exception as _:
            country = None
            country = self.find_country_by_location(location.split(",")[-1].strip())
            jobaddress = location
        print(f"COUNTRY - {country}")
        jobniche = job_info["department"]
        job_dict = {
            "jobid": time_ns(),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobcountry": country,
            "jobdate": job_info["jobdate"],
            "jobaddress": jobaddress,
            "jobpattern": jobpattern,
            "jobniche": jobniche,
            "jobsalary": jobsalary,
            "scrapedsource": joblink,
        }
        return job_dict
