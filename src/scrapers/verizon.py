from src.scrapers.base.base_scraper import BaseScraper
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from datetime import datetime
import re
import cloudscraper


class Verizon(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Verizon",
            link="https://mycareer.verizon.com/jobs/",
            domain="https://mycareer.verizon.com",
            companyid=17
        )
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=10
        )

    def get_html(self, url: str) -> str:
        """Extract the html from a url using cloudscraper"""
        headers = {
            "Referer": "https://mycareer.verizon.com/jobs/",
            "Sec-Fetch-Site": "same-origin",
        }
        response = self.scraper.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def get_positions(self, limit: int = None) -> list[str]:
        position_links = []
        page = 1
        
        while True:
            url = f"{self.link}" if page == 1 else f"{self.link}?page={page}#results"
            print(f"Page ==> {page}")
            try:
                html = self.get_html(url)
            except Exception as e:
                print(f"Error getting page {page}: {e} -> Stopping pagination.")
                break
            soup = HTMLParser(html)

            job_cards = soup.css("div.card.card-job")
            if not job_cards:
                print("NO MORE NEW PAGE")
                break

            for card in job_cards:
                job_link = card.css_first("a.stretched-link.js-view-job")
                if not job_link:
                    continue
                
                href = job_link.attributes.get("href", "")
                if href:
                    position_link = urljoin(self.domain, href) if self.domain else href
                    if position_link not in position_links:
                        position_links.append(position_link)

            if limit and page >= limit:
                print(f"Reached limit of {limit} pages")
                break
            page += 1

        return position_links

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        # Job ID
        job_id_elem = soup.css_first('p.job-meta')
        job_id_text = job_id_elem.text(strip=True) if job_id_elem else ""
        match = re.search(r'Job ID:\s*(R-?\d+)', job_id_text)
        job_id = match.group(1).replace("R-", "") if match else ""

        # Position
        h1_title = soup.css_first("h1")
        jobposition = h1_title.text(strip=True) if h1_title else ""

        # Address & Country
        location_elem = soup.css_first(".locations")
        jobaddress = location_elem.text(strip=True) if location_elem else ""
        jobcountry = jobaddress.split(",")[-1].strip() if jobaddress and "," in jobaddress else ""

        # Description (using .cms-content as requested)
        article = soup.css_first("article.cms-content")
        jobdescription = article.text(strip=True, separator="\n") if article else ""
        
        # Clean up description
        if jobdescription:
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()
            # Remove constant footer text
            jobdescription = re.sub(r'When you join Verizon.*?Join the #VTeamLife\.\s*', '', jobdescription, flags=re.DOTALL | re.IGNORECASE)
            jobdescription = re.sub(r'When you join Verizon.*?Want in\? Join the #VTeamLife\.\s*', '', jobdescription, flags=re.DOTALL | re.IGNORECASE)
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        # Niche
        culture_embed = soup.css_first("div.culture-hq-embed")
        jobniche = culture_embed.attributes.get("data-careerarea", "") if culture_embed else ""

        # Pattern
        jobpattern = ""
        if "full-time" in jobdescription.lower() or "full time" in jobdescription.lower():
            jobpattern = "Full time"
        elif "part-time" in jobdescription.lower() or "part time" in jobdescription.lower():
            jobpattern = "Part time"

        job_dict = {
            "jobid": int(job_id) if job_id and job_id.isdigit() else int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobniche": jobniche,
            "jobpattern": jobpattern,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link
        }
        return job_dict


# if __name__ == "__main__":
#     import json
#     verizon = Verizon()
#     positions = verizon.get_positions()
#     print(f"Found {len(positions)} positions")
    
#     all_details = []
#     for position in positions: 
#         print(f"Scraping {position}")
#         try:
#             details = verizon.get_position_details(position)
#             all_details.append(details)
#             print(f"Scraped job {details.get('jobid')}")
#         except Exception as e:
#             print(f"Error scraping {position}: {e}")

#     with open("verizon_results.json", "w", encoding="utf-8") as f:
#         json.dump(all_details, f, indent=4, ensure_ascii=False)
    
#     print(f"Saved {len(all_details)} jobs to verizon_results.json")
        





