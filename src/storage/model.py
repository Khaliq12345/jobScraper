from sqlmodel import Field, SQLModel


class jobs(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
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


class scraperStatus(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: int = Field(default=None, primary_key=True)  # Auto-incrementing primary key
    platform: str
    total: int
    current: int
    successful: int
    failed: int
    status: str
    last_updated: str
    process_id: int = 0
