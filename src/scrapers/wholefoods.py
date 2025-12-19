from time import time
from urllib.parse import urljoin
import json
import re

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class WholeFoods(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Whole Foods",
            link="https://careers.wholefoods.com/jobs",
            domain="https://careers.wholefoods.com",
            companyid=34,
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []
        page = 1
        page_size = 10

        while True:
            if page == 1:
                url = self.link
            else:
                url = f"{self.link}/page/{page}"
            
            print(f"Page ==> {page}")

            html = self.get_html(url)
            soup = HTMLParser(html)

            # Essayer d'extraire depuis window.__PRELOAD_STATE__ d'abord
            scripts = soup.css('script')
            jobs_found = False
            for script in scripts:
                script_text = script.text()
                if '__PRELOAD_STATE__' in script_text:
                    try:
                        # Extraire le JSON depuis window.__PRELOAD_STATE__ = {...};
                        json_start = script_text.find('window.__PRELOAD_STATE__ = ') + len('window.__PRELOAD_STATE__ = ')
                        json_end = script_text.find(';', json_start)
                        if json_end == -1:
                            json_end = script_text.find('\n', json_start)
                        
                        json_str = script_text[json_start:json_end].strip()
                        preload_data = json.loads(json_str)
                        
                        # Extraire les jobs depuis preload_data
                        if 'jobSearch' in preload_data and 'jobs' in preload_data['jobSearch']:
                            jobs = preload_data['jobSearch']['jobs']
                            for job in jobs:
                                if 'originalURL' in job:
                                    href = f"/{job['originalURL']}"
                                    if not href.startswith("http"):
                                        href = urljoin(self.domain, href)
                                    if href not in position_links:
                                        position_links.append(href)
                            jobs_found = True
                            print(f"ALL JOBS - {len(jobs)}")
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Erreur lors de l'extraction JSON: {e}")
                        pass

            # Fallback: chercher les liens dans le HTML
            if not jobs_found:
                job_links = soup.css('a[href*="/job/"]')
                print(f"ALL JOBS - {len(job_links)}")
                
                for link in job_links:
                    href = link.attributes.get("href", "")
                    if href:
                        if not href.startswith("http"):
                            href = urljoin(self.domain, href)
                        if href not in position_links and "/job/" in href:
                            position_links.append(href)

            if len(position_links) == 0:
                print("NO MORE NEW PAGE")
                break

            # Vérifier s'il y a une page suivante
            if not jobs_found:
                # Si on utilise le fallback HTML, vérifier le nombre de jobs trouvés
                if len(job_links) < page_size:
                    break
            else:
                # Si on utilise JSON, vérifier le nombre total de jobs
                if 'jobSearch' in preload_data and 'totalJob' in preload_data['jobSearch']:
                    total_jobs = preload_data['jobSearch']['totalJob']
                    if len(position_links) >= total_jobs:
                        break

            page += 1

        return list(dict.fromkeys(position_links))

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        # Titre depuis h1
        h1_title = soup.css_first('h1.hd-2')
        if not h1_title:
            h1_title = soup.css_first('h1')
        jobposition = h1_title.text(strip=True) if h1_title else ""

        # Description depuis div.description
        jobdescription = ""
        desc_div = soup.css_first('div.description')
        if desc_div:
            jobdescription = desc_div.text(strip=True, separator="\n")
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        # Localisation depuis div.job-location.body-l
        jobcountry = ""
        jobaddress = ""
        location_div = soup.css_first('div.job-location.body-l')
        if location_div:
            location_text = location_div.text(strip=True)
            if location_text:
                # Format: "5110 Telegraph Ave, Oakland CA 94609-1926, United States"
                parts = location_text.split(",")
                if len(parts) >= 3:
                    jobaddress = ", ".join(parts[:-1]).strip()
                    jobcountry = parts[-1].strip()
                elif len(parts) == 2:
                    jobaddress = parts[0].strip()
                    jobcountry = parts[1].strip()
                else:
                    jobaddress = location_text
                    jobcountry = location_text

        # Jobniche depuis span.eyebrow
        jobniche = ""
        eyebrow_span = soup.css_first('span.eyebrow')
        if eyebrow_span:
            jobniche = eyebrow_span.text(strip=True)

        # Job ID depuis dd.summary-value.reqid
        jobid = None
        reqid_dd = soup.css_first('dd.summary-value.reqid')
        if reqid_dd:
            reqid_text = reqid_dd.text(strip=True)
            # Format: "Req-202504000420"
            reqid_match = re.search(r'Req-(\d+)', reqid_text)
            if reqid_match:
                try:
                    jobid = int(reqid_match.group(1))
                except ValueError:
                    pass
        
        if not jobid:
            jobid = int(time())

        # Pattern 
        jobpattern = ""

        job_dict = {
            "jobid": jobid,
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobniche": jobniche,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "jobpattern": jobpattern,
            "scrapedsource": position_link,
            "parse_location": True
        }
        return job_dict

"""
if __name__ == "__main__":
    scraper = WholeFoods()
    positions = scraper.get_positions()
    print(f"\nNombre de positions trouvées: {len(positions)}")

    all_jobs: list[dict] = []
    
    # Ouvrir le fichier en mode écriture pour écrire progressivement
    with open("wholefoods_jobs.json", "w", encoding="utf-8") as f:
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

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'wholefoods_jobs.json'.")

"""