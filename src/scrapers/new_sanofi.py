from time import sleep, time
from urllib.parse import urljoin

import requests
from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Sanofi(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Sanofi",
            link="https://jobs.sanofi.com/en/search-jobs/results?CurrentPage=3&RecordsPerPage=100&TotalContentResults=&Distance=50&RadiusUnitType=0&Keywords=&Location=&ShowRadius=False&IsPagination=False&CustomFacetName=&FacetTerm=&FacetType=0&SearchResultsModuleName=Search+Results&SearchFiltersModuleName=Search+Filters&SortCriteria=0&SortDirection=0&SearchType=5&PostalCode=&ResultsType=0",
            domain="https://jobs.sanofi.com/",
            companyid=899,
        )

    def get_positions(self) -> list[str]:
        page = 1
        position_links = []

        while True:
            response = requests.get(self.link.replace("?CurrentPage=3", f"?CurrentPage={page}"))
            json_data = response.json()
            soup = HTMLParser(json_data.get('results'))

            positions = soup.css('li')
            print(f"ALL JOBS - {len(positions)}")

            if not positions:
                break

            for position in positions:
                position_link = position.css_first("a")
                if not position_link:
                    continue
                position_link = position_link.attributes.get("href")
                position_link = (
                    urljoin(self.domain, position_link)
                    if self.domain
                    else position_link
                )
                position_links.append(position_link)
            page += 1

        return position_links

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        sleep(2)

        soup = HTMLParser(html)
        jobposition = soup.css_first('h1')
        jobposition = jobposition.text(strip=True) if jobposition else ""
        country = soup.css_first('span[class="job-location job-info"]')
        country = country.text(strip=True) if country else ""
        location = country
        jobtype = soup.css_first('span[class="job-type job-info"]')
        jobtype = jobtype.text(strip=True) if jobtype else ""
        jobsalary = soup.css_first('span[class="job-salary job-info"]')
        jobsalary = jobsalary.text(strip=True) if jobsalary else ""
        job_description = soup.css_first('div[class="ats-description"]')
        job_description = job_description.text(strip=True) if job_description else ""

        job_dict = {
            "jobid": int(time()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": job_description,
            "jobcountry": country,
            "jobaddress": location,
            "jobsalary": jobsalary,
            "jobpattern": jobtype,
            "scrapedsource": position_link,
            "parse_location": True
        }
        return job_dict
