from time import time
import json
import re

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Toyota(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Toyota",
            link="https://careers.toyota.com/us/en/search-results",
            domain="https://careers.toyota.com",
            companyid=44,
        )

    def get_positions(self) -> list[str]:
        position_links: list[str] = []
        from_param = 0
        page_size = 10

        while True:
            if from_param == 0:
                url = self.link
            else:
                url = f"{self.link}?from={from_param}&s=1"

            html = self.get_html(url)

            pattern = r'phApp\.ddo\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)

            if not match: break

            try:
                ddo_str = match.group(1)
                ddo = json.loads(ddo_str)
                eager_data = ddo.get("eagerLoadRefineSearch", {}).get("data", {})
                jobs_data = eager_data.get("jobs", [])

                if not jobs_data: break

                print(f"ALL JOBS - {len(jobs_data)}")

                for job in jobs_data:
                    job_id = job.get("jobId", "")
                    title = job.get("title", "")

                    if job_id and title:
                        title_slug = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-')
                        position_link = f"{self.domain}/us/en/job/{job_id}/{title_slug}"
                        if position_link not in position_links:
                            position_links.append(position_link)

                if len(jobs_data) < page_size: break

                from_param += page_size

            except json.JSONDecodeError:
                break

        return list(dict.fromkeys(position_links))

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        json_ld_script = soup.css_first('script[type="application/ld+json"]')
        json_data = None
        if json_ld_script:
            try:
                json_data = json.loads(json_ld_script.text())
            except json.JSONDecodeError:
                pass

        jobposition = json_data.get("title", "") if json_data else ""
        
        jobdescription = ""
        if json_data and "description" in json_data:
            desc_html = json_data["description"]
            if isinstance(desc_html, str):
                desc_soup = HTMLParser(desc_html)
                jobdescription = desc_soup.text(strip=True, separator="\n")
                jobdescription = re.sub(r'<[^>]+>', '', jobdescription)
                jobdescription = re.sub(r'\n\s*\n+', '\n\n', jobdescription).strip()

        jobcountry = ""
        jobaddress = ""
        if json_data and "jobLocation" in json_data:
            location = json_data["jobLocation"]
            if isinstance(location, dict) and "address" in location:
                address = location["address"]
                if isinstance(address, dict):
                    parts = []
                    if address.get("addressLocality"):
                        parts.append(address.get("addressLocality"))
                    if address.get("addressRegion"):
                        parts.append(address.get("addressRegion"))
                    if address.get("postalCode"):
                        parts.append(address.get("postalCode"))
                    if address.get("addressCountry"):
                        parts.append(address.get("addressCountry"))
                    combined = ", ".join(parts)
                    jobcountry = combined
                    jobaddress = combined

        jobniche = ""
        if json_data and "occupationalCategory" in json_data:
            jobniche = json_data["occupationalCategory"]

        jobpattern = ""
        if json_data and "employmentType" in json_data:
            emp_type = json_data["employmentType"]
            if isinstance(emp_type, list):
                emp_type = emp_type[0] if emp_type else ""
            if emp_type:
                jobpattern = emp_type.replace("_", " ").title()

        job_dict = {
            "jobid": int(time()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobniche": jobniche,
            "jobcountry": jobcountry,
            "jobaddress": jobaddress,
            "jobpattern": jobpattern,
            "scrapedsource": position_link,
            "parse_location": True
        }
        return job_dict

"""
if __name__ == "__main__":
    scraper = Toyota()
    positions = scraper.get_positions()
    print(f"\nNombre de positions trouvées: {len(positions)}")

    all_jobs: list[dict] = []
    if positions:
        for i, position_link in enumerate(positions, 1):
            print(f"\nScraping [{i}/{len(positions)}]: {position_link}")
            try:
                job_dict = scraper.get_position_details(position_link)
                print(json.dumps(job_dict, indent=2, ensure_ascii=False))
                all_jobs.append(job_dict)
            except Exception as e:
                print(f"Erreur lors du scraping de {position_link}: {e}")

    with open("toyota_jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=4, ensure_ascii=False)

    print(f"\nScraping terminé. {len(all_jobs)} offres sauvegardées dans 'toyota_jobs.json'.")
"""

