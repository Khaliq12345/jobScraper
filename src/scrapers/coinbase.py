from src.scrapers.base.base_scraper import BaseScraper
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from datetime import datetime
import json
import re
import time
import random
import cloudscraper
from bs4 import BeautifulSoup


class Coinbase(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Coinbase",
            link="https://www.coinbase.com/careers/positions",
            domain="https://www.coinbase.com",
            companyid=18
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
        # Délai aléatoire entre 15 et 25 secondes pour éviter les 429
        delay = random.uniform(15, 25)
        time.sleep(delay)
        
        headers = {
            "Referer": "https://www.coinbase.com/careers/positions",
            "Sec-Fetch-Site": "same-origin",
        }
        response = self.scraper.get(url, headers=headers)
        
        # Gérer les erreurs 429
        if response.status_code == 429:
            time.sleep(60)
            response = self.scraper.get(url, headers=headers)
        
        response.raise_for_status()
        return response.text

    def get_positions(self) -> list[str]:
        position_links = []

        page = 1
        max_pages = getattr(self, 'max_pages', None)
        while True:
            if max_pages and page > max_pages:
                break
                
            url = f"{self.link}" if page == 1 else f"{self.link}?page={page}"
            
            try:
                html = self.get_html(url)
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    break
                raise
            
            soup = HTMLParser(html)

            # Chercher d'abord dans le JSON  (server-app-state)
            scripts = soup.css("script")
            found_in_json = False
            for script in scripts:
                script_id = script.attributes.get("id", "")
                if script_id == "server-app-state":
                    try:
                        data = json.loads(script.text())
                        if "relayStoreData" in data:
                            relay_data = json.loads(data["relayStoreData"])
                            if isinstance(relay_data, dict) and "recordMap" in relay_data:
                                record_map = relay_data["recordMap"]
                                for value in record_map.values():
                                    if isinstance(value, dict) and "offerId" in str(value):
                                        value_str = json.dumps(value)
                                        matches = re.findall(r'"offerId":\s*"?(\d+)"?', value_str)
                                        for offer_id in matches:
                                            position_link = f"{self.domain}/careers/positions/{offer_id}"
                                            if position_link not in position_links:
                                                position_links.append(position_link)
                                                found_in_json = True
                    except (json.JSONDecodeError, KeyError):
                        pass
                
                # Chercher aussi dans les autres scripts
                script_text = script.text()
                if "offerId" in script_text and "positions" in script_text:
                    matches = re.findall(r'"offerId":\s*"?(\d+)"?', script_text)
                    for offer_id in matches:
                        position_link = f"{self.domain}/careers/positions/{offer_id}"
                        if position_link not in position_links:
                            position_links.append(position_link)
                            found_in_json = True

            # Chercher aussi les liens dans le HTML
            job_links = soup.css('a[href*="/careers/positions/"]')
            for link in job_links:
                href = link.attributes.get("href", "")
                if href and "/careers/positions/" in href:
                    position_link = urljoin(self.domain, href) if self.domain else href
                    position_link = position_link.split("?")[0]
                    if position_link not in position_links:
                        position_links.append(position_link)

            # Si aucune position trouvée, arrêter
            if len(position_links) == 0:
                break

            page += 1

        return position_links

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)
        bs_soup = BeautifulSoup(html, 'html.parser')

        # Extraire le JSON-LD qui contient les données structurées
        json_ld = None
        json_ld_script = soup.css_first('script[type="application/ld+json"]')
        if json_ld_script:
            try:
                json_ld = json.loads(json_ld_script.text())
            except json.JSONDecodeError:
                pass

        # Job ID depuis l'URL (dernier segment numérique)
        job_id = ""
        url_match = re.search(r'/positions/(\d+)/?', position_link)
        if url_match:
            job_id = url_match.group(1)

        # Job Position
        jobposition = ""
        if json_ld and "title" in json_ld:
            jobposition = json_ld["title"]

        # Job Description
        jobdescription = ""
        if json_ld and "description" in json_ld:
            desc_html = json_ld["description"]
            if isinstance(desc_html, str):
                desc_soup = BeautifulSoup(desc_html, 'html.parser')
                jobdescription = desc_soup.get_text(separator="\n", strip=True)
                jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        # Job Qualifications - chercher "What we look for in you" dans la description
        jobqualifications = ""
        if jobdescription:
            parts = re.split(r'What we look for in you', jobdescription, flags=re.IGNORECASE, maxsplit=1)
            if len(parts) > 1:
                qual_text = parts[1]
                qual_text = re.split(r'Nice to haves|Job\s*#:', qual_text, flags=re.IGNORECASE, maxsplit=1)[0]
                jobqualifications = qual_text.strip()
                # Enlever les préfixes comme "(ie. job requirements):"
                jobqualifications = re.sub(r'^\([^)]+\):\s*', '', jobqualifications, flags=re.IGNORECASE)
                jobqualifications = re.sub(r'\n\s*\n+', '\n\n', jobqualifications).strip()

        # Job Pattern (Full time / Part time)
        jobpattern = ""
        if jobdescription:
            desc_lower = jobdescription.lower()
            if "full-time" in desc_lower or "full time" in desc_lower:
                jobpattern = "Full time"
            elif "part-time" in desc_lower or "part time" in desc_lower:
                jobpattern = "Part time"

        # Job Salary - chercher dans div.pay-range
        jobsalary = ""
        salary_div = soup.css_first("div.pay-range")
        if salary_div:
            salary_spans = salary_div.css("span")
            amounts = []
            for span in salary_spans:
                text = span.text(strip=True)
                if text.startswith("$"):
                    amounts.append(text)
            if len(amounts) >= 2:
                jobsalary = f"{amounts[0]} - {amounts[1]}"
            elif len(amounts) == 1:
                jobsalary = amounts[0]

        # Job Address et Country
        jobaddress = ""
        jobcountry = ""
        if json_ld and "jobLocation" in json_ld:
            location = json_ld["jobLocation"]
            if isinstance(location, dict) and "address" in location:
                address = location["address"]
                if isinstance(address, str):
                    if address.startswith("Remote"):
                        jobaddress = "Remote"
                        if " - " in address:
                            jobcountry = address.split(" - ", 1)[1].strip()
                    else:
                        jobaddress = address
                        parts = address.split(",")
                        if len(parts) > 0:
                            jobcountry = parts[-1].strip()

        job_dict = {
            "jobid": int(job_id) if job_id.isdigit() else int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobqualifications": jobqualifications,
            "jobpattern": jobpattern,
            "jobsalary": jobsalary,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link
        }
        return job_dict

