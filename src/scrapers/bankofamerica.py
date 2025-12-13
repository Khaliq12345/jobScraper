from src.scrapers.base.base_scraper import BaseScraper
from selectolax.parser import HTMLParser
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import re


class BankOfAmerica(BaseScraper):
    def __init__(self) -> None:
        super().__init__(name="Bank of America", link="https://careers.bankofamerica.com/en-us/job-search", domain="https://careers.bankofamerica.com", companyid=16)


    def get_positions(self) -> list[str]:
        position_links = []
        offset = 0
        rows = 10
        while True:
            url = f"{self.link}?ref=search&start={offset}&rows={rows}&search=getAllJobs"
            html = self.get_html(url)
            soup = HTMLParser(html)

            tiles = soup.css("a.job-search-tile__url")
            if len(tiles) == 0:
                break

            for tile in tiles:
                href = tile.attributes.get("href")
                if not href:
                    continue
                position_link = urljoin(self.domain, href) if self.domain else href
                if position_link not in position_links:
                    position_links.append(position_link)

            offset += rows
        return position_links


    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)
        bs_soup = BeautifulSoup(html, 'html.parser')

        # Job ID (from meta job-path)
        jobid = None
        meta_job_path = soup.css_first('meta[name="job-path"]')
        if meta_job_path:
            content = meta_job_path.attributes.get('content', '')
            match = re.search(r'/job-detail/(\d+)', content)
            if match:
                jobid = int(match.group(1))

        # Title
        jobposition = soup.css_first('h1.job-description-body__title')
        jobposition = jobposition.text(strip=True) if jobposition else ""

        # Attributes on job container
        jd_container = soup.css_first('div.job-description-body')
        jobpattern = jd_container.attributes.get('data-jobTimeType', '') if jd_container else ''
        # Fallback: check sidebar for Full time / Part time
        if not jobpattern:
            sidebar = soup.css_first('div.job-description-sidebar')
            if sidebar:
                text = sidebar.text(strip=True).lower()
                if 'full time' in text or 'full-time' in text:
                    jobpattern = 'Full time'
                elif 'part time' in text or 'part-time' in text:
                    jobpattern = 'Part time'
        # Location - extraire depuis .js-primary-location
        jobaddress = ""
        jobcountry = ""
        location_elem = soup.css_first('span.js-primary-location')
        if location_elem:
            location_text = location_elem.text(strip=True)
            if location_text:
                # Séparer ville, état, pays
                parts = [p.strip() for p in location_text.split(',')]
                if len(parts) >= 2:
                    jobaddress = f"{parts[0]}, {parts[1]}"
                    # Si c'est un état américain, le pays est USA
                    us_states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 
                                'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 
                                'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 
                                'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 
                                'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 
                                'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 
                                'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 
                                'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 
                                'Washington', 'West Virginia', 'Wisconsin', 'Wyoming', 'District of Columbia']
                    if parts[1] in us_states:
                        jobcountry = "USA"
                    else:
                        jobcountry = parts[1]
                else:
                    jobaddress = location_text

        # Job description - inclure les responsibilities, s'arrêter avant "Required Qualifications"
        jobdescription = ""
        job_info_div = bs_soup.find('div', class_='job-description-body__internal')
        if job_info_div:
            desc_parts = []
            seen_texts = set()
            
            # Parcourir tous les enfants du div
            for child in job_info_div.children:
                if not hasattr(child, 'name'):
                    continue
                
                # Vérifier si on doit s'arrêter (avant "Required Qualifications")
                # Vérifier dans les <b> ou <strong> directement dans l'enfant
                if child.name in ('b', 'strong'):
                    text = child.get_text(strip=True).lower()
                    if 'required qualifications' in text:
                        break
                
                # Vérifier dans les paragraphes
                if child.name == 'p':
                    # Vérifier si ce paragraphe contient "Required Qualifications"
                    bold_in_p = child.find(['b', 'strong'])
                    if bold_in_p:
                        bold_text = bold_in_p.get_text(strip=True).lower()
                        if 'required qualifications' in bold_text:
                            break
                    
                    text = child.get_text(strip=True, separator=' ')
                    # Ignorer si c'est "Minimum Education Requirement" (sera dans jobexperience)
                    if 'minimum education requirement' in text.lower():
                        continue
                    if text and text not in seen_texts:
                        desc_parts.append(text)
                        seen_texts.add(text)
                
                # Extraire les listes (responsibilities)
                elif child.name in ('ul', 'ol'):
                    # Vérifier le sibling précédent pour "Required Qualifications"
                    prev_sibling = child.find_previous_sibling(['p', 'b', 'strong'])
                    if prev_sibling:
                        prev_text = prev_sibling.get_text(strip=True).lower()
                        if 'required qualifications' in prev_text:
                            break
                    
                    for li in child.find_all('li', recursive=False):
                        li_text = li.get_text(strip=True)
                        if li_text and li_text not in seen_texts:
                            desc_parts.append(f"• {li_text}")
                            seen_texts.add(li_text)
            
            jobdescription = '\n\n'.join(desc_parts).strip()

        # Extract Required Qualifications, Desired Qualifications, et Skills
        jobqualifications = ""
        jobexperience = ""
        skills = []
        
        # Utiliser BeautifulSoup pour mieux naviguer
        all_bold = bs_soup.find_all(['b', 'strong'])
        for bold in all_bold:
            bold_text = bold.get_text(strip=True).lower()
            
            # Required Qualifications
            if 'required qualifications' in bold_text:
                ul = bold.find_next('ul')
                if ul:
                    lis = [li.get_text(strip=True) for li in ul.find_all('li', recursive=False)]
                    if lis:
                        jobqualifications += 'Required Qualifications:\n' + '\n'.join(lis) + '\n\n'
            
            # Desired Qualifications
            elif 'desired qualifications' in bold_text:
                ul = bold.find_next('ul')
                if ul:
                    lis = [li.get_text(strip=True) for li in ul.find_all('li', recursive=False)]
                    if lis:
                        jobqualifications += 'Desired Qualifications:\n' + '\n'.join(lis) + '\n\n'
            
            # Skills
            elif bold_text.strip() == 'skills':
                ul = bold.find_next('ul')
                if ul:
                    skills = [li.get_text(strip=True) for li in ul.find_all('li', recursive=False)]
            
            # Minimum Education Requirement (pour jobexperience)
            elif 'minimum education requirement' in bold_text:
                # Le texte est dans le même paragraphe que le <b>
                parent_p = bold.find_parent('p')
                if parent_p:
                    # Prendre tout le texte du paragraphe et enlever "Minimum Education Requirement:"
                    full_text = parent_p.get_text(strip=True)
                    # Enlever le label "Minimum Education Requirement:"
                    if ':' in full_text:
                        jobexperience = full_text.split(':', 1)[1].strip()
                    else:
                        jobexperience = full_text

        # Ajouter Skills aux qualifications
        if skills:
            jobqualifications += 'Skills:\n' + '\n'.join(skills)

        job_dict = {
            'jobid': int(jobid) if jobid else int(datetime.now().timestamp()),
            'jobposition': jobposition,
            'jobdescription': jobdescription,
            'jobqualifications': jobqualifications,
            'jobexperience': jobexperience,
            'jobpattern': jobpattern,
            'jobcountry': jobcountry,
            'jobaddress': jobaddress,
            'scrapedsource': position_link
        }
        return job_dict




