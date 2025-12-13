from urllib.parse import urljoin
from datetime import datetime
from selectolax.parser import HTMLParser
from src.scrapers.base.base_scraper import BaseScraper


class Google(BaseScraper):
    def __init__(self) -> None:
        super().__init__(name="Google", link="https://www.google.com/about/careers/applications/jobs/results/", domain="https://www.google.com", companyid=11)


    def get_positions(self) -> list[str]:
        position_links = []

        page = 1
        while True:
            print(f"Page ==> {page}")
            html = self.get_html(f"{self.link}?page={page}")
            soup = HTMLParser(html)

            base_tag = soup.css_first("base")
            base_href = base_tag.attributes.get("href") if base_tag else self.link

            cards = soup.css("li.lLd3Je")
            print(f"ALL JOBS - {len(cards)}")
            if len(cards) == 0:
                print("NO MORE NEW PAGE")
                break

            for card in cards:
                anchor = card.css_first('a[href*="jobs/results/"]')
                if not anchor:
                    continue
                href = anchor.attributes.get("href")
                if not href:
                    continue
                position_link = urljoin(base_href, href).split("?")[0]
                position_links.append(position_link)

            page += 1
        return position_links


    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        jobposition = soup.css_first("h2.p1N2lc")
        jobposition = jobposition.text(strip=True) if jobposition else ""

        # About the job
        about_el = soup.css_first("div.aG5W3")
        about_text = about_el.text(strip=True, separator=" ") if about_el else ""
        if about_text.startswith("About the job"):
            about_text = about_text.replace("About the job", "", 1).lstrip(" :\n\t")

        # Responsibilities
        responsibilities = []
        for h3 in soup.css("h3"):
            if h3.text(strip=True) == "Responsibilities":
                ul = h3.next
                while ul and getattr(ul, 'tag', None) != 'ul':
                    ul = getattr(ul, 'next', None)
                if ul:
                    responsibilities = [li.text(strip=True) for li in ul.css('li')]
                break
        responsibilities_text = "Responsibilities: " + "; ".join(responsibilities) if responsibilities else ""

        jobdescription = " ".join(filter(None, [about_text, responsibilities_text])).strip()

        # Qualifications
        quals = []
        for h3 in soup.css("h3"):
            title = h3.text(strip=True)
            if "qualifications" in title.lower():
                ul = h3.next
                while ul and getattr(ul, 'tag', None) != 'ul':
                    ul = getattr(ul, 'next', None)
                if ul:
                    quals.extend([li.text(strip=True) for li in ul.css('li')])
        jobqualifications = "\n".join(quals)

        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobqualifications": jobqualifications,
            "scrapedsource": position_link
        }
        return job_dict




