import time
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Airbnb(BaseScraper):
    def __init__(self, save: bool) -> None:
        super().__init__(
            name="Airbnb",
            link="https://careers.airbnb.com/positions/",
            domain="https://careers.airbnb.com",
            companyid=19,
            save=save
        )

    def get_positions(self) -> list[str]:
        position_links = []
        page = 1

        while True:
            url = f"{self.link}?_paged={page}"
            print(f"Scraping page {page} → {url}")
            html = self.get_html(url)
            if not html:
                break

            tree = HTMLParser(html)
            jobs = tree.css("li.inner-grid")
            if not jobs:
                print("Fin de pagination")
                break

            print(f"{len(jobs)} offres sur la page {page}")
            for job in jobs:
                a = job.css_first("h3 a")
                if a and a.attributes.get("href"):
                    full_url = urljoin(self.domain, a.attributes["href"])
                    if full_url not in position_links:
                        position_links.append(full_url)

            page += 1
            time.sleep(0.7)

        print(f"TOTAL OFFRES AIRBNB : {len(position_links)}")
        return position_links

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        if not html:
            return {}

        tree = HTMLParser(html)

        # === Titre ===
        title = tree.css_first("h1.text-size-12") or tree.css_first("h1")
        jobposition = title.text(strip=True) if title else ""

        # === ID === (extrait de l'URL ou du data-job-id)
        job_id = position_link.rstrip("/").split("/")[-1]
        # Alternative: extraire du data-job-id
        job_div = tree.css_first("div.job-application")
        if job_div and "data-job-id" in job_div.attributes:
            job_id = job_div.attributes["data-job-id"]

        # === Localisation ===
        location_elem = tree.css_first("div.offices span.text-size-4")
        location_raw = location_elem.text(strip=True) if location_elem else ""

        # Parsing ville/état/pays
        city = state = country = ""
        if location_raw:
            # Le HTML montre juste "United States"
            if "United States" in location_raw:
                country = "United States"
            else:
                # Pour d'autres formats
                parts = [p.strip() for p in location_raw.split(",")]
                if len(parts) == 1:
                    country = parts[0]
                elif len(parts) == 2:
                    city, country = parts[0], parts[1]
                elif len(parts) >= 3:
                    city, state, country = parts[0], parts[1], parts[2]

        # === Description complète ===
        desc_parts = []

        # 1. Introduction
        content_intro = tree.css_first("div.content-intro")
        if content_intro:
            desc_parts.append(content_intro.text(strip=True))

        # 2. Tout le contenu principal
        job_detail = tree.css_first("div.job-detail.active")
        if job_detail:
            # Exclure certaines parties si nécessaire
            for unwanted in job_detail.css("div.content-pay-transparency, .hidden"):
                unwanted.decompose()

            # Récupérer tout le texte
            desc_text = job_detail.text(separator="\n", strip=True)
            if desc_text:
                desc_parts.append(desc_text)

        job_description = "\n\n".join(desc_parts).strip()

        # === Salaire ===
        pay_range_elem = tree.css_first("div.pay-range")
        pay_range = pay_range_elem.text() if pay_range_elem else ""

        # === Work Mode (Remote/Hybrid/On-site) ===
        workmode = ""
        desc_lower = job_description.lower()
        if "remote" in desc_lower and "office" in desc_lower:
            workmode = "Hybrid"
        elif "remote" in desc_lower and "eligible" in desc_lower:
            workmode = "Remote"
        elif "on-site" in desc_lower or "onsite" in desc_lower:
            workmode = "On-site"

        # === Niche / Département ===
        jobniche = ""

        job_dict = {
            "jobid": job_id,
            "jobposition": jobposition,
            "jobdescription": job_description,
            "jobpattern": workmode,
            "jobsalary": pay_range,
            "jobniche": jobniche,
            "jobcountry": country,
            "jobaddress": f"{city} {state}".strip(),
            "joblocation": location_raw,
            "scrapedsource": position_link,
            "companyid": self.companyid,
        }

        return job_dict
