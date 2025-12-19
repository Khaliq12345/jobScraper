from time import time
from urllib.parse import urljoin
import json
import re

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Chevron(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Chevron",
            link="https://careers.chevron.com/search-jobs",
            domain="https://careers.chevron.com",
            companyid=999,
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []
        page = 1
        page_size = 15

        while True:
            if page == 1:
                url = self.link
            else:
                url = f"{self.link}?p={page}"

            print(f"Page ==> {page}")

            html = self.get_html(url)
            soup = HTMLParser(html)

            # Extraire les liens depuis #search-results-list > ul > li > a
            job_links = soup.css('#search-results-list ul li a')
            
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

        # Titre depuis h2.ajd_header__job-title
        jobposition = soup.css_first('h2.ajd_header__job-title')
        jobposition = jobposition.text(strip=True) if jobposition else ""

        # Description depuis .ajd_job-details ou .job-description
        jobdescription = ""
        desc_div = soup.css_first('section.ajd_job-details.job-description')
        if desc_div:
            jobdescription = desc_div.text(strip=True, separator="\n")
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        # Localisation depuis .job-location ou depuis le JSON-LD
        jobcountry = ""
        jobaddress = ""

        # Essayer d'abord depuis le JSON-LD
        json_ld_script = soup.css_first('script[type="application/ld+json"]')
        if json_ld_script:
            try:
                json_data = json.loads(json_ld_script.text())
                if not jobposition and json_data.get("title"):
                    jobposition = json_data.get("title", "")
                
                if not jobdescription and json_data.get("description"):
                    desc_html = json_data.get("description", "")
                    if isinstance(desc_html, str):
                        desc_soup = HTMLParser(desc_html)
                        jobdescription = desc_soup.text(strip=True, separator="\n")
                        jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()
                
                # Localisation depuis jobLocation
                if json_data.get("jobLocation"):
                    locations = json_data.get("jobLocation", [])
                    if isinstance(locations, list) and locations:
                        location = locations[0]
                    else:
                        location = locations
                    
                    if isinstance(location, dict) and "address" in location:
                        address = location["address"]
                        if isinstance(address, dict):
                            if address.get("addressCountry"):
                                jobcountry = address.get("addressCountry", "")
                            parts = []
                            if address.get("addressLocality"):
                                parts.append(address.get("addressLocality"))
                            if address.get("addressRegion"):
                                parts.append(address.get("addressRegion"))
                            if parts:
                                jobaddress = ", ".join(parts)
            except json.JSONDecodeError:
                pass

        # Si pas de localisation depuis JSON-LD, chercher dans le HTML
        if not jobaddress:
            location_span = soup.css_first('span.job-location')
            if location_span:
                location_text = location_span.text(strip=True)
                if location_text:
                    # Format: "Makati City, Philippines" ou "Pecos, Texas"
                    parts = location_text.split(",")
                    if len(parts) >= 2:
                        jobaddress = location_text
                        jobcountry = parts[-1].strip()
                    else:
                        jobaddress = location_text


        # Pattern depuis JSON-LD
        jobpattern = ""
        if json_ld_script:
            try:
                json_data = json.loads(json_ld_script.text())
                emp_type = json_data.get("employmentType", "")
                if emp_type:
                    jobpattern = emp_type.replace("_", " ").title()
            except json.JSONDecodeError:
                pass

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
    scraper = Chevron()
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

    with open("chevron_jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=4, ensure_ascii=False)

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'chevron_jobs.json'.")

"""