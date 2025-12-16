from datetime import datetime
from urllib.parse import urljoin
import json
from xml.etree import ElementTree as ET
import re

import cloudscraper
from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Adidas(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Adidas",
            link="https://careers.adidas-group.com/jobs",
            domain="https://careers.adidas-group.com",
            companyid=77,
        )

    def _get_html_adidas(self, url: str) -> str:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def get_positions(self) -> list[str]:
        position_links: list[str] = []

        # On passe par le flux global /jobs/feed.xml pour récupérer toutes les offres car la pagination se fait dynamiquement 
        #avec un bouton "Charger plus" en bas de la page limitant le nombre d'offres
        feed_url = self.link.rstrip("/") + "/feed.xml"
        feed_xml = self._get_html_adidas(feed_url)
        root = ET.fromstring(feed_xml)

        # Le flux est un XML simple : chaque bloc <job> contient une balise <url>
        # qui pointe directement vers la page détail de l'offre.
        for job_el in root.findall(".//job"):
            url_el = job_el.find("url")
            href = (url_el.text or "").strip() if url_el is not None else ""
            if not href:
                continue
            position_link = urljoin(self.domain, href)
            position_links.append(position_link)

        # On enlève les doublons en conservant l'ordre
        return list(dict.fromkeys(position_links))

    def get_position_details(self, position_link: str) -> dict:
        html = self._get_html_adidas(position_link)
        soup = HTMLParser(html)

        # Titre du poste
        title_el = soup.css_first('span[data-careersite-propertyid="title"]')
        jobposition = title_el.text(strip=True) if title_el else ""

        # Description (corps principal de l'annonce)
        desc_el = soup.css_first("span.jobdescription")
        jobdescription = (
            desc_el.text(strip=True, separator=" ") if desc_el else ""
        )

        # Experience : on mappe les formats "x-y years" en gardant la dernière année (y years)
        jobexperience = ""
        text_lower = (jobdescription or "").lower()
        range_match = re.search(r"(\d+)\s*-\s*(\d+)\s+years", text_lower)
        if range_match:
            last_year = range_match.group(2)
            jobexperience = f"{last_year} years"

        # Localisation (ville / état / pays)
        city_el = soup.css_first('span[data-careersite-propertyid="city"]')
        state_el = soup.css_first('span[data-careersite-propertyid="state"]')
        country_el = soup.css_first('span[data-careersite-propertyid="country"]')

        city = city_el.text(strip=True) if city_el else ""
        state = state_el.text(strip=True) if state_el else ""
        country = country_el.text(strip=True) if country_el else ""

        # Type de contrat
        pattern_el = soup.css_first('span[data-careersite-propertyid="shifttype"]')
        jobpattern = pattern_el.text(strip=True) if pattern_el else ""
        # Normalisation des valeurs de pattern 
        pattern_map = {
            "temp": "Temporary",
            "temporary": "Temporary",
            "part time": "Part Time",
            "part-time": "Part Time",
            "full time": "Full Time",
            "full-time": "Full Time",
            "pupil": "Temporary",
            "limited duration": "Contract",
            "seasonal": "Seasonal",
        }
        norm = pattern_map.get(jobpattern.lower())
        if norm:
            jobpattern = norm

        # On met le pays dans jobcountry, et l'adresse complète dans jobaddress
        parts = [p for p in [city, state, country] if p]
        jobaddress = ", ".join(parts) if parts else ""
        jobcountry = country

        jobniche = "Job"

        # Données de base du job_dict
        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobexperience": jobexperience,  
            "jobpattern": jobpattern,
            "jobniche": jobniche,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link,
        }

        # Utiliser validate_data 
        parsed = self.validate_data(job_dict)
        job_dict["jobqualifications"] = parsed.jobqualifications
        job_dict["jobexperience"] = parsed.jobexperience
        job_dict["jobpattern"] = parsed.jobpattern
        job_dict["jobsalary"] = parsed.jobsalary

        return job_dict

"""
if __name__ == "__main__":
    scraper = Adidas()
    positions = scraper.get_positions()
    print(f"\nNombre de positions trouvées: {len(positions)}")

    output_path = "adidas_jobs.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("[\n")
        first = True

        if positions:
            for i, position_link in enumerate(positions, 1):
                print(f"\nScraping [{i}/{len(positions)}]: {position_link}")
                try:
                    job_dict = scraper.get_position_details(position_link)
                    print(json.dumps(job_dict, indent=2, ensure_ascii=False))

                    if not first:
                        f.write(",\n")
                    f.write(json.dumps(job_dict, ensure_ascii=False, indent=2))
                    f.flush()
                    first = False
                except Exception as e:
                    print(f"Erreur lors du scraping de {position_link}: {e}")
                    continue

        f.write("\n]\n")
        f.flush()

    print("\nScraping terminé. Résultats écrits progressivement dans 'adidas_jobs.json'.")
    
"""


