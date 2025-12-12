from sqlmodel import Session, create_engine, select
from src.storage.model import jobs, SQLModel


class Database:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///foo.db")


    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine) 

    def get_jobs(self) -> list[dict]:
        with Session(bind=self.engine) as session:
            stmt = select(jobs).limit(10)
            records = session.exec(stmt).all()
            print(records)

        return []

    def send_jobs(self, jobs: list[dict]):
        """Send all jobs to database"""
        with Session(bind=self.engine) as session:
            session.add_all(jobs)
            session.commit()


