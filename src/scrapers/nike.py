from time import time
from urllib.parse import urljoin
import json
import re

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Nike(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Nike",
            link="https://careers.nike.com/jobs",
            domain="https://careers.nike.com",
            companyid=30,
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

            # Extraire les liens depuis a.results-list__item-title--link
            job_links = soup.css('a.results-list__item-title--link')
            
            print(f"ALL JOBS - {len(job_links)}")

            if len(job_links) == 0:
                print("NO MORE NEW PAGE")
                break

            for link in job_links:
                href = link.attributes.get("href", "")
                if href:
                    if not href.startswith("http"):
                        href = urljoin(self.domain, href)
                    if href not in position_links:
                        position_links.append(href)

            if len(job_links) < page_size:
                break

            page += 1

        return list(dict.fromkeys(position_links))

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        # JSON-LD - format de données structurées
        json_ld_script = soup.css_first('script[type="application/ld+json"]')
        json_data = None
        if json_ld_script:
            try:
                json_data = json.loads(json_ld_script.text())
            except json.JSONDecodeError:
                pass

        # Titre du job
        jobposition = ""
        
        # D'abord depuis JSON-LD
        if json_data:
            jobposition = json_data.get("title", "")
        
        # Sinon dans h1
        if not jobposition:
            h1_title = soup.css_first('h1')
            if h1_title:
                jobposition = h1_title.text(strip=True)
        
        # Sinon dans meta og:title
        if not jobposition:
            og_title = soup.css_first('meta[property="og:title"]')
            if og_title:
                title_content = og_title.attributes.get("content", "")
                if " in " in title_content:
                    jobposition = title_content.split(" in ")[0].strip()
                else:
                    jobposition = title_content.strip()

        # Description
        jobdescription = ""
        
        # D'abord depuis JSON-LD
        if json_data:
            desc_html = json_data.get("description", "")
            if desc_html:
                # Nettoyer le HTML
                desc_soup = HTMLParser(desc_html)
                jobdescription = desc_soup.text(strip=True, separator="\n")
                jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()
        
        # Sinon chercher dans les sections de description
        if not jobdescription:
            # Chercher dans les divs/sections avec "description" ou "job description"
            desc_elements = soup.css('div[class*="description"], section[class*="description"], div.job-description')
            for elem in desc_elements:
                text = elem.text(strip=True, separator="\n")
                if text and len(text) > 50:
                    jobdescription = re.sub(r'\n\s*\n+', '\n\n', text).strip()
                    if jobdescription:
                        break
        
        # Si pas trouvé, prendre tous les paragraphes significatifs
        if not jobdescription:
            paragraphs = soup.css('p')
            desc_parts = []
            for p in paragraphs:
                text = p.text(strip=True)
                if text and len(text) > 20:
                    desc_parts.append(text)
            if desc_parts:
                jobdescription = "\n\n".join(desc_parts)

        # Localisation
        jobcountry = ""
        jobaddress = ""
        
        # D'abord depuis JSON-LD
        if json_data:
            job_locations = json_data.get("jobLocation", [])
            if job_locations:
                if isinstance(job_locations, list) and len(job_locations) > 0:
                    location = job_locations[0]
                else:
                    location = job_locations
                
                address = location.get("address", {}) if isinstance(location, dict) else {}
                if address:
                    parts = []
                    if address.get("streetAddress"):
                        parts.append(address.get("streetAddress"))
                    if address.get("addressLocality"):
                        parts.append(address.get("addressLocality"))
                    if address.get("addressRegion"):
                        parts.append(address.get("addressRegion"))
                    if address.get("postalCode"):
                        parts.append(address.get("postalCode"))
                    
                    if parts:
                        jobaddress = ", ".join(parts)
                    if address.get("addressCountry"):
                        jobcountry = address.get("addressCountry")
        
        # Sinon chercher dans les spans avec location
        if not jobaddress:
            location_spans = soup.css('span[class*="location"], span[class*="address"], span[class*="street"]')
            for span in location_spans:
                location_text = span.text(strip=True)
                if location_text and len(location_text) > 5:
                    parts = location_text.split(",")
                    if len(parts) >= 2:
                        jobaddress = ", ".join(parts[:-1]).strip()
                        jobcountry = parts[-1].strip()
                    else:
                        jobaddress = location_text
                    break

        # Employment Type / Pattern
        jobpattern = ""
        
        # D'abord depuis JSON-LD
        if json_data:
            emp_type = json_data.get("employmentType", "")
            if emp_type:
                if isinstance(emp_type, list):
                    emp_type = emp_type[0] if emp_type else ""
                if "full" in emp_type.lower() or "temps plein" in emp_type.lower():
                    jobpattern = "Full-Time"
                elif "part" in emp_type.lower() or "temps partiel" in emp_type.lower():
                    jobpattern = "Part-Time"
                else:
                    jobpattern = emp_type
        
        # Sinon chercher dans le texte
        if not jobpattern:
            type_elements = soup.css('span, div, li')
            for elem in type_elements:
                text = elem.text(strip=True)
                if "type de poste" in text.lower() or "employment type" in text.lower():
                    if "temps plein" in text.lower() or "full time" in text.lower():
                        jobpattern = "Full-Time"
                    elif "temps partiel" in text.lower() or "part time" in text.lower():
                        jobpattern = "Part-Time"
                    break

        job_dict = {
            "jobid": int(time()),
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
    scraper = Nike()
    positions = scraper.get_positions()
    print(f"\nNombre de positions trouvées: {len(positions)}")

    all_jobs: list[dict] = []
    
    # Ouvrir le fichier en mode écriture pour écrire progressivement
    with open("nike_jobs.json", "w", encoding="utf-8") as f:
        f.write("[\n")  # Début du tableau JSON
        first_item = True
        
        if positions:
            for i, position_link in enumerate(positions, 1):
                print(f"\nScraping [{i}/{len(positions)}]: {position_link}")
                try:
                    job_dict = scraper.get_position_details(position_link)
                    print(json.dumps(job_dict, indent=2, ensure_ascii=False))
                    all_jobs.append(job_dict)
                    
                    # Écrire progressivement dans le fichier
                    if not first_item:
                        f.write(",\n")
                    else:
                        first_item = False
                    
                    # Écrire l'objet JSON avec indentation
                    json_str = json.dumps(job_dict, indent=4, ensure_ascii=False)
                    # Ajouter l'indentation pour chaque ligne (sauf la première)
                    indented_lines = []
                    for line in json_str.split('\n'):
                        indented_lines.append("    " + line)
                    f.write('\n'.join(indented_lines))
                    f.flush()  # Forcer l'écriture immédiate
                    
                except Exception as e:
                    print(f"Erreur lors du scraping de {position_link}: {e}")
        
        f.write("\n]")  # Fin du tableau JSON
        f.flush()

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'nike_jobs.json'.")
"""

