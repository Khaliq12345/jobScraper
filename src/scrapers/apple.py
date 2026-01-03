from datetime import datetime
import httpx
from src.scrapers.base.base_scraper import BaseScraper

cookies = {
    'jobs': '07158c1e454930789e2005e0f1ec2e71',
    's_fid': '3875E9C231083124-3F2B77FEFF6DFC36',
    's_vi': '[CS]v1|349E1ED06F2F00C8-4000056E399D7496[CE]',
    'aa_lastvisit': '1766570786800',
    's_getNewRepeat': '1766571047006-Repeat',
    's_vnum_n2_us': '1%7C1',
    'cs-id': '573f1c5b-5cc5-4509-b33c-385d03c51caa',
    'AWSALBAPP-0': 'AAAAAAAAAAD5dqOcO+CWjL6b/EkRuOfaibcKYjl4EUToZpjJUVPpFWzXV+EXyrKn4GnreYEzj+PPCI/j8s0LbrlncAl69rqICFIMMOkTtzWIsS1o+VdSVZDsGEQ+YpeqqrOcA7OU1xlYyPw=',
    'AWSALBAPP-1': '_remove_',
    'AWSALBAPP-2': '_remove_',
    'AWSALBAPP-3': '_remove_',
    'geo': 'BJ',
    'gpv': 'jobs%3Aen-us%3Asearch%3Asearch',
    's_sq': '%5B%5BB%5D%5D',
    's_cc': 'true',
    'jssid': 's%3A1_bszM3hg9fLXX4m33WcQP8MG32fn8ve.dJ3eckSv%2F6nDJPOAZ7lJ7KId0smHOLuXtYXb043PEIQ',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://jobs.apple.com/en-us/search',
    'locale': 'en_US',
    'browserLocale': 'en-us',
    'Content-Type': 'application/json',
    'X-Apple-CSRF-Token': '39aa703677ab37a774cb68736d3c2e157b03d49aa1a94b431ae98548697cf5a2',
    'x-b3-traceid': '3093577c-c1e1-433e-ab32-b5d719591474',
    'Origin': 'https://jobs.apple.com',
    'Connection': 'keep-alive', 
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Priority': 'u=4',
}

class Apple(BaseScraper):
    def __init__(self, save: bool) -> None:
        super().__init__(name = "Apple", link="https://jobs.apple.com/en-us/search", companyid=21, domain="https://jobs.apple.com", save=save)


    def get_positions(self) -> list[str]:
        position_links = []
        page = 1
        while True:
            print(f'Page - {page}')
            payload = {
                'query': '',
                'filters': {},
                'page': page,
                'locale': 'en-us',
                'sort': '',
                'format': {
                    'longDate': 'MMMM D, YYYY',
                    'mediumDate': 'MMM D, YYYY',
                },
            }

            response = httpx.post('https://jobs.apple.com/api/v1/search', cookies=cookies, headers=headers, json=payload)
            response.raise_for_status()
            json_data = response.json()

            job_data = json_data['res']
            jobs = job_data['searchResults']
            for job in jobs:
                position_links.append(f"https://jobs.apple.com/api/v1/jobDetails/{job['positionId']}?locale=en-us")

            if len(jobs) == 0:
                break

            page += 1
        return position_links



    def get_position_details(self, position_link: str) -> dict:
        response = httpx.get(position_link)
        response.raise_for_status()
        json_data = response.json()

        position_data = json_data['res']
        jobposition = position_data['postingTitle']
        category = position_data['teamNames'][0]
        location = position_data['locations'][0]
        job_address = f"{location.get('city', '')} {location.get('cityProvince', '')}".strip()
        country = location['countryName']
        job_description = f"{position_data['jobSummary']} {position_data['description']} {position_data['preferredQualifications']} {position_data['minimumQualifications']}"
        job_type = position_data['jobType']
        job_link = f"https://jobs.apple.com/en-us/details/{position_data['jobNumber']}/{position_data['transformedPostingTitle']}"

        job_dict = {
            "jobid": int(datetime.now().timestamp()),
            "companyid": self.companyid,
            "jobposition": jobposition,
            "jobdescription": job_description,
            "jobniche": category,
            "jobcountry": country,
            "jobaddress": job_address,
            "jobpattern": job_type,
            "scrapedsource": job_link,
        }
        return job_dict
