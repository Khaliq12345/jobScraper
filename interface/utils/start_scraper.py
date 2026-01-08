from src.scrapers.workdayjobs import Workday
from src.storage.database import Database
from multiprocessing import Process
import time
from src.storage.model import scraperStatus
from src.scrapers.wise import Wise

def run_scraper_task(save_to_db: bool, companyid: int, user_link: str, name: str, is_test: bool, is_generic: bool):
    if is_generic:
      scraper = None
      match name:
        case 'Wise':
          scraper = Wise(save=save_to_db, process_id=0, is_test=is_test)

      if not scraper:
        return False

    else:
      scraper = Workday(
          save=save_to_db,
          companyid=companyid,
          user_link=user_link,
          name=name,
          is_test=is_test,
          process_id=0
      )
    scraper.main()


def start_workday_task(db: Database, save_to_db: bool, jobserver_id: int, platform_link: str, name: str, is_test: bool) -> bool:
    # Delete existing jobs
    db.delete_jobs_by_company(jobserver_id)
    
    # Start process
    p = Process(target=run_scraper_task, args=(save_to_db, jobserver_id, platform_link, name, is_test, False))
    p.start()
    
    # Wait a bit for process to start
    time.sleep(2)
    
    # Update database with process info
    if p.pid:
        db.update_status(scraperStatus(
            id=jobserver_id,
            platform=name,
            platform_url=platform_link,
            status='running',
            process_id=p.pid
        ))
        return True
    return False


def start_generic_scraper(db: Database, jobserver_id: int, is_test:bool, save_to_db: bool, name: str, platform_link: str):
    print('STARTING GENERIC SCRAPER')
    # Delete existing jobs
    db.delete_jobs_by_company(jobserver_id)

    scraper = None
    match name:
      case 'Wise':
        scraper = Wise(save=save_to_db, process_id=0, is_test=is_test)

    if not scraper:
      return False
    # Start process
    p = Process(target=run_scraper_task, args=(save_to_db, jobserver_id, platform_link, name, is_test, True))
    p.start()
    
    # Wait a bit for process to start
    time.sleep(2)
    
    # Update database with process info
    if p.pid:
        db.update_status(scraperStatus(
            id=jobserver_id,
            platform=name,
            platform_url=platform_link,
            status='running',
            process_id=p.pid
        ))
        return True
    return False
