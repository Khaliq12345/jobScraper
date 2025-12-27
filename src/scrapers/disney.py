from time import time
from urllib.parse import urljoin
import json
import re

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Disney(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Disney",
            link="https://www.disneycareers.com/en/search-jobs",
            domain="https://www.disneycareers.com",
            companyid=33,  
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []
        page = 1
        page_size = 10

        while True:
            if page == 1:
                url = self.link
            else:
                # Format de pagination: /en/search-jobs?p=2
                url = f"{self.link}?p={page}"
            
            print(f"Page ==> {page}")

            html = self.get_html(url)
            soup = HTMLParser(html)

            # Sélecteur: #search-results-list > ul > li > a
            job_links = soup.css('#search-results-list > ul > li > a')
            
            print(f"ALL JOBS - {len(job_links)}")

            if len(job_links) == 0:
                print("NO MORE NEW PAGE")
                break

            for link in job_links:
                href = link.attributes.get("href", "")
                if href:
                    if not href.startswith("http"):
                        href = urljoin(self.domain, href)
                    if href not in position_links and "/job/" in href:
                        position_links.append(href)

            if len(job_links) < page_size:
                break

            page += 1

        return list(dict.fromkeys(position_links))

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        # Titre depuis h1
        h1_title = soup.css_first('h1')
        jobposition = h1_title.text(strip=True) if h1_title else ""

        # Description depuis div.ats-description__content
        jobdescription = ""
        desc_div = soup.css_first('div.ats-description__content')
        if desc_div:
            # Extraire le texte en préservant la structure
            jobdescription = desc_div.text(strip=True, separator="\n")
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        # Localisation depuis span.job-location
        jobcountry = ""
        jobaddress = ""
        location_span = soup.css_first('span.job-location')
        if location_span:
            location_text = location_span.text(strip=True)
            # Extraire le texte après "Location" si présent
            if "Location" in location_text:
                location_text = location_text.split("Location", 1)[-1].strip()
                # Nettoyer les espaces multiples
                location_text = re.sub(r'\s+', ' ', location_text)
            
            if location_text:
                # Séparer par la dernière virgule pour obtenir country
                parts = location_text.split(",")
                if len(parts) >= 2:
                    jobaddress = ", ".join(parts[:-1]).strip()
                    jobcountry = parts[-1].strip()
                else:
                    jobaddress = location_text
                    jobcountry = location_text

        # Job ID depuis span.job-id.job-info
        jobid = None
        job_id_span = soup.css_first('span.job-id.job-info')
        if job_id_span:
            job_id_text = job_id_span.text(strip=True)
            # Format: "Job ID 10137190" - extraire le nombre
            job_id_match = re.search(r'(\d+)', job_id_text)
            if job_id_match:
                try:
                    jobid = int(job_id_match.group(1))
                except ValueError:
                    pass
        
        if not jobid:
            jobid = int(time())


        jobpattern = ""

        job_dict = {
            "jobid": jobid,
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobniche": "", 
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "jobpattern": jobpattern,
            "scrapedsource": position_link,
            "parse_location": True
        }
        return job_dict


"""
if __name__ == "__main__":
    scraper = Disney()
    positions = scraper.get_positions()
    print(f"\nNombre de positions trouvées: {len(positions)}")

    all_jobs: list[dict] = []
    
    # Ouvrir le fichier en mode écriture pour écrire progressivement
    with open("disney_jobs.json", "w", encoding="utf-8") as f:
        f.write("[\n")  # Début du tableau JSON
        first_item = True
        
        if positions:
            for i, position_link in enumerate(positions, 1):
                print(f"\nScraping [{i}/{len(positions)}]: {position_link}")
                try:
                    job_dict = scraper.get_position_details(position_link)
                    validated_job = scraper.validate_data(job_dict)
                    job_dict_validated = validated_job.model_dump()
                    print(json.dumps(job_dict_validated, indent=2, ensure_ascii=False))
                    all_jobs.append(job_dict_validated)
                    
                    # Écrire progressivement dans le fichier
                    if not first_item:
                        f.write(",\n")
                    else:
                        first_item = False
                    
                    # Écrire l'objet JSON avec indentation
                    json_str = json.dumps(job_dict_validated, indent=4, ensure_ascii=False)
                    # Ajouter l'indentation pour chaque ligne
                    indented_lines = []
                    for line in json_str.split('\n'):
                        indented_lines.append("    " + line)
                    f.write('\n'.join(indented_lines))
                    f.flush()  # Forcer l'écriture immédiate
                    
                except Exception as e:
                    print(f"Erreur lors du scraping de {position_link}: {e}")
        
        f.write("\n]")  # Fin du tableau JSON
        f.flush()

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'disney_jobs.json'.")
"""

