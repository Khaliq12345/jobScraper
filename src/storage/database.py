import sys
sys.path.append('.')

from sqlmodel import Session, create_engine, select
from src.storage.model import jobs, SQLModel
from config.config import DB_USER, DB_PASSWORD, DB_HOST, DB_DATABASE


class Database:
    def __init__(self) -> None:
        self.engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_DATABASE}")


    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine) 

    def get_jobs(self) -> list[dict]:
        with Session(bind=self.engine) as session:
            stmt = select(jobs).limit(10)
            records = session.exec(stmt).all()
            print(records)

        return []

    def send_job(self, job: jobs):
        """Send all jobs to database"""
        with Session(bind=self.engine) as session:
            session.add(job)
            session.commit()
        print("JOB SENT")


if __name__ == "__main__":
    db = Database()
    db.get_jobs()


