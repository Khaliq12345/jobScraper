from datetime import datetime
from urllib.parse import urljoin
import httpx
from selectolax.parser import HTMLParser
from src.storage.database import Database
from src.storage.model import jobs


class BaseScraper(Database):
    def __init__(self, name: str, link: str, positions_selector: str, domain: str = "") -> None:
        super().__init__()
        self.name = name
        self.link = link
        self.positions_selector = positions_selector
        self.domain = domain
        self.create_db_and_tables()


    @staticmethod
    def get_html(url: str) -> str:
        """Extract the html from a url"""
        response = httpx.get(url)
        print(response)
        response.raise_for_status()
        return response.text


    @staticmethod
    def validate_data(job_details: dict):
        """Validate Scraped job info"""
        scraped_job = jobs(**job_details)
        print(scraped_job)
        return scraped_job
    

    def get_positions(self) -> list[str]:
        """Extract the position links"""
        position_links = []

        html = self.get_html(self.link)
        soup = HTMLParser(html)

        positions = soup.css(self.positions_selector)
        print(f"ALL JOBS - {len(positions)}")

        for position in positions:
            position_link = position.css_first("a")
            if not position_link:
                continue
            position_link = position_link.attributes.get("href")
            position_link = urljoin(self.domain, position_link) if self.domain else position_link
            position_links.append(position_link)
        return position_links

    def get_position_details(self, position_link: str) -> dict:
        """Extract position details"""
        print(f"POSITION - {position_link}")
        html = self.get_html(position_link)

        soup = HTMLParser(html)
        jobposition = soup.css_first('span[class="header__text"]')
        jobposition = jobposition.text(strip=True) if jobposition else ""
        category = soup.css_first('li[class="Team-wrapper"]')
        category = category.text(strip=True).replace("__vacancyopjusttionswidget.opt-Team__", "") if category else ""
        country = soup.css_first('li[class="Locations-wrapper"]')
        country = country.text(strip=True).replace('__vacancyopjusttionswidget.opt-Locations__', "") if country else ""
        job_info = soup.css_first('div[aria-label="Job description"]')
        job_info = job_info.text(strip=True, separator=" ") if job_info else ""
        job_description = job_info.split("Job Description")[1]
        job_salary = soup.css_first('div[data-type="SalaryWidget"]')
        job_salary = job_salary.text(strip=True) if job_salary else ""

        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": job_description,
            "jobsalary": job_salary,
            "jobniche": category,
            "jobcountry": country,
            "scrapedsource": position_link
        }
        return job_dict



    def main(self) -> None:
        print(self.name)
        positions = self.get_positions()
        print(positions)
        parsed_positions = []
        for position in positions:
            job_details = self.get_position_details(position)
            parsed_position = self.validate_data(job_details)
            parsed_positions.append(parsed_position)

        self.send_jobs(parsed_positions) 
