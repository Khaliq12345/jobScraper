from src.scrapers.base.base_scraper import BaseScraper
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from datetime import datetime
import re
import cloudscraper
from src.utils import static


class Verizon(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Verizon",
            link="https://mycareer.verizon.com/jobs/",
            domain="https://mycareer.verizon.com",
            companyid=17
        )
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=10
        )

    def get_html(self, url: str) -> str:
        """Extract the html from a url using cloudscraper"""
        headers = {
            "Referer": "https://mycareer.verizon.com/jobs/",
            "Sec-Fetch-Site": "same-origin",
        }
        response = self.scraper.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def get_positions(self, limit: int = 50) -> list[str]:
        position_links = []
        page = 1
        max_pages = limit
        
        while page <= max_pages:
            url = f"{self.link}" if page == 1 else f"{self.link}?page={page}#results"
            print(f"Page ==> {page}", flush=True)
            try:
                html = self.get_html(url)
            except Exception as e:
                print(f"Error getting page {page}: {e} -> Stopping pagination.", flush=True)
                break
            soup = HTMLParser(html)

            job_cards = soup.css("div.card.card-job")
            if not job_cards:
                print("NO MORE NEW PAGE", flush=True)
                break

            for card in job_cards:
                job_link = card.css_first("a.stretched-link.js-view-job")
                if not job_link:
                    continue
                
                href = job_link.attributes.get("href", "")
                if href:
                    position_link = urljoin(self.domain, href) if self.domain else href
                    if position_link not in position_links:
                        position_links.append(position_link)

            if page >= max_pages:
                print(f"Reached limit of {max_pages} pages", flush=True)
                break
            page += 1

        return position_links

    def _text_to_digits(self, text: str) -> str:
        """
        Convertit les nombres écrits en lettres (one to ten, fifteen, twenty) en chiffres.
        """
        mapping = {
            "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
            "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
            "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
            "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18",
            "nineteen": "19", "twenty": "20"
        }
        # On remplace les mots par des chiffres (ex: "Three" -> "3")
        # Utilisation de \b pour les limites de mots afin d'éviter les remplacements partiels
        for word, digit in mapping.items():
            text = re.sub(r'\b' + word + r'\b', digit, text, flags=re.IGNORECASE)
        return text

    def _extract_experience(self, jobdescription: str) -> str:
        """
        Extrait le niveau d'expérience requis depuis la description du job.
        """
        if not jobdescription:
            return "No Experience"
        
        # Normalisation et conversion des nombres en lettres
        desc_normalized = self._normalize_text(jobdescription).lower()
        desc_normalized = self._text_to_digits(desc_normalized)
        
        # Vérification directe dans la liste statique
        for experience in static.experienceLevels:
            exp_normalized = self._normalize_text(experience).lower()
            if exp_normalized in desc_normalized:
                return experience
        
        # Extraction des années d'expérience via regex
        years_found = self._extract_years_from_text(desc_normalized)
        
        if years_found:
            # Filtrer les valeurs aberrantes et prendre le maximum
            valid_years = [y for y in years_found if 0 < y < 40]
            if not valid_years:
                return "No Experience"
            
            final_years = max(valid_years)
            return self._format_experience(final_years)
        
        # Fallback: mappings textuels pour les cas sans chiffres explicites
        return self._extract_experience_from_keywords(desc_normalized)
    
    def _extract_years_from_text(self, text: str) -> list[int]:
        """
        Extrait toutes les années d'expérience mentionnées dans le texte.
        """
        years_found = []
        
        # Pattern pour "X or more years"
        pattern_or_more = r"(\d+)\s+or\s+more\s+years?"
        for match in re.finditer(pattern_or_more, text):
            years_found.append(int(match.group(1)))
        
        # Pattern pour "X years", "X+ years", "X-Y years"
        pattern_standard = r"(\d+)(?:\s*[-–—]\s*(\d+))?(?:\+)?\s+years?"
        for match in re.finditer(pattern_standard, text):
            match_text = match.group(0)
            # Éviter les doublons avec "or more"
            if "or more" not in match_text:
                first_year = int(match.group(1))
                second_year = int(match.group(2)) if match.group(2) else None
                years_found.append(max(first_year, second_year) if second_year else first_year)
        
        return years_found
    
    def _format_experience(self, years: int) -> str:
        """
        Formate le nombre d'années en chaîne d'expérience standardisée.
        """
        if years >= 20:
            return "> 20 years"
        
        experience_str = f"{years} year" if years == 1 else f"{years} years"
        return experience_str
    
    def _extract_experience_from_keywords(self, text: str) -> str:
        """
        Extrait l'expérience à partir de mots-clés textuels (fallback).
        
        Args:
            text: Texte normalisé
            
        Returns:
            Niveau d'expérience ou "No Experience"
        """
        keyword_mappings = [
            ("entry level", "No Experience"),
            ("graduate", "No Experience"),
        ]
        
        for keyword, experience in keyword_mappings:
            if keyword in text:
                return experience
        
        return "No Experience"

    def _normalize_text(self, text: str) -> str:
        """Normalise les caractères typographiques (apostrophes, tirets)"""
        if not text:
            return ""
        return text.replace("'", "'").replace("'", "'").replace("–", "-").replace("—", "-").strip()

    def _extract_requirements_section(self, soup: HTMLParser) -> str:
        """
        Extrait intelligemment les listes situées après le titre "What we're looking for" avec selectolax
        """
        article = soup.css_first("article.cms-content")
        if not article: return ""

        requirements_text = []
        start_capturing = False
        
        # On itère sur tous les enfants de l'article pour garder l'ordre
        for node in article.iter(include_text=False):
            # Détection du point de départ
            if node.tag == 'h3':
                text = self._normalize_text(node.text(strip=True)).lower()
                if "what we're looking for" in text or "what we are looking for" in text:
                    start_capturing = True
                    continue
                
                # Arrêt si on trouve un titre de fin (sauf "even better" qui continue)
                # le titre (Even better if you have one or more of the following…)
                if start_capturing and "even better" not in text:
                    if "after you apply" in text or "where you'll be working" in text or "benefits" in text:
                        break
            
            # Capture des listes une fois le point de départ trouvé
            if start_capturing and node.tag == 'ul':
                for li in node.css('li'):
                    li_text = li.text(separator=' ', strip=True) 
                    if li_text:
                        requirements_text.append(li_text)

        return "\n".join(requirements_text)

    def _extract_qualifications(self, jobdescription: str) -> str:
        """
        Extrait les qualifications requises depuis la description du poste.
        
        Recherche d'abord directement dans static.qualifications, puis utilise des mappings
        personnalisés pour les valeurs qui ne sont pas dans la liste.
        """
        if not jobdescription:
            return "General"
        
        # 1. Normalisation importante (apostrophes courbes vs droites)
        desc_normalized = self._normalize_text(jobdescription).lower()
        
        # 2. Recherche d'abord dans static.qualifications
        for qualification in static.qualifications:
            qual_lower = self._normalize_text(qualification).lower()
            if qual_lower in desc_normalized:
                return qualification
            
            # Recherche flexible sur la partie principale
            main_part = qual_lower.split("(")[0].strip()
            # Nettoyage supplémentaire pour "Bachelor's" -> "bachelor
            main_keyword = main_part.replace("'s", "").replace("'s", "").strip()
            
            if len(main_keyword) > 3 and f" {main_keyword} " in f" {desc_normalized} ":
                return qualification
        
        # 3. Mappings personnalisés simplifiés (seulement High School, Associate, Bachelor)
        custom_mappings = [
            # High School variations
            ("high school diploma", "High School (S.S.C.E)"),
            ("high school diploma or ged", "High School (S.S.C.E)"),
            ("high school diploma or g.e.d", "High School (S.S.C.E)"),
            ("ged", "High School (S.S.C.E)"),
            ("g.e.d", "High School (S.S.C.E)"),
            ("secondary school", "High School (S.S.C.E)"),
            ("high school certificate", "High School (S.S.C.E)"),
            ("ssce", "High School (S.S.C.E)"),
            
            # Associate variations
            ("associate degree", "Associate"),
            ("associates degree", "Associate"),
            ("associate's", "Associate"),
            ("associate", "Associate"),
            
            # Bachelor variations
            ("bachelor's", "Bachelor's (B.A.)"), 
            ("bachelors", "Bachelor's (B.A.)"),
            ("bachelor's degree", "Bachelor's (B.A.)"),
            ("bachelor degree", "Bachelor's (B.A.)"),
            ("bachelor of arts", "Bachelor's (B.A.)"),
            ("bachelor of science", "Bachelor's (B.Sc.)"),
            ("bachelor of commerce", "Bachelor's (B.Com.)"),
            ("bachelor of engineering", "Bachelor's (B.Eng.)"),
            ("bachelor of education", "Bachelor's (B.Ed.)"),
            ("bachelor of laws", "Bachelor's (LLB)"),
        ]
        
        for keyword, qualification in custom_mappings:
            if keyword in desc_normalized:
                # Vérifier que la qualification existe dans static.qualifications
                if qualification in static.qualifications:
                    return qualification
        
        return "General"

    def get_position_details(self, position_link: str) -> dict:

        html = self.get_html(position_link)
        soup = HTMLParser(html)

        # Job ID
        job_id_elem = soup.css_first('p.job-meta')
        job_id_text = job_id_elem.text(strip=True) if job_id_elem else ""
        match = re.search(r'Job ID:\s*(R-?\d+)', job_id_text)
        job_id = match.group(1).replace("R-", "") if match else ""

        # Position
        h1_title = soup.css_first("h1")
        jobposition = h1_title.text(strip=True) if h1_title else ""

        # Address & Country
        location_elem = soup.css_first(".locations")
        location_text = location_elem.text(strip=True) if location_elem else ""
        jobaddress = location_text
        jobcountry = location_text

        # Description (using .cms-content as requested)
        article = soup.css_first("article.cms-content")
        jobdescription = article.text(strip=True, separator="\n") if article else ""
        
        # Clean up description
        if jobdescription:
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()
            # Remove constant footer text
            jobdescription = re.sub(r'When you join Verizon.*?Join the #VTeamLife\.\s*', '', jobdescription, flags=re.DOTALL | re.IGNORECASE)
            jobdescription = re.sub(r'When you join Verizon.*?Want in\? Join the #VTeamLife\.\s*', '', jobdescription, flags=re.DOTALL | re.IGNORECASE)
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        # Niche
        culture_embed = soup.css_first("div.culture-hq-embed")
        jobniche = culture_embed.attributes.get("data-careerarea", "") if culture_embed else ""

        # Pattern
        jobpattern = ""
        if "full-time" in jobdescription.lower() or "full time" in jobdescription.lower():
            jobpattern = "Full time"
        elif "part-time" in jobdescription.lower() or "part time" in jobdescription.lower():
            jobpattern = "Part time"

        # Extraire la section "What we're looking for" / "You'll need to have" pour une extraction plus précise
        requirements_section = self._extract_requirements_section(soup)
        
        # Extraction de l'expérience : d'abord depuis la section requirements, puis depuis toute la description
        jobexperience = self._extract_experience(requirements_section) if requirements_section else "No Experience"
        if jobexperience == "No Experience":
            jobexperience = self._extract_experience(jobdescription)
        
        # Extraction des qualifications : d'abord depuis la section requirements, puis depuis toute la description
        jobqualifications = self._extract_qualifications(requirements_section) if requirements_section else "General"
        if jobqualifications == "General":
            jobqualifications = self._extract_qualifications(jobdescription)

        job_dict = {
            "jobid": int(job_id) if job_id and job_id.isdigit() else int(datetime.now().timestamp()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobniche": jobniche,
            "jobpattern": jobpattern,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "jobexperience": jobexperience,
            "jobqualifications": jobqualifications,
            "scrapedsource": position_link,
            "parse_location": True
        }
        
        return job_dict


        
"""
if __name__ == "__main__":
    import json
    verizon = Verizon()
    positions = verizon.get_positions()
    print(f"\nNombre de positions trouvées: {len(positions)}", flush=True)

    all_jobs: list[dict] = []
    
    # Ouvrir le fichier en mode écriture pour écrire progressivement
    with open("verizon_results.json", "w", encoding="utf-8") as f:
        f.write("[\n")  # Début du tableau JSON
        first_item = True
        
        if positions:
            for i, position_link in enumerate(positions, 1):
                print(f"\nScraping [{i}/{len(positions)}]: {position_link}", flush=True)
                try:
                    job_dict = verizon.get_position_details(position_link)
                    validated_job = verizon.validate_data(job_dict)
                    job_dict_validated = validated_job.model_dump()
                    print(json.dumps(job_dict_validated, indent=2, ensure_ascii=False), flush=True)
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
                    print(f"Erreur lors du scraping de {position_link}: {e}", flush=True)
        
        f.write("\n]")  # Fin du tableau JSON
        f.flush()

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'verizon_results.json'.", flush=True)
 """       





