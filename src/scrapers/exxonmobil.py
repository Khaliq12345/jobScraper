from time import time
from urllib.parse import urljoin
import json
import re

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class ExxonMobil(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="ExxonMobil",
            link="https://jobs.exxonmobil.com/search/",
            domain="https://jobs.exxonmobil.com",
            companyid=999,
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []
        startrow = 0
        page_size = 25

        while True:
            if startrow == 0:
                url = self.link
            else:
                url = f"{self.link}?q=&sortColumn=referencedate&sortDirection=desc&startrow={startrow}"

            html = self.get_html(url)
            soup = HTMLParser(html)

            positions = soup.css('a.jobTitle-link')
            print(f"ALL JOBS - {len(positions)}")

            if not positions:
                break

            for position in positions:
                position_link = position.attributes.get("href", "")
                if position_link:
                    position_link = urljoin(self.domain, position_link)
                    if position_link not in position_links:
                        position_links.append(position_link)

            if len(positions) < page_size:
                break

            startrow += page_size

        return list(dict.fromkeys(position_links))

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        jobposition = soup.css_first('span[itemprop="title"]')
        jobposition = jobposition.text(strip=True) if jobposition else ""

        jobdescription = ""
        desc_span = soup.css_first('span[itemprop="description"]')
        if desc_span:
            jobdescription = desc_span.text(strip=True, separator="\n")
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        jobcountry = ""
        jobaddress = ""
        locality = soup.css_first('meta[itemprop="addressLocality"]')
        region = soup.css_first('meta[itemprop="addressRegion"]')
        country = soup.css_first('meta[itemprop="addressCountry"]')
        
        parts = []
        if locality:
            parts.append(locality.attributes.get("content", ""))
        if region:
            parts.append(region.attributes.get("content", ""))
        
        if country:
            jobcountry = country.attributes.get("content", "")
            if jobcountry:
                parts.append(jobcountry)
        
        if parts:
            jobaddress = ", ".join(filter(None, parts))

        jobniche = ""
        industry = soup.css_first('span[itemprop="industry"]')
        if industry:
            jobniche = industry.text(strip=True)

        job_dict = {
            "jobid": int(time()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobniche": jobniche,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link,
            "parse_location": True
        }
        return job_dict

"""
if __name__ == "__main__":
    scraper = ExxonMobil()
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

    with open("exxonmobil_jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=4, ensure_ascii=False)

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'exxonmobil_jobs.json'.")
    """

