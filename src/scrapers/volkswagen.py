from datetime import datetime
from urllib.parse import urljoin
import json

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Volkswagen(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Volkswagen",
            link="https://jobs.volkswagen-group.com/search/",
            domain="https://jobs.volkswagen-group.com",
            companyid=78,
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []
        startrow = 0

        while True:
            page_url = (
                self.link if startrow == 0 else f"{self.link}?startrow={startrow}"
            )
            html = self.get_html(page_url)
            soup = HTMLParser(html)

            anchors = soup.css(
                "table#searchresults tbody tr.data-row td.colTitle span.jobTitle a.jobTitle-link"
            )
            if not anchors:
                break

            for a in anchors:
                href = a.attributes.get("href")
                if not href:
                    continue
                position_link = urljoin(self.domain, href)
                position_links.append(position_link)

            # La page liste 25 résultats par défaut ; si on en a moins, on est sur la dernière page.
            if len(anchors) < 25:
                break

            startrow += 25

        # On enlève les doublons en conservant l'ordre
        return list(dict.fromkeys(position_links))

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        # Titre du poste
        title_el = soup.css_first('span[data-careersite-propertyid="title"]')
        jobposition = title_el.text(strip=True) if title_el else ""

        # Description (corps principal de l'annonce)
        desc_el = soup.css_first("span.jobdescription")
        jobdescription = (
            desc_el.text(strip=True, separator=" ") if desc_el else ""
        )

        # Localisation 
        loc_el = soup.css_first("p#job-location span.jobGeoLocation")
        location_text = loc_el.text(strip=True) if loc_el else ""

        jobaddress = location_text
        jobcountry = ""
        if location_text:
            parts = [p.strip() for p in location_text.split(",") if p.strip()]
            # ville, état, pays, code postal ; on prend l'avant-dernier comme pays.
            if len(parts) >= 3:
                jobcountry = parts[-2]

        # Working Model (Full-time, Part-time,..)
        pattern_el = soup.css_first('span[data-careersite-propertyid="shift"]')
        jobpattern = pattern_el.text(strip=True) if pattern_el else ""

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
    scraper = Volkswagen()
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

    with open("volkswagen_jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=4, ensure_ascii=False)

    print(
        f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'volkswagen_jobs.json'."
    )
"""

