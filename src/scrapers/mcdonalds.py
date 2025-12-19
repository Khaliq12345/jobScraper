from time import time
from urllib.parse import urljoin
import json
import re

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class McDonalds(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="McDonald's",
            link="https://careers.mcdonalds.com/jobs",
            domain="https://careers.mcdonalds.com",
            companyid=32,  
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []
        page = 1
        page_size = 10

        while True:
            if page == 1:
                url = self.link
            else:
                # La pagination peut être gérée via des paramètres URL
                url = f"{self.link}?page={page}"
            
            print(f"Page ==> {page}")

            html = self.get_html(url)
            soup = HTMLParser(html)


            # Sélecteur: a.results-list__item-title--link
            job_links = soup.css('a.results-list__item-title--link')
            
            # Si pas trouvé, essayer de chercher dans window.__PRELOAD_STATE__
            if len(job_links) == 0:
                # Chercher dans window.__PRELOAD_STATE__ qui contient les données JSON
                scripts = soup.css('script')
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
                        except (json.JSONDecodeError, KeyError):
                            pass
            
            print(f"ALL JOBS - {len(job_links)}")

            # Extraire les liens depuis les éléments HTML trouvés
            for link in job_links:
                href = link.attributes.get("href", "")
                if href:
                    if not href.startswith("http"):
                        href = urljoin(self.domain, href)
                    
                    if href and href not in position_links and "/job/" in href:
                        position_links.append(href)

            if len(job_links) == 0 and len(position_links) == 0:
                print("NO MORE NEW PAGE")
                break

            if len(job_links) < page_size and len(position_links) > 0:
                # Si on a déjà des liens depuis le JSON, continuer
                if page > 1:
                    break

            page += 1

        return list(dict.fromkeys(position_links))

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        # Titre
        h1_title = soup.css_first('h1.job-header-title__main')
        jobposition = h1_title.text(strip=True) if h1_title else ""

        # Description depuis div.description
        desc_div = soup.css_first('div.description')
        jobdescription = ""
        if desc_div:
            jobdescription = desc_div.text(strip=True, separator="\n")
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        # Job ID depuis dd.summary-value.reqid
        jobid = None
        reqid_dd = soup.css_first('dd.summary-value.reqid')
        if reqid_dd:
            reqid_text = reqid_dd.text(strip=True)
            try:
                jobid = int(reqid_text)
            except ValueError:
                pass
        
        if not jobid:
            jobid = int(time())

        # Jobniche depuis les catégories
        jobniche = ""
        # Localisation complète (adresse + pays ensemble)
        jobcountry = ""
        jobaddress = ""
        
        location_items = soup.css('dl.summary-list-item')
        for item in location_items:
            label = item.css_first('dt.summary-label')
            value = item.css_first('dd.summary-value')
            if label and value:
                label_text = label.text(strip=True)
                if "Categories" in label_text:
                    # Extraire les catégories depuis ul > li
                    categories_ul = value.css_first('ul')
                    if categories_ul:
                        categories = categories_ul.css('li')
                        if categories:
                            # Prendre la première catégorie
                            jobniche = categories[0].text(strip=True)
                elif "Location" in label_text:
                    # Extraire la localisation complète
                    location_text = value.text(strip=True)
                    if location_text:
                        # Mettre la localisation complète dans les deux champs
                        jobcountry = location_text
                        jobaddress = location_text

        # Pattern géré par validate_data
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
    scraper = McDonalds()
    positions = scraper.get_positions()
    print(f"\nNombre de positions trouvées: {len(positions)}")

    all_jobs: list[dict] = []
    
    # Ouvrir le fichier en mode écriture pour écrire progressivement
    with open("mcdonalds_jobs.json", "w", encoding="utf-8") as f:
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

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'mcdonalds_jobs.json'.")

"""