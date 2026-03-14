from src.scrapers.smartrecruiters import Smartrecruiters
from src.scrapers.lever import Lever
from src.scrapers.greenhouse import GreenHouse
from src.scrapers.workdayjobs import Workday
from src.storage.database import Database
from multiprocessing import Process
import time
from src.storage.model import scraperStatus
from src.scrapers.wise import Wise
from src.scrapers.adidas import Adidas
from src.scrapers.airbnb import Airbnb
from src.scrapers.apple import Apple
from src.scrapers.att import ATT
from src.scrapers.bankofamerica import BankOfAmerica
from src.scrapers.capitec_bank import CapitecBank
from src.scrapers.cisco import Cisco
from src.scrapers.coinbase import Coinbase
from src.scrapers.ecolab import Ecolab
from src.scrapers.google import Google
from src.scrapers.new_capgemini import Capgemini
from src.scrapers.new_dangote import Dangote
from src.scrapers.new_huawei import HUAWEI
from src.scrapers.new_julius_berger import JB
from src.scrapers.new_sanofi import Sanofi
from src.scrapers.siemens import Siemens
from src.scrapers.sysco import Sysco
from src.scrapers.verizon import Verizon
from src.scrapers.workable import Workable
from src.scrapers.ashbyhq import Ashbyhq


def start_custom_task(
    db: Database,
    save_to_db: bool,
    jobserver_id: int,
    platform_link: str,
    name: str,
    is_test: bool,
) -> bool:
    # Start process
    print(save_to_db, jobserver_id, platform_link, name, is_test, False)
    p = Process(
        target=run_scraper_task,
        args=(save_to_db, jobserver_id, platform_link, name, is_test, False),
    )
    p.start()

    # Wait a bit for process to start
    time.sleep(2)

    # Update database with process info
    if p.pid:
        db.update_status(
            scraperStatus(
                id=jobserver_id,
                platform=name,
                platform_url=platform_link,
                status="running",
                process_id=p.pid,
            )
        )
        return True
    return False


def start_generic_scraper(
    db: Database,
    jobserver_id: int,
    is_test: bool,
    save_to_db: bool,
    name: str,
    platform_link: str,
):
    print("STARTING GENERIC SCRAPER")
    print(save_to_db, jobserver_id, platform_link, name, is_test, False)

    # Start process
    p = Process(
        target=run_scraper_task,
        args=(save_to_db, jobserver_id, platform_link, name, is_test, True),
    )
    p.start()

    # Wait a bit for process to start
    time.sleep(2)

    # Update database with process info
    if p.pid:
        db.update_status(
            scraperStatus(
                id=jobserver_id,
                platform=name,
                platform_url=platform_link,
                status="running",
                process_id=p.pid,
            )
        )
        return True
    return False


def run_scraper_task(
    save_to_db: bool,
    companyid: int,
    user_link: str,
    name: str,
    is_test: bool,
    is_generic: bool,
):
    if is_generic:
        scraper = None
        match name:
            case "Wise":
                scraper = Wise(save=save_to_db, process_id=0, is_test=is_test)
            case "Adidas":
                scraper = Adidas(save=save_to_db, process_id=0, is_test=is_test)
            case "Airbnb":
                scraper = Airbnb(save=save_to_db, process_id=0, is_test=is_test)
            case "Apple":
                scraper = Apple(save=save_to_db, process_id=0, is_test=is_test)
            case "ATT":
                scraper = ATT(save=save_to_db, process_id=0, is_test=is_test)
            case "Bank of America":
                scraper = BankOfAmerica(save=save_to_db, process_id=0, is_test=is_test)
            case "Capitec Bank":
                scraper = CapitecBank(save=save_to_db, process_id=0, is_test=is_test)
            case "Cisco":
                scraper = Cisco(save=save_to_db, process_id=0, is_test=is_test)
            case "Coinbase":
                scraper = Coinbase(save=save_to_db, process_id=0, is_test=is_test)
            case "Ecolab":
                scraper = Ecolab(save=save_to_db, process_id=0, is_test=is_test)
            case "Google":
                scraper = Google(save=save_to_db, process_id=0, is_test=is_test)
            case "Capgemini":
                scraper = Capgemini(save=save_to_db, process_id=0, is_test=is_test)
            case "Dangote":
                scraper = Dangote(save=save_to_db, process_id=0, is_test=is_test)
            case "Huawei":
                scraper = HUAWEI(save=save_to_db, process_id=0, is_test=is_test)
            case "Julius Berger":
                scraper = JB(save=save_to_db, process_id=0, is_test=is_test)
            case "Sanofi":
                scraper = Sanofi(save=save_to_db, process_id=0, is_test=is_test)
            case "Siemens":
                scraper = Siemens(save=save_to_db, process_id=0, is_test=is_test)
            case "Sysco":
                scraper = Sysco(save=save_to_db, process_id=0, is_test=is_test)
            case "Verizon":
                scraper = Verizon(save=save_to_db, process_id=0, is_test=is_test)

        if not scraper:
            return False

    else:
        if "Workday" in name:
            scraper = Workday(
                save=save_to_db,
                companyid=companyid,
                user_link=user_link,
                name=name,
                is_test=is_test,
                process_id=0,
            )
        elif "Greenhouse" in name:
            scraper = GreenHouse(
                save=save_to_db,
                companyid=companyid,
                user_link=user_link,
                name=name,
                is_test=is_test,
                process_id=0,
            )
        elif "Workable" in name:
            scraper = Workable(
                save=save_to_db,
                companyid=companyid,
                user_link=user_link,
                name=name,
                is_test=is_test,
                process_id=0,
            )
        elif "Lever" in name:
            scraper = Lever(
                save=save_to_db,
                companyid=companyid,
                user_link=user_link,
                name=name,
                is_test=is_test,
                process_id=0,
            )
        elif "Ashbyhq" in name:
            scraper = Ashbyhq(
                save=save_to_db,
                companyid=companyid,
                user_link=user_link,
                name=name,
                is_test=is_test,
                process_id=0,
            )
        elif "Smartrecruiters" in name:
            scraper = Smartrecruiters(
                save=save_to_db,
                companyid=companyid,
                user_link=user_link,
                name=name,
                is_test=is_test,
                process_id=0,
            )

    scraper.main()
