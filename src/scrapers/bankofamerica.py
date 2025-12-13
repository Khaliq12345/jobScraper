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
        
        # Niche / Department
        jobniche = ""
        niche_elem = soup.css_first('p.item')
        jobniche = niche_elem.text(strip=True) if niche_elem else ""

        # Description (All in description, no qualifications splitting)
        jobdescription = ""
        content_div = soup.css_first('div.job-description-body__internal')
        if content_div:
            jobdescription = content_div.text(strip=True, separator='\n')
            # Clean up
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()
            jobdescription = jobdescription.replace("Job Description:\nJob Description:", "Job Description:")

        job_dict = {
            "jobid": int(jobid) if jobid and jobid.isdigit() else int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobniche": jobniche,
            "jobpattern": jobpattern,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link
        }
        return job_dict


if __name__ == "__main__":
    import json
    
    scraper = BankOfAmerica()
    positions = scraper.get_positions()
    print(f"Found {len(positions)} positions")
    
    all_details = []
    for position in positions:
        print(f"Scraping {position}")
        try:
            details = scraper.get_position_details(position)
            all_details.append(details)
            print(f"Scraped job {details.get('jobid')}")
        except Exception as e:
            print(f"Error scraping {position}: {e}")

    with open("bankofamerica_results.json", "w", encoding="utf-8") as f:
        json.dump(all_details, f, indent=4, ensure_ascii=False)
    
    print(f"Saved {len(all_details)} jobs to bankofamerica_results.json")
