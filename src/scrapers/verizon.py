from src.scrapers.base.base_scraper import BaseScraper
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from datetime import datetime
import re
import cloudscraper
from bs4 import BeautifulSoup


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

    def get_positions(self) -> list[str]:
        position_links = []

        page = 1
        while True:
            url = f"{self.link}" if page == 1 else f"{self.link}?page={page}#results"
            html = self.get_html(url)
            soup = HTMLParser(html)

            job_cards = soup.css("div.card.card-job")
            if len(job_cards) == 0:
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

            page += 1

        return position_links

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        
        soup = HTMLParser(html)

        job_id = ""
        job_id_elem = soup.css_first('p.job-meta')
        if job_id_elem:
            job_id_text = job_id_elem.text(strip=True)
            match = re.search(r'Job ID:\s*(R-?\d+)', job_id_text)
            if match:
                job_id = match.group(1).replace("R-", "")

        h1_title = soup.css_first("h1")
        jobposition = h1_title.text(strip=True) if h1_title else ""
        # if h1_title:
        #     jobposition = h1_title.text(strip=True)

        location_list = soup.css_first("ul.locations li")
        jobaddress = location_list.text(strip=True) if location_list else ""

        jobcountry = ""
        if jobaddress:
            parts = jobaddress.split(",")
            if len(parts) > 0:
                jobcountry = parts[-1].strip()

        jobdescription = ""
        jobqualifications = ""
        article = soup.css_first("article.cms-content")
        if article:
            article_html = str(article.html)
            bs_soup = BeautifulSoup(article_html, 'html.parser')
            
            doing_h3 = None
            qual_h3 = None
            for h3 in bs_soup.find_all('h3'):
                h3_text = h3.get_text(strip=True)
                if "you'll be doing" in h3_text.lower() or "you'll be doing" in h3_text.lower():
                    doing_h3 = h3
                if "looking for" in h3_text.lower():
                    qual_h3 = h3
                    if doing_h3:
                        break
            
            if qual_h3:
                qual_elements = []
                current = qual_h3.next_sibling
                while current:
                    if current.name == 'h3':
                        break
                    if hasattr(current, 'get_text'):
                        text = current.get_text(strip=True, separator=' ')
                        if text:
                            qual_elements.append(text)
                    current = current.next_sibling
                
                if qual_elements:
                    jobqualifications = "\n".join(qual_elements)
                    jobqualifications = re.sub(r'\n\s*\n+', '\n\n', jobqualifications).strip()
            
            if doing_h3 and qual_h3:
                desc_elements = []
                seen_texts = set()
                for sibling in doing_h3.find_next_siblings():
                    if sibling == qual_h3:
                        break
                    if hasattr(sibling, 'name') and sibling.name == 'h3':
                        break
                    if hasattr(sibling, 'get_text'):
                        text = sibling.get_text(strip=True, separator=' ')
                        if text and "When you join Verizon" not in text:
                            if text not in seen_texts:
                                desc_elements.append(text)
                                seen_texts.add(text)
                
                if desc_elements:
                    jobdescription = "\n".join(desc_elements)
                else:
                    article_text = article.text(strip=True, separator="\n")
                    parts = article_text.split("What we're looking for")
                    doing_parts = parts[0].split("What you'll be doing") if "What you'll be doing" in parts[0] else [parts[0]]
                    if len(doing_parts) > 1:
                        jobdescription = doing_parts[1].strip()
                    else:
                        jobdescription = doing_parts[0].strip()
            elif doing_h3:
                desc_elements = []
                seen_texts = set()
                for sibling in doing_h3.find_next_siblings():
                    if hasattr(sibling, 'name') and sibling.name == 'h3':
                        if "looking for" in sibling.get_text(strip=True).lower():
                            break
                        continue
                    if hasattr(sibling, 'get_text'):
                        text = sibling.get_text(strip=True, separator=' ')
                        if text and "When you join Verizon" not in text:
                            if text not in seen_texts:
                                desc_elements.append(text)
                                seen_texts.add(text)
                
                if desc_elements:
                    jobdescription = "\n".join(desc_elements)
                else:
                    article_text = article.text(strip=True, separator="\n")
                    parts = article_text.split("What we're looking for")
                    doing_parts = parts[0].split("What you'll be doing") if "What you'll be doing" in parts[0] else [parts[0]]
                    if len(doing_parts) > 1:
                        jobdescription = doing_parts[1].strip()
                    else:
                        jobdescription = doing_parts[0].strip()
            else:
                article_text = article.text(strip=True, separator="\n")
                parts = article_text.split("What we're looking for")
                doing_parts = parts[0].split("What you'll be doing") if "What you'll be doing" in parts[0] else [parts[0]]
                if len(doing_parts) > 1:
                    jobdescription = doing_parts[1].strip()
                else:
                    jobdescription = doing_parts[0].strip()
            
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()
            # Supprimer le texte constant "When you join Verizon..."
            jobdescription = re.sub(r'When you join Verizon.*?Join the #VTeamLife\.\s*', '', jobdescription, flags=re.DOTALL | re.IGNORECASE)
            jobdescription = re.sub(r'When you join Verizon.*?Want in\? Join the #VTeamLife\.\s*', '', jobdescription, flags=re.DOTALL | re.IGNORECASE)
            jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        jobniche = ""
        culture_embed = soup.css_first("div.culture-hq-embed")
        culture_embed = culture_embed.attributes.get("data-careerarea", "") if culture_embed else ""


        jobpattern = ""
        if article:
            article_text = article.text(strip=True, separator="\n")
            if "full-time" in article_text.lower() or "full time" in article_text.lower():
                jobpattern = "Full time"
            elif "part-time" in article_text.lower() or "part time" in article_text.lower():
                jobpattern = "Part time"

        job_dict = {
            "jobid": int(job_id) if job_id and job_id.isdigit() else int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobqualifications": jobqualifications,
            "jobniche": jobniche,
            "jobpattern": jobpattern,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "scrapedsource": position_link
        }
        return job_dict



