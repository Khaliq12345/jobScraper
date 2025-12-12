from sqlmodel import Field, SQLModel


class jobs(SQLModel, table=True):
    jobid:  int = Field(primary_key=True)
    jobposition: str = ""
    jobdescription: str = ""
    jobqualifications: str = ""
    jobexperience: str = ""
    jobpattern: str = ""
    jobsalary: str = ""
    jobniche: str = ""
    jobcountry: str = ""
    jobaddress: str = ""
    jobstatus: str =  ""
    scrapedsource: str = ""
    editpin: str = ""
    jobscraper: str = ""
