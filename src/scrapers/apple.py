from datetime import datetime
from urllib.parse import urljoin
from selectolax.parser import HTMLParser
from src.scrapers.base.base_scraper import BaseScraper

class Apple(BaseScraper):
    def __init__(self) -> None:
        super().__init__(name = "Apple", link="https://jobs.apple.com/en-us/search", companyid=99, domain="https://jobs.apple.com")


    def get_positions(self) -> list[str]:
        position_links = []

        page = 1
        while True:
            print(f"Page ==> {page}")
            html = self.get_html(f"{self.link}?page={page}")
            soup = HTMLParser(html)

            positions = soup.css('ul[id="search-job-list"] li[role="listitem"]')
            print(f"ALL JOBS - {len(positions)}")
            if len(positions) == 0:
                print("NO MORE NEW PAGE")
                break

            for position in positions:
                position_link = position.css_first("a")
                if not position_link:
                    continue
                position_link = position_link.attributes.get("href")
                position_link = urljoin(self.domain, position_link) if self.domain else position_link
                position_links.append(position_link) if position_link not in position_links else None
            
            page += 1
            if page == 3:
                break
        print(f"ALL JOBS NO DUPLICATES - {len(position_links)}")
        return position_links


    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)

        soup = HTMLParser(html)
        print(soup.text())
        jobposition = soup.css_first('h1[id="jobdetails-postingtitle"]')
        jobposition = jobposition.text(strip=True) if jobposition else ""
        category = soup.css_first('label[id="jobdetails-teamname"]')
        category = category.text(strip=True) if category else ""
        country = soup.css_first('label[id="jobdetails-joblocation"]')
        country = country.text(strip=True) if country else ""
        job_description = soup.css_first('div[id="jobdetails-jobdetails-jobdescription-content-row"]')
        job_description = job_description.text(strip=True, separator=" ") if job_description else ""
        jobqualifications_1 = soup.css_first('div[id="jobdetails-minimumqualifications"]')
        jobqualifications_1 = jobqualifications_1.text(strip=True, separator=" ") if jobqualifications_1 else ""
        jobqualifications_2 = soup.css_first('div[id="jobdetails-preferredqualifications"]')
        jobqualifications_2 = jobqualifications_2.text(strip=True, separator=" ") if jobqualifications_2 else ""
        jobqualifications = f"{jobqualifications_1} {jobqualifications_2}"

        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": job_description,
            "jobniche": category,
            "jobcountry": country,
            "scrapedsource": position_link,
            "jobqualifications": jobqualifications
        }
        return job_dict
