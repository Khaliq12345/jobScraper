from datetime import datetime
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class CapitecBank(BaseScraper):
    def __init__(self, save: bool) -> None:
        super().__init__(
            name="Capitec Bank",
            link="https://careers.capitecbank.co.za/search/",
            domain="https://careers.capitecbank.co.za",
            companyid=35,
            save=save
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []

        html = self.get_html(self.link)
        soup = HTMLParser(html)

        anchors = soup.css(
            "table#searchresults tbody tr.data-row td.colTitle span.jobTitle a.jobTitle-link"
        )

        for a in anchors:
            href = a.attributes.get("href")
            if not href:
                continue
            position_link = urljoin(self.domain, href)
            position_links.append(position_link)

        return position_links

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        title_el = soup.css_first("h1#job-title")
        jobposition = title_el.text(strip=True) if title_el else ""

        location_el = soup.css_first("p#job-location span.jobGeoLocation")
        jobaddress = location_el.text(strip=True) if location_el else ""
        jobcountry = jobaddress.split(',')[-1].strip() if jobaddress else ""
        jobaddress = jobaddress.replace(jobcountry, "").strip()

        desc_el = soup.css_first("span.jobdescription")
        jobdescription = desc_el.text(strip=True, separator=" ") if desc_el else ""

        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link,
        }

        return job_dict
