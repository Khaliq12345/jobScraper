from time import sleep, time
from urllib.parse import urljoin

import requests
from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Dangote(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Dangote",
            link="https://careers.dangote.com/tile-search-results/?q=&sortColumn=referencedate&sortDirection=desc&startrow=200&_=1766067820563",
            domain="https://careers.dangote.com/",
            companyid=54,
        )

    def get_positions(self) -> list[str]:
        position_links = []

        html = self.get_html(f"{self.link}")
        soup = HTMLParser(html)

        positions = soup.css('li')
        print(f"ALL JOBS - {len(positions)}")

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

        return position_links

    def get_position_details(self, position_link: str) -> dict:
        response = requests.get(position_link)
        sleep(2)

        soup = HTMLParser(response.text)
        jobposition = response.url.split('/job/')[-1].split('/')[0].replace('-', " ").title()
        category = soup.css_first('span[class="sc-crgk9f-7 fMHCZe"]')
        category = category.text(strip=True) if category else "" 
        location = soup.css_first('p[id="job-location"]')
        location = location.text(strip=True).replace("Location:", "") if location else ""
        country = location
        job_description = soup.css_first('span[class="jobdescription"]')
        job_description = job_description.text(strip=True) if job_description else ""

        job_dict = {
            "jobid": int(time()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": job_description,
            "jobniche": category,
            "jobcountry": country,
            "jobaddress": location,
            "scrapedsource": position_link,
            "parse_location": True
        }
        return job_dict
