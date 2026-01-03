from datetime import datetime
import json
import re
from selectolax.parser import HTMLParser
from src.scrapers.base.base_scraper import BaseScraper


class Ecolab(BaseScraper):
    def __init__(self, save: bool) -> None:
        super().__init__(
            name="Ecolab",
            link="https://jobs.ecolab.com/global/en/search-results",
            domain="https://jobs.ecolab.com",
            companyid=15,
            save=save
        )

    def get_positions(self) -> list[str]:
        position_links = []

        page = 1
        max_pages = getattr(self, 'max_pages', None)
        
        while True:
            # Si on a une limite de pages, on s'arrête
            if max_pages and page > max_pages:
                break
            
            if page == 1:
                url = f"{self.link}"
            else:
                from_param = (page - 1) * 10
                url = f"{self.link}?from={from_param}&s=1"
            
            html = self.get_html(url)
            soup = HTMLParser(html)

            # Les jobs sont dans un script JavaScript avec phApp.ddo
            # On cherche le script qui contient les données JSON des jobs
            scripts = soup.css("script")
            jobs_found = False
            
            for script in scripts:
                script_text = script.text()
                if "eagerLoadRefineSearch" in script_text and '"jobs":[' in script_text:
                    try:
                        # On extrait le JSON depuis phApp.ddo
                        match = re.search(r'phApp\.ddo\s*=\s*({.*?});', script_text, re.DOTALL)
                        if match:
                            ddo_data = json.loads(match.group(1))
                            jobs_data = ddo_data.get("eagerLoadRefineSearch", {}).get("data", {}).get("jobs", [])
                            
                            if jobs_data:
                                jobs_found = True
                                
                                for job in jobs_data:
                                    job_seq_no = job.get("jobSeqNo", "")
                                    title = job.get("title", "")
                                    
                                    if job_seq_no:
                                        # On crée un slug depuis le titre pour l'URL
                                        title_slug = title.lower().replace(" ", "-").replace("/", "-")
                                        title_slug = re.sub(r'[^a-z0-9-]', '', title_slug)
                                        position_link = f"{self.domain}/global/en/job/{job_seq_no}/{title_slug}"
                                        position_links.append(position_link)
                    except (json.JSONDecodeError, KeyError):
                        continue

            # Si on ne trouve plus de jobs, on arrête
            if not jobs_found or len(position_links) == 0:
                break

            page += 1

        return position_links

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        # JSON-LD est un format de données structurées dans le HTML
        # C'est un script avec type="application/ld+json" qui contient les infos du job
        # en format JSON standardisé (schema.org). On le parse une seule fois pour tout extraire.
        json_ld_script = soup.css_first('script[type="application/ld+json"]')
        json_data = None
        if json_ld_script:
            try:
                json_data = json.loads(json_ld_script.text())
            except json.JSONDecodeError:
                pass

        # Titre du job - on essaie plusieurs endroits dans l'ordre
        jobposition = ""
        
        # D'abord on cherche dans le HTML directement
        h1_title = soup.css_first("h1.job-title")
        if h1_title:
            jobposition = h1_title.text(strip=True)
        
        # Sinon on regarde dans les meta tags (pour les réseaux sociaux)
        if not jobposition:
            og_title = soup.css_first('meta[property="og:title"]')
            if og_title:
                title_content = og_title.attributes.get("content", "")
                # Le format est souvent "Titre in Location | Category"
                if " in " in title_content:
                    jobposition = title_content.split(" in ")[0].strip()
                else:
                    jobposition = title_content.strip()
            else:
                twitter_title = soup.css_first('meta[name="twitter:title"]')
                if twitter_title:
                    title_content = twitter_title.attributes.get("content", "")
                    if " in " in title_content:
                        jobposition = title_content.split(" in ")[0].strip()
                    else:
                        jobposition = title_content.strip()
        
        # En dernier recours, on prend depuis le JSON-LD
        if not jobposition and json_data:
            jobposition = json_data.get("title", "")

        # Location 
        joblocation = ""
        
        if json_data:
            job_location = json_data.get("jobLocation", {})
            if job_location:
                address = job_location.get("address", {})
                # On récupère ville, région, pays et on les joint
                parts = []
                if address.get("addressLocality"):
                    parts.append(address.get("addressLocality"))
                if address.get("addressRegion"):
                    parts.append(address.get("addressRegion"))
                if address.get("addressCountry"):
                    parts.append(address.get("addressCountry"))
                if parts:
                    joblocation = ", ".join(parts)
        
        # Si pas trouvé, on essaie d'extraire depuis les meta tags
        if not joblocation:
            og_title = soup.css_first('meta[property="og:title"]')
            if og_title:
                title_content = og_title.attributes.get("content", "")
                if " in " in title_content:
                    location_part = title_content.split(" in ", 1)[1]
                    if " | " in location_part:
                        joblocation = location_part.split(" | ")[0].strip()
                    else:
                        joblocation = location_part.strip()
        
        # Description et qualifications
        jobdescription = ""
        jobqualifications = ""
        
        if json_data:
            description_html = json_data.get("description", "")
            if description_html:
                # La description est en HTML, on la parse pour extraire le texte
                desc_soup = HTMLParser(description_html)
                all_text = desc_soup.text(strip=True, separator="\n")
                # On enlève les balises HTML restantes
                jobdescription = re.sub(r'<[^>]+>', '', all_text)
                
                # On cherche les sections "Minimum Qualifications" et "Preferred Qualifications"
                min_match = re.search(r'Minimum Qualifications:(.*?)(?=Preferred Qualifications:|About|$)', all_text, re.DOTALL | re.IGNORECASE)
                pref_match = re.search(r'Preferred Qualifications:(.*?)(?=About|$)', all_text, re.DOTALL | re.IGNORECASE)
                
                quals_parts = []
                if min_match:
                    quals_parts.append("Minimum Qualifications:\n" + min_match.group(1).strip())
                if pref_match:
                    quals_parts.append("Preferred Qualifications:\n" + pref_match.group(1).strip())
                
                if quals_parts:
                    jobqualifications = "\n\n".join(quals_parts)
                    # Nettoyage final
                    jobqualifications = re.sub(r'<[^>]+>', '', jobqualifications)
                    jobqualifications = re.sub(r'([a-z])([A-Z])', r'\1\n\2', jobqualifications)
                    jobqualifications = re.sub(r'\n\s*\n+', '\n\n', jobqualifications).strip()

        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobqualifications": jobqualifications,
            "joblocation": joblocation,
            "scrapedsource": position_link
        }
        return job_dict



