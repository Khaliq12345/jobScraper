import sys

sys.path.append(".")

from sqlmodel import Session, create_engine, delete, func, select
from src.storage.model import jobs, scraperStatus, Users
from config.config import DB_USER, DB_PASSWORD, DB_HOST, DB_DATABASE


class Database:
    def __init__(self) -> None:
        self.engine = create_engine(
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_DATABASE}"
        )
        # self.engine2 = create_engine("sqlite:///scraper.db")
        self.create_db_and_tables()

    def create_db_and_tables(self):
        jobs.metadata.create_all(self.engine)
        scraperStatus.metadata.create_all(self.engine)
        Users.metadata.create_all(self.engine)

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

    def delete_jobs_by_company(self, company_id: int) -> int:
        """Delete all jobs for a specific company. Returns count of deleted jobs."""
        with Session(bind=self.engine) as session:
            print("SEESION", session)
            stmt = delete(jobs).where(jobs.companyid == company_id)
            result = session.exec(stmt)
            session.commit()
            deleted_count = result.rowcount
            print(f"Deleted {deleted_count} jobs for company_id: {company_id}")
            return deleted_count

    # -----------------PROCESSES-------------------------------
    def update_status(self, info: scraperStatus) -> None:
        with Session(bind=self.engine) as session:
            stmt = select(scraperStatus).where(scraperStatus.id == info.id)
            status = session.exec(stmt).first()
            if status:
                # Update existing record
                status.total = info.total
                status.current = info.current
                status.successful = info.successful
                status.failed = info.failed
                status.status = info.status
                status.last_updated = info.last_updated
                status.platform_url = info.platform_url
                status.platform = info.platform
            else:
                # Create new record
                session.add(info)

            session.commit()

    def update_process_id(self, platform: str, process_id: int) -> None:
        print(f"Updating Process ID - {process_id}")
        with Session(bind=self.engine) as session:
            stmt = select(scraperStatus).where(scraperStatus.platform == platform)
            status = session.exec(stmt).first()
            if status:
                # Update only process_id
                status.process_id = process_id
                session.commit()
            else:
                # Optionally raise an exception or log if record doesn't exist
                raise ValueError(f"No record found for platform: {platform}")

    def get_all_process(
        self, name: str | None = None, page: int = 1, filter: dict = {}
    ) -> list[scraperStatus]:
        limit = 10
        offset = (page - 1) * limit
        search_name = filter.get("search")
        status = filter.get("status")
        with Session(bind=self.engine) as session:
            if name:
                stmt = select(scraperStatus).where(
                    scraperStatus.platform.startswith(name)
                )
            else:
                stmt = select(scraperStatus)
            if search_name:
                stmt = stmt.where(
                    func.lower(scraperStatus.platform).contains(search_name.lower())
                )
            if (status) and (status != "all"):
                stmt = stmt.where(scraperStatus.status == status)

            stmt = stmt.offset(offset).limit(limit)
            processes = session.exec(stmt).all()
            return list(processes)

    def get_process(self, companyid: int):
        with Session(bind=self.engine) as session:
            stmt = select(scraperStatus).where(scraperStatus.id == companyid)
            process = session.exec(stmt).first()
            return process

    def update_process_status(self, status: str, platform: str) -> None:
        with Session(bind=self.engine) as session:
            stmt = select(scraperStatus).where(scraperStatus.platform == platform)
            process = session.exec(stmt).first()
            if process:
                process.status = status
                session.commit()

    def delete_process(self, process_id: int) -> bool:
        """Delete a process record from the database"""
        with Session(bind=self.engine) as session:
            stmt = select(scraperStatus).where(scraperStatus.process_id == process_id)
            process = session.exec(stmt).first()
            if process:
                session.delete(process)
                session.commit()
                return True
            return False

    # ---------------------------USERS-------------------------------
    def create_user(self, username: str, password: str) -> None:
        with Session(bind=self.engine) as session:
            session.add(Users(username=username, password=password))
            session.commit()

    def get_user(self, username: str) -> None | Users:
        with Session(bind=self.engine) as session:
            stmt = select(Users).where(Users.username == username)
            return session.exec(stmt).first()

    def update_user(self, username: str, password: str) -> None | Users:
        with Session(bind=self.engine) as session:
            stmt = select(Users).where(Users.username == username)
            user = session.exec(stmt).first()
            if not user:
                return None
            user.password = password
            session.commit()
            session.refresh(user)  # Add this
            return user  # Add this


if __name__ == "__main__":
    db = Database()
    db.get_jobs()
