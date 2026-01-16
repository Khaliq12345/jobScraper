from datetime import datetime
from sqlmodel import Field, SQLModel


class jobs(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    jobid: int | None = Field(primary_key=True, default=None)
    # jobid:  int = Field(primary_key=True, default=None)
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
    jobdate: str | None = None


class scraperStatus(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: int = Field(primary_key=True)
    platform: str
    platform_url: str
    total: int = 0
    current: int = 0
    successful: int = 0
    failed: int = 0
    status: str = "running"
    last_updated: str = datetime.now().isoformat()
    process_id: int = 0

class Users(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: int = Field(default=None, primary_key=True)  # Auto-incrementing primary key
    username: str
    password: str
