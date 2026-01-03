from src.scrapers.base.base_scraper import BaseScraper
from selectolax.parser import HTMLParser
from datetime import datetime
import re
import json
import html


class Cisco(BaseScraper):
    def __init__(self, save:bool) -> None:
        super().__init__(
            name="Cisco",
            link="https://careers.cisco.com/global/en/search-results",
            domain="https://careers.cisco.com",
            companyid=34,
            save=save
        )

    def extract_phenom_json(self, text: str):
        # 1. Use regex to find the content assigned to phApp.ddo
        # It looks for "phApp.ddo =" and captures everything until the final "};"
        pattern = re.compile(r"phApp\.ddo\s*=\s*({.*?});", re.DOTALL)
        match = pattern.search(text)
        
        if match:
            json_str = match.group(1)
            try:
                # 2. Parse the string into a Python Dictionary
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return None
        else:
            print("Could not find the phApp.ddo object in the script.")
            return None

    def get_positions(self) -> list[str]:
        """Récupère toutes les URLs des offres d'emploi depuis la page de recherche"""
        position_links = set()
        offset = 0
        size = 50
        total_hits = None
        prev_len = 0
        new_len = 0
        
        while True:
            url = f"{self.link}?from={offset}&size={size}"
            print(url)
            html_content = self.get_html(url)
            soup = HTMLParser(html_content)

            scripts = soup.css("script")
            
            for script in scripts:
                script_text = script.text()
                job_data = self.extract_phenom_json(script_text)
                if not job_data:
                    continue
                search = job_data['eagerLoadRefineSearch']
                jobs = search['data']['jobs']
                for job in jobs:
                    position_links.add(f"{job['applyUrl']}::{job['department']}")

                total_hits = search['totalHits']
                new_len = len(position_links)
                print(total_hits, new_len)

     
            if total_hits and (len(position_links) >= total_hits):
                break
            
            
            if prev_len == new_len:
                break
            
            offset += size
            prev_len = new_len

        return list(position_links)

    def get_position_details(self, position_link: str) -> dict:
        """Extrait les détails d'une offre d'emploi depuis sa page"""
        position_link, department = position_link.split("::")
        html_content = self.get_html(position_link)
        soup = HTMLParser(html_content)

        jobid = ""
        jobposition = ""
        jobdescription = ""
        jobpattern = ""
        jobcountry = ""
        jobaddress = ""

        json_ld_script = soup.css_first('script[type="application/ld+json"]')
        if json_ld_script:
            try:
                json_ld = json.loads(json_ld_script.text())
                
                if "identifier" in json_ld and isinstance(json_ld["identifier"], dict):
                    jobid = json_ld["identifier"].get("value", "")
                
                jobposition = json_ld.get("title", "")
                
                desc_html = json_ld.get("description", "")
                if desc_html:
                    desc_html = html.unescape(desc_html)
                    desc_text = re.sub(r'<[^>]+>', ' ', desc_html)
                    desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                    if "Why Cisco?" in desc_text:
                        desc_text = desc_text.split("Why Cisco?")[0].strip()
                    jobdescription = desc_text
                
                if "employmentType" in json_ld:
                    emp_type = json_ld["employmentType"]
                    emp_type = emp_type[0] if isinstance(emp_type, list) and len(emp_type) > 0 else emp_type
                    if isinstance(emp_type, str):
                        jobpattern = "full-time" if "FULL_TIME" in emp_type.upper() else jobpattern
                        jobpattern = "part-time" if "PART_TIME" in emp_type.upper() else jobpattern
                
                if "jobLocation" in json_ld:
                    location = json_ld["jobLocation"]
                    if isinstance(location, dict) and "address" in location:
                        address = location["address"]
                        if isinstance(address, dict):
                            address_parts = []
                            if "addressLocality" in address:
                                address_parts.append(address["addressLocality"])
                            if "addressRegion" in address:
                                address_parts.append(address["addressRegion"])
                            if "postalCode" in address:
                                address_parts.append(address["postalCode"])
                            jobaddress = ", ".join(address_parts) if address_parts else ""
                            
                            if "addressCountry" in address:
                                country = address["addressCountry"]
                                jobcountry = country.get("name", "") if isinstance(country, dict) else (country if isinstance(country, str) else "")
            except json.JSONDecodeError:
                pass

        job_dict = {
            'jobid': int(datetime.now().timestamp()),
            'companyid': self.companyid,
            'jobposition': jobposition,
            'jobdescription': jobdescription,
            'jobpattern': jobpattern,
            'jobcountry': jobcountry,
            'jobaddress': jobaddress,
            'scrapedsource': position_link,
            'jobniche': department
        }
        return job_dict

