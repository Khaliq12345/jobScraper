from pydantic import BaseModel


class Scraper(BaseModel):
    jobid: int
    companyid: int
    jobposition: str = ""
    jobdescription: str = ""
    jobqualifications: str = ""
    jobexperience: str = ""
    jobpattern: str = ""
    jobsalary: str = ""
    jobniche: str = ""
    jobcountry: str = ""
    jobaddress: str = ""
    jobstatus: str = "scraped"
    scrapedsource: str
    editpin: str = "end"
    jobscraper: str = "Loicx"
