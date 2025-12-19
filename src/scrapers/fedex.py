from time import time
from urllib.parse import urljoin
import json
import re

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class FedEx(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="FedEx",
            link="https://careers.fedex.com/fr/jobs",
            domain="https://careers.fedex.com",
            companyid=29,
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []
        page = 1
        page_size = 10

        while True:
            if page == 1:
                url = self.link
            else:
                url = f"{self.link}/page/{page}"

            print(f"Page ==> {page}")

            html = self.get_html(url)
            soup = HTMLParser(html)

            # Extraire les liens depuis a.results-list__item-title--link
            job_links = soup.css('a.results-list__item-title--link')
            
            print(f"ALL JOBS - {len(job_links)}")

            if len(job_links) == 0:
                print("NO MORE NEW PAGE")
                break

            for link in job_links:
                href = link.attributes.get("href", "")
                if href:
                    if not href.startswith("http"):
                        href = urljoin(self.domain, href)
                    if href not in position_links:
                        position_links.append(href)

            if len(job_links) < page_size:
                break

            page += 1

        return list(dict.fromkeys(position_links))

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        # Titre depuis h1.c-main-hero__title
        jobposition = soup.css_first('h1.c-main-hero__title')
        jobposition = jobposition.text(strip=True) if jobposition else ""

        # Description depuis div.c-job-details-content__description
        jobdescription = ""
        desc_div = soup.css_first('div.c-job-details-content__description')
        if desc_div:
            jobdescription = desc_div.text(strip=True, separator="\n")
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        # Localisation et pattern depuis job-details-brief__description-list
        jobcountry = ""
        jobaddress = ""
        jobpattern = ""

        list_items = soup.css('li.job-details-brief__description-list--item')
        for item in list_items:
            label_span = item.css_first('span.label')
            value_span = item.css_first('span.value')
            
            if label_span and value_span:
                label_text = label_span.text(strip=True)
                value_text = value_span.text(strip=True)
                
                if "Location:" in label_text:
                    # Format: "21300 Van Owen, Canoga Park, CA 91303, United States"
                    location_parts = value_text.split(",")
                    if len(location_parts) >= 2:
                        jobaddress = ", ".join(location_parts[:-1]).strip()
                        jobcountry = location_parts[-1].strip()
                    else:
                        jobaddress = value_text
                
                elif "Employment Type:" in label_text:
                    # Convertir "Full Time" -> "Full-Time", "À temps plein" -> "Full-Time"
                    emp_type = value_text.strip()
                    if "temps plein" in emp_type.lower() or "full" in emp_type.lower():
                        jobpattern = "Full-Time"
                    elif "temps partiel" in emp_type.lower() or "part" in emp_type.lower():
                        jobpattern = "Part-Time"
                    else:
                        jobpattern = emp_type

        job_dict = {
            "jobid": int(time()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobniche": "",
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "jobpattern": jobpattern,
            "scrapedsource": position_link,
            "parse_location": True
        }
        return job_dict

"""
if __name__ == "__main__":
    scraper = FedEx()
    positions = scraper.get_positions()
    print(f"\nNombre de positions trouvées: {len(positions)}")

    all_jobs: list[dict] = []
    if positions:
        for i, position_link in enumerate(positions, 1):
            print(f"\nScraping [{i}/{len(positions)}]: {position_link}")
            try:
                job_dict = scraper.get_position_details(position_link)
                print(json.dumps(job_dict, indent=2, ensure_ascii=False))
                all_jobs.append(job_dict)
            except Exception as e:
                print(f"Erreur lors du scraping de {position_link}: {e}")

    with open("fedex_jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=4, ensure_ascii=False)

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'fedex_jobs.json'.")

"""