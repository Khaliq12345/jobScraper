from time import sleep, time

import requests

from src.scrapers.base.base_scraper import BaseScraper


class HUAWEI(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="HUAWEI",
            link="https://career.huawei.com/reccampportal/services/portal/portalpub/getJob/newHr/page/20/1?curPage=1&pageSize=20&jobFamilyCode=&deptCode=&keywords=&searchType=1&orderBy=P_COUNT_DESC&jobType=1",
            domain="https://career.huawei.com/",
            companyid=900,
        )

    def get_positions(self) -> list[str]:
        response = requests.get(self.link)
        json_data = response.json()
        jobs = json_data['result']
        print(f"ALL JOBS - {len(jobs)}")

        return jobs

    def get_position_details(self, position: dict) -> dict:
        sleep(2)

        jobposition = position["jobname"]
        country = position["jobArea"]
        location = country
        jobtype = position["jobType"]
        job_description = position["mainBusiness"]
        job_niche = position["deptName"]
        job_dict = {
            "jobid": int(time()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": job_description,
            "jobcountry": country,
            "jobaddress": location,
            "jobniche": job_niche,
            "jobpattern": jobtype,
            "scrapedsource": f"https://career.huawei.com/reccampportal/portal5/social-recruitment-detail.html?jobId={position['jobId']}&dataSource=1",
            "parse_location": True
        }
        return job_dict
