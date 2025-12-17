from src.scrapers.base.base_scraper import BaseScraper
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from datetime import datetime
import re


class BankOfAmerica(BaseScraper):
    def __init__(self) -> None:
        super().__init__(name="Bank of America", link="https://careers.bankofamerica.com/en-us/job-search", domain="https://careers.bankofamerica.com", companyid=16)


    def get_positions(self) -> list[str]:
        position_links = []
        offset = 0
        rows = 2000 #Editer pour tout obtenir 
        
        while True:
            url = f"{self.link}?ref=search&start={offset}&rows={rows}&search=getAllJobs"
            print(f"Fetching {url}")
            try:
                html = self.get_html(url)
            except Exception as e:
                print(f"Error fetching page {offset}: {e} -> Stopping.")
                break
                
            soup = HTMLParser(html)
            tiles = soup.css("a.job-search-tile__url")
            
            if not tiles:
                print("No more jobs found.")
                break

            for tile in tiles:
                href = tile.attributes.get("href")
                if not href:
                    continue
                position_link = urljoin(self.domain, href) if self.domain else href
                if position_link not in position_links:
                    position_links.append(position_link)
            
            offset += rows
            
        return position_links


    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)
        
        # Job ID
        jobid = ""
        jd_body = soup.css_first('div.job-description-body')
        if jd_body:
            jobid = jd_body.attributes.get('data-jobRequisitionID', '')
        
        if not jobid:
             job_info_id = soup.css_first('p.job-information__id span')
             if job_info_id:
                 jobid = job_info_id.text(strip=True).replace('JR-', '').strip()

        if not jobid:
             meta_job_path = soup.css_first('meta[name="job-path"]')
             if meta_job_path:
                content = meta_job_path.attributes.get('content', '')
                match = re.search(r'/job-detail/(\d+)', content)
                if match:
                    jobid = match.group(1)

        # Title
        jobposition_elem = soup.css_first('h1.job-description-body__title')
        jobposition = jobposition_elem.text(strip=True) if jobposition_elem else ""

        # Pattern (Full time/Part time)
        jobpattern = ""
        pattern_elem = soup.css_first('p.job-information__type span')
        
        if pattern_elem:
            jobpattern = pattern_elem.text(strip=True)
        
        if not jobpattern and jd_body:
             jobpattern = jd_body.attributes.get('data-jobTimeType', '')
        
        if not jobpattern:
            sidebar = soup.css_first('div.job-description-sidebar')
            if sidebar:
                sidebar_text = sidebar.text(strip=True).lower()
                if 'full time' in sidebar_text or 'full-time' in sidebar_text:
                    jobpattern = 'Full time'
                elif 'part time' in sidebar_text or 'part-time' in sidebar_text:
                    jobpattern = 'Part time'

        # Location
        jobaddress_elem = soup.css_first('span.js-primary-location')
        jobaddress = jobaddress_elem.text(strip=True) if jobaddress_elem else ""
        
        jobcountry = ""
        if jobaddress:
             parts = jobaddress.split(',')
             if len(parts) > 1:
                 last_part = parts[-1].strip()
                 if len(last_part) == 2 or last_part == "United States": 
                     jobcountry = "USA"
                 else:
                     jobcountry = last_part
        
        # Niche / Department (data-jobfamily sur le bloc principal)
        jobniche = jd_body.attributes.get("data-jobfamily", "") if jd_body else ""

        # Description 
        jobdescription = ""
        content_div = soup.css_first('div.job-description-body__internal')
        if content_div:
            jobdescription = content_div.text(strip=True, separator='\n')
            # Clean up
            jobdescription = re.sub(r"\n\s*\n+", "\n\n", jobdescription).strip()
            jobdescription = jobdescription.replace(
                "Job Description:\nJob Description:", "Job Description:"
            )

        # Mapping des formats d'expérience du type "x-y years" -> on garde "y years"
        jobexperience = ""
        text_lower = (jobdescription or "").lower()
        # Exemple dans la page : "4-8 years of experience in Global Markets"
        range_match = re.search(r"(\d+)\s*-\s*(\d+)\s+years", text_lower)
        if range_match:
            last_year = range_match.group(2)
            jobexperience = f"{last_year} years"

        # Données de base du job_dict
        job_dict = {
            "jobid": int(jobid) if jobid and jobid.isdigit() else int(datetime.now().timestamp()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobexperience": jobexperience,
            "jobniche": jobniche,
            "jobpattern": jobpattern,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link
        }

        # Appliquer la logique de validate_data 
        parsed = self.validate_data(job_dict)
        # On met à jour seulement les variables issues de validate_data
        job_dict["jobqualifications"] = parsed.jobqualifications
        job_dict["jobexperience"] = parsed.jobexperience
        job_dict["jobpattern"] = parsed.jobpattern
        job_dict["jobsalary"] = parsed.jobsalary

        return job_dict

"""
if __name__ == "__main__":
    import json

    scraper = BankOfAmerica()
    positions = scraper.get_positions()
    print(f"Found {len(positions)} positions")

    # Écriture progressive dans le JSON pour voir les résultats au fur et à mesure
    output_path = "bankofamerica_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("[\n")
        first = True

        for position in positions:
            print(f"Scraping {position}")
            try:
                details = scraper.get_position_details(position)

                if not first:
                    f.write(",\n")
                # JSON bien formaté pour chaque offre (indentation)
                f.write(json.dumps(details, ensure_ascii=False, indent=2))
                f.flush()  # On force l'écriture disque à chaque offre
                first = False
                print(f"Scraped job {details.get('jobid')}")
            except Exception as e:
                print(f"Error scraping {position}: {e}")
                continue

        f.write("\n]\n")
        f.flush()

    print(f"Saved results progressively to {output_path}")
"""
