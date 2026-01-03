import sys
sys.path.append('.')

from sqlmodel import Session, create_engine, select
from src.storage.model import jobs, scraperStatus
from config.config import DB_USER, DB_PASSWORD, DB_HOST, DB_DATABASE


class Database:
    def __init__(self) -> None:
        self.engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_DATABASE}")
        self.engine2 = create_engine("sqlite:///scraper.db")
        self.create_db_and_tables()


    def create_db_and_tables(self):
        jobs.metadata.create_all(self.engine) 
        scraperStatus.metadata.create_all(self.engine2)

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

    # ------------------------------------------------
    def update_status(self, info: scraperStatus) -> None:
        with Session(bind=self.engine2) as session:
            stmt = select(scraperStatus).where(scraperStatus.platform == info.platform)
            status = session.exec(stmt).first()
            if status:
                # Update existing record
                status.total = info.total
                status.current = info.current
                status.successful = info.successful
                status.failed = info.failed
                status.status = info.status
                status.last_updated = info.last_updated
            else:
                # Create new record
                session.add(info)
            
            session.commit()

    def update_process_id(self, platform: str, process_id: int) -> None:
        print(f"Updating Process ID - {process_id}")
        with Session(bind=self.engine2) as session:
            stmt = select(scraperStatus).where(scraperStatus.platform == platform)
            status = session.exec(stmt).first()
            if status:
                # Update only process_id
                status.process_id = process_id
                session.commit()
            else:
                # Optionally raise an exception or log if record doesn't exist
                raise ValueError(f"No record found for platform: {platform}")

    def get_all_process(self) -> list[scraperStatus]:
        with Session(bind=self.engine2) as session:
            stmt = select(scraperStatus)
            processes = session.exec(stmt).all()
            return list(processes)

    def update_process_status(self, status: str, platform: str) -> None:        
        with Session(bind=self.engine2) as session:
            stmt = select(scraperStatus).where(scraperStatus.platform == platform)
            process = session.exec(stmt).first()
            if process:
                process.status = status
                session.commit()

            


if __name__ == "__main__":
    db = Database()
    db.get_jobs()


