from datetime import datetime
from urllib.parse import urljoin
import json

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Sysco(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Sysco",
            link="https://careers.sysco.com/en/search-jobs",
            domain="https://careers.sysco.com",
            companyid=75,
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []

        html = self.get_html(self.link)
        soup = HTMLParser(html)

        # Les liens des offres sont dans un <a> directement sous chaque <li> de #search-results-list
        anchors = soup.css("#search-results-list ul li a")

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

        # Les détails sont disponibles en JSON-LD dans un script type application/ld+json
        script = soup.css_first('script[type="application/ld+json"]')
        data = json.loads(script.text()) if script else {}

        jobposition = data.get("title", "")

        desc_html = data.get("description", "") or ""
        # On enlève les balises HTML pour ne garder que du texte brut
        jobdescription = (
            HTMLParser(desc_html).text(strip=True, separator=" ") if desc_html else ""
        )

        # Job pattern (type de contrat) et salaire sont dans les blocs .job-info
        jobpattern = ""
        jobsalary = ""
        for info in soup.css("p.job-info, span.job-info"):
            label_el = info.css_first("b")
            if not label_el:
                continue
            label = label_el.text(strip=True)
            full_text = info.text(strip=True, separator=" ")
            value = full_text.replace(label, "", 1).strip(" :")

            if label == "Employment Type" and not jobpattern:
                jobpattern = value
            elif label == "Compensation" and not jobsalary:
                jobsalary = value

        jobcountry = ""
        job_location = data.get("jobLocation") or []
        if isinstance(job_location, list) and job_location:
            address = job_location[0].get("address", {})
            jobcountry = address.get("addressCountry", "") or ""

        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobpattern": jobpattern,
            "jobsalary": jobsalary,
            "jobcountry": jobcountry,
            "scrapedsource": position_link,
        }

        return job_dict

"""
if __name__ == "__main__":
    scraper = Sysco()
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

    with open("sysco_jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=4, ensure_ascii=False)

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'sysco_jobs.json'.")
"""
