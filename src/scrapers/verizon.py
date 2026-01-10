from time import time_ns
from country_named_entity_recognition import find_countries
from src.scrapers.base.base_scraper import BaseScraper
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
import re
import cloudscraper
from src.utils import static


class Verizon(BaseScraper):
    def __init__(self, save: bool, process_id: int, is_test: bool) -> None:
        super().__init__(
            name="Verizon",
            link="https://mycareer.verizon.com/jobs/",
            domain="https://mycareer.verizon.com",
            companyid=31,
            save=save,
            process_id=process_id,
            is_test=is_test
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
        country_finder = find_countries(location_text)
        if not country_finder:
            jobcountry = "United States"
        if country_finder:
            country = country_finder[0][0].name
            if location_text.endswith(country):
                jobcountry = country

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
            "jobid": time_ns(),
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
