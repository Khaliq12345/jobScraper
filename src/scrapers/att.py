from urllib.parse import urljoin
from datetime import datetime
import json
import re
from selectolax.parser import HTMLParser
from src.scrapers.base.base_scraper import BaseScraper


class ATT(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="AT&T",
            link="https://www.att.jobs/search-jobs",
            domain="https://www.att.jobs",
            companyid=16
        )

    def get_positions(self) -> list[str]:
        position_links = []

        page = 1
        while True:
            url = f"{self.link}" if page == 1 else f"{self.link}?p={page}"
            html = self.get_html(url)
            soup = HTMLParser(html)

            # Le '^' dans [href^="/job/"] signifie "commence par"
            # Cela sélectionne tous les liens <a> dont l'attribut href commence par "/job/"
            job_links = soup.css('a[href^="/job/"]')
            if len(job_links) == 0:
                break

            new_links_count = 0
            for link in job_links:
                href = link.attributes.get("href", "")
                if href and href.startswith("/job/"):
                    position_link = urljoin(self.domain, href)
                    if position_link not in position_links:
                        position_links.append(position_link)
                        new_links_count += 1
            
            print(f"Page {page}: found {len(job_links)} links, {new_links_count} new. Total: {len(position_links)}")

            if new_links_count == 0:
                print("No new links found on this page. Ending pagination.")
                break

            page += 1

        return position_links

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        json_ld_script = soup.css_first('script[type="application/ld+json"]')
        json_data = None
        if json_ld_script:
            try:
                json_data = json.loads(json_ld_script.text())
            except json.JSONDecodeError:
                pass

        jobposition = json_data.get("title", "") if json_data else ""
        
        jobcountry = ""
        jobaddress = ""
        if json_data:
            job_locations = json_data.get("jobLocation", [])
            if job_locations and isinstance(job_locations, list):
                address = job_locations[0].get("address", {})
                parts = []
                if address.get("addressLocality"):
                    parts.append(address.get("addressLocality"))
                if address.get("addressRegion"):
                    parts.append(address.get("addressRegion"))
                if address.get("addressCountry"):
                    parts.append(address.get("addressCountry"))
                    jobcountry = address.get("addressCountry", "")
                if parts:
                    jobaddress = ", ".join(parts)

        jobdescription = ""
        if json_data:
            description_html = json_data.get("description", "")
            if description_html:
                desc_soup = HTMLParser(description_html)
                all_text = desc_soup.text(strip=True, separator="\n")
                jobdescription = re.sub(r'<[^>]+>', '', all_text)
                jobdescription = re.sub(r'^Job Description:\s*', '', jobdescription, flags=re.IGNORECASE)
                jobdescription = re.sub(r'Weekly Hours:.*?$', '', jobdescription, flags=re.MULTILINE | re.IGNORECASE)
                jobdescription = re.sub(r'Time Type:.*?$', '', jobdescription, flags=re.MULTILINE | re.IGNORECASE)
                jobdescription = re.sub(r'Location:.*?$', '', jobdescription, flags=re.MULTILINE | re.IGNORECASE)
                jobdescription = re.sub(r'It is the policy of AT&T.*?$', '', jobdescription, flags=re.DOTALL | re.IGNORECASE)
                jobdescription = re.sub(r'AT&T is a fair chance employer.*?$', '', jobdescription, flags=re.DOTALL | re.IGNORECASE)
                
                lines = jobdescription.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not re.match(r'^\d+$', line) and line not in ['Regular', 'Full Time', 'Part Time']:
                        if not (re.match(r'^[A-Z][a-z]+(?:,\s*[A-Z][a-z]+)?$', line) and len(line) < 50):
                            cleaned_lines.append(line)
                jobdescription = '\n'.join(cleaned_lines)
                jobdescription = re.sub(r'\n\d+\s*$', '', jobdescription)
                jobdescription = re.sub(r'\n(?:Regular|Full Time|Part Time)\s*$', '', jobdescription, flags=re.IGNORECASE)
                jobdescription = re.sub(r'\n[A-Z][a-z]+(?:,\s*[A-Z][a-z]+)?\s*$', '', jobdescription)
                jobdescription = re.sub(r'\n\s*\n\s*\n+', '\n\n', jobdescription).strip()

        jobpattern = ""
        if json_data:
            employment_type = json_data.get("employmentType", "")
            if employment_type:
                if isinstance(employment_type, list):
                    jobpattern = ", ".join(employment_type)
                else:
                    jobpattern = employment_type

        job_id = json_data.get("identifier", "") if json_data else ""

        job_dict = {
            "jobid": job_id if job_id else int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobpattern": jobpattern,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link
        }
        return job_dict


# if __name__ == "__main__":
#     scraper = ATT()
#     positions = scraper.get_positions()
#     print(f"\nNombre de positions trouvées: {len(positions)}")

#     all_jobs = []
#     if positions:
#         for i, position_link in enumerate(positions, 1):
#             print(f"Scraping [{i}/{len(positions)}]: {position_link}")
#             try:
#                 job_dict = scraper.get_position_details(position_link)
#                 all_jobs.append(job_dict)
#             except Exception as e:
#                 print(f"Error scraping {position_link}: {e}")

#     with open('att_jobs.json', 'w', encoding='utf-8') as f:
#         json.dump(all_jobs, f, indent=4, ensure_ascii=False)
    
#     print(f"\nScraping complete. Saved {len(all_jobs)} jobs to 'att_jobs.json'.")

