from src.scrapers.base.base_scraper import BaseScraper
from selectolax.parser import HTMLParser
from datetime import datetime
import re
import json
import html


class Cisco(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Cisco",
            link="https://careers.cisco.com/global/en/search-results",
            domain="https://careers.cisco.com",
            companyid=17
        )

    def get_positions(self) -> list[str]:
        """Récupère toutes les URLs des offres d'emploi depuis la page de recherche"""
        position_links = set()
        offset = 0
        size = 50
        total_hits = None
        
        while True:
            url = f"{self.link}?from={offset}&size={size}"
            html_content = self.get_html(url)
            soup = HTMLParser(html_content)

            scripts = soup.css("script")
            jobs_found = False
            
            for script in scripts:
                script_text = script.text()
                # On cherche le script qui contient les données des jobs dans phApp.ddo
                if "phApp.ddo" in script_text and "eagerLoadRefineSearch" in script_text:
                    try:
                        # Trouver le début de l'objet phApp.ddo (peut être écrit avec ou sans espace)
                        ddo_start = script_text.find('phApp.ddo = {')
                        ddo_start = ddo_start if ddo_start != -1 else script_text.find('phApp.ddo={')
                        
                        if ddo_start != -1:
                            # Trouver la première accolade ouvrante qui marque le début du JSON
                            json_start = script_text.find('{', ddo_start)
                            if json_start != -1:
                                # Variables pour suivre l'état lors du parcours du JSON
                                brace_count = 0  # Compteur d'accolades pour savoir quand on ferme l'objet principal
                                in_string = False  # Indique si on est actuellement dans une chaîne de caractères
                                escape_next = False  # Indique si le prochain caractère est échappé (ex: \")
                                json_end = json_start
                                
                                # Parcourir caractère par caractère pour trouver la fin du JSON
                                # On doit faire ça manuellement car le JSON peut contenir des accolades
                                # dans les chaînes de caractères qu'il ne faut pas compter
                                for i in range(json_start, len(script_text)):
                                    char = script_text[i]
                                    
                                    # Si le caractère précédent était un backslash, on ignore ce caractère
                                    # (c'est un caractère échappé, comme \" ou \\)
                                    if escape_next:
                                        escape_next = False
                                        continue
                                    
                                    # Si on rencontre un backslash, le prochain caractère sera échappé
                                    if char == '\\':
                                        escape_next = True
                                        continue
                                    
                                    # Si on rencontre un guillemet non échappé, on entre/sort d'une chaîne
                                    if char == '"' and not escape_next:
                                        in_string = not in_string
                                        continue
                                    
                                    # On ne compte les accolades que si on n'est pas dans une chaîne
                                    # (sinon on compterait les accolades qui sont dans le texte des descriptions)
                                    if not in_string:
                                        if char == '{':
                                            brace_count += 1  # Accolade ouvrante : on entre dans un objet
                                        elif char == '}':
                                            brace_count -= 1  # Accolade fermante : on sort d'un objet
                                            # Quand le compteur revient à 0, on a fermé l'objet principal
                                            if brace_count == 0:
                                                json_end = i + 1  # +1 pour inclure l'accolade fermante
                                                break
                                
                                # Extraire la chaîne JSON complète
                                json_str = script_text[json_start:json_end]
                                # Parser le JSON en objet Python
                                ddo_data = json.loads(json_str)
                                # Récupérer la section qui contient les jobs
                                eager_data = ddo_data.get("eagerLoadRefineSearch", {})
                                
                                # Récupérer le nombre total de jobs disponibles (pour la pagination)
                                if total_hits is None:
                                    total_hits = eager_data.get("totalHits", 0)
                                
                                # Extraire la liste des jobs de cette page
                                jobs_data = eager_data.get("data", {}).get("jobs", [])
                                
                                if jobs_data:
                                    jobs_found = True
                                    
                                    # Pour chaque job, construire l'URL complète
                                    for job in jobs_data:
                                        job_id = job.get("jobId", "")
                                        title = job.get("title", "")
                                        
                                        if job_id and title:
                                            # Créer un slug à partir du titre pour l'URL
                                            # (ex: "Software Engineer" -> "software-engineer")
                                            title_slug = title.lower().replace(" ", "-").replace("/", "-")
                                            # Enlever tous les caractères non alphanumériques sauf les tirets
                                            title_slug = re.sub(r'[^a-z0-9-]', '', title_slug)
                                            # Remplacer les tirets multiples par un seul tiret
                                            title_slug = re.sub(r'-+', '-', title_slug)
                                            # Construire l'URL complète du job
                                            position_link = f"{self.domain}/global/en/job/{job_id}/{title_slug}"
                                            position_links.add(position_link)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        # Si le parsing échoue, on ignore ce script et on continue
                        pass

            if not jobs_found:
                break
            
            if total_hits and len(position_links) >= total_hits:
                break
            
            offset += size
            
            if offset > 10000:
                break

        return list(position_links)

    def get_position_details(self, position_link: str) -> dict:
        """Extrait les détails d'une offre d'emploi depuis sa page"""
        html_content = self.get_html(position_link)
        soup = HTMLParser(html_content)

        jobid = ""
        jobposition = ""
        jobdescription = ""
        jobpattern = ""
        jobcountry = ""
        jobaddress = ""

        json_ld_script = soup.css_first('script[type="application/ld+json"]')
        if json_ld_script:
            try:
                json_ld = json.loads(json_ld_script.text())
                
                if "identifier" in json_ld and isinstance(json_ld["identifier"], dict):
                    jobid = json_ld["identifier"].get("value", "")
                
                jobposition = json_ld.get("title", "")
                
                desc_html = json_ld.get("description", "")
                if desc_html:
                    desc_html = html.unescape(desc_html)
                    desc_text = re.sub(r'<[^>]+>', ' ', desc_html)
                    desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                    if "Why Cisco?" in desc_text:
                        desc_text = desc_text.split("Why Cisco?")[0].strip()
                    jobdescription = desc_text
                
                if "employmentType" in json_ld:
                    emp_type = json_ld["employmentType"]
                    emp_type = emp_type[0] if isinstance(emp_type, list) and len(emp_type) > 0 else emp_type
                    if isinstance(emp_type, str):
                        jobpattern = "Full time" if "FULL_TIME" in emp_type.upper() else jobpattern
                        jobpattern = "Part time" if "PART_TIME" in emp_type.upper() else jobpattern
                
                if "jobLocation" in json_ld:
                    location = json_ld["jobLocation"]
                    if isinstance(location, dict) and "address" in location:
                        address = location["address"]
                        if isinstance(address, dict):
                            address_parts = []
                            if "addressLocality" in address:
                                address_parts.append(address["addressLocality"])
                            if "addressRegion" in address:
                                address_parts.append(address["addressRegion"])
                            if "postalCode" in address:
                                address_parts.append(address["postalCode"])
                            jobaddress = ", ".join(address_parts) if address_parts else ""
                            
                            if "addressCountry" in address:
                                country = address["addressCountry"]
                                jobcountry = country.get("name", "") if isinstance(country, dict) else (country if isinstance(country, str) else "")
            except json.JSONDecodeError:
                pass

        job_dict = {
            'jobid': int(jobid) if jobid and jobid.isdigit() else int(datetime.now().timestamp()),
            'jobposition': jobposition,
            'jobdescription': jobdescription,
            'jobpattern': jobpattern,
            'jobcountry': jobcountry,
            'jobaddress': jobaddress,
            'scrapedsource': position_link
        }
        return job_dict


# if __name__ == "__main__":
#     scraper = Cisco()
#     positions = scraper.get_positions()
#     print(f"\nNombre de positions trouvées: {len(positions)}")

#     all_jobs = []
#     if positions:
#         for i, position_link in enumerate(positions, 1):
#             print(f"\nScraping [{i}/{len(positions)}]: {position_link}")
#             try:
#                 job_dict = scraper.get_position_details(position_link)
#                 print(json.dumps(job_dict, indent=2, ensure_ascii=False))
#                 print("-" * 80)
#                 all_jobs.append(job_dict)
#             except Exception as e:
#                 print(f"Error scraping {position_link}: {e}")

#     with open('cisco_jobs.json', 'w', encoding='utf-8') as f:
#         json.dump(all_jobs, f, indent=4, ensure_ascii=False)
    
#     print(f"\nScraping complete. Saved {len(all_jobs)} jobs to 'cisco_jobs.json'.")

