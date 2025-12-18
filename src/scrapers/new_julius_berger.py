from time import sleep, time
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class JB(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Julius Berger",
            link="https://juliusbergerinternationalgmbh.recruitee.com/",
            domain="https://juliusbergerinternationalgmbh.recruitee.com",
            companyid=199,
        )

    def get_positions(self) -> list[str]:
        position_links = []

        html = self.get_html(f"{self.link}")
        soup = HTMLParser(html)

        positions = soup.css('div[class="sc-uzptka-1 igNTCz"]')
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
        html = self.get_html(position_link)
        sleep(2)

        soup = HTMLParser(html)
        jobposition = soup.css_first('h1[class="sc-crgk9f-2 dYxSYU"]')
        jobposition = jobposition.text(strip=True) if jobposition else ""
        category = soup.css_first('span[class="sc-crgk9f-7 fMHCZe"]')
        category = category.text(strip=True) if category else "" 
        country = soup.css_first('span[class="sc-qfruxy-1 kiOgGf custom-css-style-job-location-country"]')
        country = country.text(strip=True) if country else ""
        location = soup.css_first('span[class="sc-qfruxy-1 kiOgGf custom-css-style-job-location-city"]')
        location = location.text(strip=True) if location else ""
        job_description = soup.css_first('div[class="sc-1fwbcuw-0 koMcQZ"]')
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
            "parse_location": False
        }
        return job_dict
