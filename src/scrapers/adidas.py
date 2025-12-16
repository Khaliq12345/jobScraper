from datetime import datetime
from urllib.parse import urljoin
import json
from xml.etree import ElementTree as ET

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

        # On met le pays dans jobcountry, et l'adresse complète dans jobaddress
        parts = [p for p in [city, state, country] if p]
        jobaddress = ", ".join(parts) if parts else ""
        jobcountry = country

        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobpattern": jobpattern,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link,
        }

        return job_dict

"""
if __name__ == "__main__":
    scraper = Adidas()
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

    with open("adidas_jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=4, ensure_ascii=False)

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'adidas_jobs.json'.")
"""

