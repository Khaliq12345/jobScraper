from datetime import datetime
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

import cloudscraper
from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Adidas(BaseScraper):
    def __init__(self, save: bool, companyid: int) -> None:
        super().__init__(
            name="Adidas",
            link="https://careers.adidas-group.com/jobs",
            domain="https://careers.adidas-group.com",
            companyid=companyid,
            save=save
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

        print(f"TOTAL JOBS - {len(position_links)}")

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
        jobaddress = jobaddress.replace(jobcountry, "")

        jobniche = soup.css_first('span[data-careersite-propertyid="facility"]')
        jobniche = jobniche.text(strip=True) if jobniche else ""

        # Données de base du job_dict
        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobpattern": jobpattern,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "jobniche": jobniche,
            "scrapedsource": position_link,
        }
        return job_dict
