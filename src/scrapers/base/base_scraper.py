from abc import abstractmethod
import httpx
from src.storage.database import Database
from src.storage.model import jobs, scraperStatus
from src.utils import static
import re
from datetime import datetime


class BaseScraper(Database):
    def __init__(self, save: bool, name: str, link: str, process_id: int, companyid: int, domain: str = "", is_test: bool = False) -> None:
        super().__init__()
        self.name = name
        self.link = link
        self.domain = domain
        self.companyid = companyid
        self.save = save
        self.is_test = is_test
        self.process_id = process_id
        self.create_db_and_tables()


    @staticmethod
    def get_html(url: str) -> str:
        """Extract the html from a url"""
        response = httpx.get(url)
        print(response)
        print(response.url)
        response.raise_for_status()
        return response.text


    def validate_data(self, job_details: dict):
        """Validate Scraped job info"""
        scraped_job = jobs(**job_details)

        # Job qualification
        if not scraped_job.jobqualifications:
            scraped_job.jobqualifications = self._extract_qualifications(scraped_job.jobdescription)


        # Job exprience
        if not scraped_job.jobexperience:
            scraped_job.jobexperience = "General"
            years = self._extract_years_from_text(scraped_job.jobdescription)
            if years:
                if years[0] > 20:
                    scraped_job.jobexperience = "Highly Experienced"
                else:
                    scraped_job.jobexperience = f"{years[0]}-years"

                    
        # Job pattern
        if not scraped_job.jobpattern:
            for pattern in static.workPatterns:
                if pattern.lower() in scraped_job.jobpattern:
                    scraped_job.jobpattern = pattern.replace(' ', '-')

                else:
                    scraped_job.jobpattern = "full-time"

        if (not scraped_job.jobcountry) and (scraped_job.jobaddress):
            scraped_job.jobcountry = "Same As Address"
        if (not scraped_job.jobaddress) and (scraped_job.jobcountry):
            scraped_job.jobaddress = "Same As Country"
        if (not scraped_job.jobcountry) and (not scraped_job.jobaddress):
            scraped_job.jobcountry = "Worldwide"
            scraped_job.jobaddress = "Same As Country"

        if not scraped_job.jobniche:
            jobniches = scraped_job.jobposition.split(',')
            scraped_job.jobniche = ', '.join(jobniches[1:]).strip() if jobniches else ""
            if not scraped_job.jobniche:
                scraped_job.jobniche = "Job"

        # Job salary
        if not scraped_job.jobsalary:
            scraped_job.jobsalary = static.jobSalary_default
        

        scraped_job.jobsalary = scraped_job.jobsalary.replace("Salary:", "")

        return scraped_job

    def _normalize_text(self, text: str) -> str:
        """Normalise les caractères typographiques (apostrophes, tirets)"""
        if not text:
            return ""
        return text.replace("'", "'").replace("'", "'").replace("–", "-").replace("—", "-").strip()


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
            ("bachelor of laws", "Bachelor's (LLB)"),
        ]
        
        for keyword, qualification in custom_mappings:
            if keyword in desc_normalized:
                # Vérifier que la qualification existe dans static.qualifications
                if qualification in static.qualifications:
                    return qualification
        
        return "General"
        
    

    @abstractmethod
    def get_positions(self) -> list[str]:
        """Extract the position links"""
        pass

    @abstractmethod
    def get_position_details(self, position_link: str) -> dict:
        """Extract position details"""
        print(f"POSITION - {position_link}")
        pass


    def main(self) -> None:
        print(self.name) 
        successful = 0
        failed = 0
        idx = 0
        status = "running"
        total = 0

        self._update_progress({
            "site": self.name,
            "total": total,
            "current": 0,
            "successful": 0,
            "failed": 0,
            "status": status,
            "last_updated": datetime.now().isoformat()
        }) 
        
        try:
            positions = self.get_positions()
            total = len(positions)  
            self._update_progress({
                "site": self.name,
                "total": total,
                "current": 0,
                "successful": 0,
                "failed": 0,
                "status": "running",
                "last_updated": datetime.now().isoformat()
            })
            
            for idx, position in enumerate(positions, 1):
                try:
                    job_details = self.get_position_details(position)
                    parsed_position = self.validate_data(job_details)
                    print(parsed_position)
                    
                    if not parsed_position.jobposition:
                        continue
                        
                    if self.save:
                        self.send_job(parsed_position)
                    
                    successful += 1
                    
                except Exception as e:
                    print(f"ERROR - {str(e)}")
                    failed += 1
                
                self._update_progress({
                    "site": self.name,
                    "total": total,
                    "current": idx,
                    "successful": successful,
                    "failed": failed,
                    "status": "running",
                    "last_updated": datetime.now().isoformat()
                })
            
            status = "completed"
            
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted!")
            status = "interrupted"
            raise
            
        except Exception as e:
            print(f"\n❌ Fatal error: {str(e)}")
            status = "failed"
            raise
            
        finally:
            # ALWAYS saves progress, even if something crashes
            self._update_progress({
                "site": self.name,
                "total": total,
                "current": idx,
                "successful": successful,
                "failed": failed,
                "status": status,
                "last_updated": datetime.now().isoformat()
            })  

    def _update_progress(self, data: dict) -> None:
        """Update progress in database with current site's data"""
        
        data['platform'] = self.name  # Use platform instead of site
        
        # Create scraperStatus object
        status_info = scraperStatus(
            platform=data['platform'],
            total=data['total'],
            current=data['current'],
            successful=data['successful'],
            failed=data['failed'],
            status=data['status'],
            last_updated=data['last_updated'],
        )
        
        # Update or insert in database
        self.update_status(status_info)

