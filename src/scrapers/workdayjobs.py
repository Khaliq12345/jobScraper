from time import sleep
import time
import requests
from selectolax.parser import HTMLParser
from src.scrapers.base.base_scraper import BaseScraper
from urllib.parse import urlparse

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
    'Accept': 'application/json',
    'Accept-Language': 'en-US',
    'Content-Type': 'application/json',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Priority': 'u=4',
}


class Workday(BaseScraper):
    def __init__(self, save: bool, name: str, user_link: str, companyid: int, process_id: int,  is_test: bool = False) -> None:
        parsed_url = urlparse(user_link)
        username = parsed_url.netloc.split(".")[0]
        domain = parsed_url.netloc
        path = parsed_url.path.split('/')[-1]
        super().__init__(
            name=f'Workday-{username}',
            link=f"https://{domain}/wday/cxs/{username}/{path}/jobs",
            domain=f"https://{domain}/wday/cxs/{username}/{path}",
            companyid=companyid,
            save=save,
            is_test=is_test,
            process_id=process_id,
        ) 

    def get_positions(self) -> list[str]:
        print(f'LINK = {self.link}')
        jobs = []
        offset = 0
        limit = 20
        total = 0
        
        while True:
            print(f"OFFSET - {offset} | LIMIT - {limit}")
            json_data = {
                'appliedFacets': {},
                'limit': limit,
                'offset': offset,
                'searchText': '',
            }
            response = requests.post(f"{self.link}", timeout=60, headers=headers, json=json_data)
            json_data = response.json()
            postings = json_data["jobPostings"]
            
            if total == 0:
                total = json_data["total"]
            
            print(f"FETCHED JOBS - {len(postings)} | TOTAL - {total}") 
            
            if not postings:
                break
            
            for job in postings:
                job_path = job['externalPath']
                job_link = f'{self.domain}{job_path}'
                jobs.append(job_link)
            
            # Check if we've collected all jobs
            if len(jobs) >= total:
                break

            if (self.is_test):
                break
                
            offset += limit
        
        return jobs

    def get_position_details(self, link: str) -> dict | None:
        sleep(0.5)
        response = requests.get(
            link,
            headers=headers,
        )
        json_data = response.json()
        job_info = json_data['jobPostingInfo']
        jobposition = job_info['title']
        jobdescription = HTMLParser(job_info['jobDescription']).text(separator=" ")
        jobpattern = job_info['timeType']
        country = job_info['country']['descriptor']
        joblink =job_info['externalUrl'] 
        jobaddress = job_info['location']

        job_dict = {
            "jobid": int(time.time()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": jobdescription,
            "jobcountry": country,
            "jobaddress": jobaddress,
            "jobpattern": jobpattern,
            "scrapedsource": joblink,
            "parse_location": True
        }
        return job_dict
