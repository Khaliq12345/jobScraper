from datetime import datetime
from urllib.parse import urljoin
import json

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class CapitecBank(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Capitec Bank",
            link="https://careers.capitecbank.co.za/search/",
            domain="https://careers.capitecbank.co.za",
            companyid=74,
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []

        html = self.get_html(self.link)
        soup = HTMLParser(html)

        # Les liens des offres sont dans un <a> à l'intérieur de <span class="jobTitle hidden-phone">
        # Exemple de chemin CSS vu dans le navigateur :
        # #searchresults > tbody > tr:nth-child(1) > td.colTitle > span > a
        anchors = soup.css(
            "table#searchresults tbody tr.data-row td.colTitle span.jobTitle a.jobTitle-link"
        )

        for a in anchors:
            href = a.attributes.get("href")
            if not href:
                continue
            position_link = urljoin(self.domain, href)
            position_links.append(position_link)

        return position_links

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        title_el = soup.css_first("h1#job-title")
        jobposition = title_el.text(strip=True) if title_el else ""

        location_el = soup.css_first("p#job-location span.jobGeoLocation")
        jobcountry = location_el.text(strip=True) if location_el else ""

        desc_el = soup.css_first("span.jobdescription")
        jobdescription = desc_el.text(strip=True, separator=" ") if desc_el else ""

        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobcountry": jobcountry,
            "scrapedsource": position_link,
        }

        return job_dict

"""
if __name__ == "__main__":
    scraper = CapitecBank()
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

    with open("capitec_bank_jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=4, ensure_ascii=False)

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'capitec_bank_jobs.json'.")
"""


