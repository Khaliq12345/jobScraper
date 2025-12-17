from src.scrapers.base.base_scraper import BaseScraper
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from datetime import datetime
import json
import re
import time
import random
import cloudscraper


class Coinbase(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Coinbase",
            link="https://www.coinbase.com/careers/positions",
            domain="https://www.coinbase.com",
            companyid=18
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
        """Extract the html from a url using cloudscraper.

        Pour les tests locaux, délais minimaux pour démarrer rapidement.
        """
        # Délai minimal pour les tests (0.1-0.5 secondes)
        delay = random.uniform(0.1, 0.5)
        time.sleep(delay)

        headers = {
            "Referer": "https://www.coinbase.com/careers/positions",
            "Sec-Fetch-Site": "same-origin",
        }
        response = self.scraper.get(url, headers=headers)

        # Gérer les erreurs 429
        if response.status_code == 429:
            print(f"⚠️ 429 détecté, attente de 5 secondes...")
            time.sleep(5)
            response = self.scraper.get(url, headers=headers)

        response.raise_for_status()
        return response.text

    def get_positions(self) -> list[str]:
        """Extract position links - optimisé avec regex directe sur le HTML brut"""
        position_links = []
        seen_ids = set()

        page = 1
        max_pages = getattr(self, 'max_pages', None)
        while True:
            if max_pages and page > max_pages:
                break
                
            url = f"{self.link}" if page == 1 else f"{self.link}?page={page}"
            print(f"📄 Récupération page {page}: {url}")
            
            try:
                html = self.get_html(url)
                print(f"✅ Page {page} récupérée ({len(html)} caractères)")
            except Exception as e:
                print(f"❌ Erreur page {page}: {e}")
                if "429" in str(e) or "Too Many Requests" in str(e):
                    break
                raise
            
            # Extraction directe avec regex sur le HTML brut (plus rapide)
            # Chercher les offerId dans le HTML
            offer_ids = re.findall(r'"offerId"\s*:\s*"?(\d+)"?', html)
            print(f"   → Trouvé {len(offer_ids)} offerId(s) dans le HTML")
            for offer_id in offer_ids:
                if offer_id not in seen_ids:
                    seen_ids.add(offer_id)
                    position_links.append(f"{self.domain}/careers/positions/{offer_id}")
            
            # Chercher aussi les liens directs dans le HTML
            href_matches = re.findall(r'href=["\']([^"\']*?/careers/positions/\d+[^"\']*)["\']', html)
            print(f"   → Trouvé {len(href_matches)} lien(s) direct(s)")
            for href in href_matches:
                position_link = urljoin(self.domain, href) if self.domain else href
                position_link = position_link.split("?")[0].split("#")[0]
                if position_link not in position_links:
                    position_links.append(position_link)

            print(f"   → Total positions trouvées: {len(position_links)}")

            # Si aucune position trouvée sur cette page, arrêter
            if not offer_ids and not href_matches:
                print(f"   → Aucune position trouvée, arrêt de la pagination")
                break

            page += 1

        result = list(dict.fromkeys(position_links))  # Dédupliquer en gardant l'ordre
        print(f"\n✅ Total final: {len(result)} positions uniques")
        return result

    def get_position_details(self, position_link: str) -> dict:
        """Extract job details - optimisé avec extraction directe du JSON-LD"""
        html = self.get_html(position_link)
        
        # Job ID depuis l'URL
        job_id = ""
        url_match = re.search(r'/positions/(\d+)/?', position_link)
        if url_match:
            job_id = url_match.group(1)

        # Extraire le JSON-LD directement avec regex 
        json_ld = None
        json_ld_match = re.search(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        if json_ld_match:
            try:
                json_ld = json.loads(json_ld_match.group(1))
            except json.JSONDecodeError:
                pass

        # Si pas de JSON-LD, utiliser HTMLParser en fallback
        if not json_ld:
            soup = HTMLParser(html)
            json_ld_script = soup.css_first('script[type="application/ld+json"]')
            if json_ld_script:
                try:
                    json_ld = json.loads(json_ld_script.text())
                except json.JSONDecodeError:
                    pass

        # Extraction des données depuis JSON-LD
        jobposition = json_ld.get("title", "") if json_ld else ""
        
        # Description : extraire et nettoyer le HTML
        jobdescription = ""
        if json_ld and "description" in json_ld:
            desc_html = json_ld["description"]
            if isinstance(desc_html, str):
                # Nettoyer le HTML rapidement avec regex 
                jobdescription = re.sub(r'<[^>]+>', '', desc_html)  # Enlever les tags HTML
                jobdescription = re.sub(r'&nbsp;', ' ', jobdescription)
                jobdescription = re.sub(r'&amp;', '&', jobdescription)
                jobdescription = re.sub(r'&lt;', '<', jobdescription)
                jobdescription = re.sub(r'&gt;', '>', jobdescription)
                jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        # Experience : mapping "x-y years" -> "y years"
        jobexperience = ""
        if jobdescription:
            text_lower = jobdescription.lower()
            range_match = re.search(r"(\d+)\s*-\s*(\d+)\s+years", text_lower)
            if range_match:
                jobexperience = f"{range_match.group(2)} years"

        # Job Pattern
        jobpattern = ""
        if jobdescription:
            desc_lower = jobdescription.lower()
            if "full-time" in desc_lower or "full time" in desc_lower:
                jobpattern = "Full time"
            elif "part-time" in desc_lower or "part time" in desc_lower:
                jobpattern = "Part time"

        # Job Salary - extraction rapide avec regex
        jobsalary = ""
        salary_match = re.search(r'<div[^>]*class=["\']pay-range["\'][^>]*>(.*?)</div>', html, re.DOTALL)
        if salary_match:
            salary_html = salary_match.group(1)
            amounts = re.findall(r'\$[\d,]+', salary_html)
            if len(amounts) >= 2:
                jobsalary = f"{amounts[0]} - {amounts[1]}"
            elif len(amounts) == 1:
                jobsalary = amounts[0]

        # Job Address et Country depuis JSON-LD
        jobaddress = ""
        jobcountry = ""
        if json_ld and "jobLocation" in json_ld:
            location = json_ld["jobLocation"]
            if isinstance(location, dict) and "address" in location:
                address = location["address"]
                if isinstance(address, str):
                    # Garder l'adresse complète dans jobaddress
                    jobaddress = address
                    
                    # Extraire le pays
                    if address.startswith("Remote") and " - " in address:
                        # Pour "Remote - USA" -> jobcountry = "USA"
                        jobcountry = address.split(" - ", 1)[1].strip()
                    elif "," in address:
                        # Pour les adresses avec virgules, prendre la dernière partie
                        # Mais attention : "Charlotte, NC" -> "NC" n'est pas un pays

                        parts = address.split(",")
                        if parts:
                            jobcountry = parts[-1].strip()

        jobniche = "Job"

 
        job_dict = {
            "jobid": int(job_id) if job_id and job_id.isdigit() else int(datetime.now().timestamp()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobexperience": jobexperience,
            "jobpattern": jobpattern,
            "jobniche": jobniche,
            "jobsalary": jobsalary,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link,
        }

        # Utiliser validate_data pour compléter les champs
        parsed = self.validate_data(job_dict)
        job_dict["jobqualifications"] = parsed.jobqualifications
        job_dict["jobexperience"] = parsed.jobexperience
        job_dict["jobpattern"] = parsed.jobpattern
        job_dict["jobsalary"] = parsed.jobsalary

        return job_dict

"""
if __name__ == "__main__":
    import json

    print("Démarrage du scraper Coinbase...")
    scraper = Coinbase()
    print(" Scraper initialisé")
    
    print("\n Recherche des positions...")
    positions = scraper.get_positions()
    print(f"\n Nombre de positions trouvées: {len(positions)}")

    output_path = "coinbase_jobs.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("[\n")
        first = True

        if positions:
            for i, position_link in enumerate(positions, 1):
                print(f"\nScraping [{i}/{len(positions)}]: {position_link}")
                try:
                    job_dict = scraper.get_position_details(position_link)
                    print(json.dumps(job_dict, indent=2, ensure_ascii=False))

                    if not first:
                        f.write(",\n")
                    f.write(json.dumps(job_dict, ensure_ascii=False, indent=2))
                    f.flush()
                    first = False
                except Exception as e:
                    print(f"Erreur lors du scraping de {position_link}: {e}")
                    continue

        f.write("\n]\n")
        f.flush()

    print("\nScraping terminé. Résultats écrits progressivement dans 'coinbase_jobs.json'.")
"""