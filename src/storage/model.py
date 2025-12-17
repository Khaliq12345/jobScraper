from sqlmodel import Field, SQLModel


class jobs(SQLModel, table=True):
    jobid:  int = Field(primary_key=True)
    companyid: int 
    jobposition: str = ""
    jobdescription: str = ""
    jobqualifications: str = ""
    jobexperience: str = ""
    jobpattern: str = "" #job type
    jobsalary: str = ""
    jobniche: str = ""
    jobcountry: str = ""
    jobaddress: str = ""
    jobstatus: str = "scraped"
    scrapedsource: str
    editpin: str = "end"
    jobscraper: str = "Loicx"
