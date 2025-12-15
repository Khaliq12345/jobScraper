from time import sleep, time
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Wise(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Wise",
            link="https://wise.jobs/jobs",
            domain="https://wise.jobs",
            companyid=18,
        )

    def get_positions(self) -> list[str]:
        position_links = []

        page = 1
        while True:
            print(f"Page ==> {page}")
            html = self.get_html(f"{self.link}?page={page}&size=48")
            soup = HTMLParser(html)

            positions = soup.css("div.attrax-vacancy-tile")
            print(f"ALL JOBS - {len(positions)}")
            if len(positions) == 0:
                print("NO MORE NEW PAGE")
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
        jobposition = soup.css_first('span[class="header__text"]')
        jobposition = jobposition.text(strip=True) if jobposition else ""
        category = soup.css_first('li[class="Team-wrapper"]')
        category = (
            category.text(strip=True).replace(
                "__vacancyopjusttionswidget.opt-Team__", ""
            )
            if category
            else ""
        )
        country = soup.css_first('li[class="Locations-wrapper"]')
        country = (
            country.text(strip=True).replace(
                "__vacancyopjusttionswidget.opt-Locations__", ""
            )
            if country
            else ""
        )
        job_info = soup.css_first('div[aria-label="Job description"]')
        job_info = job_info.text(strip=True, separator=" ") if job_info else ""
        job_description = job_info.split("Job Description")[1]
        job_salary = soup.css_first('div[data-type="SalaryWidget"]')
        job_salary = job_salary.text(strip=True) if job_salary else ""

        job_dict = {
            "jobid": int(time()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": job_description,
            "jobsalary": job_salary,
            "jobniche": category,
            "jobcountry": country,
            "scrapedsource": position_link,
        }
        return job_dict
