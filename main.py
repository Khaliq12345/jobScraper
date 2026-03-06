from argparse import ArgumentParser
from src.scrapers import (
    new_dangote,
    google,
    ecolab,
    coinbase,
    cisco,
    capitec_bank,
    bankofamerica,
    att,
    apple,
    airbnb,
    adidas,
    workdayjobs,
    greenhouse,
    workable,
    smartrecruiters,
    lever,
)

args = ArgumentParser()
args.add_argument("--save", choices=["yes", "no"], default="no")
args.add_argument("--name", type=str, required=True)
args.add_argument("--id", type=int, required=True)
args.add_argument("--user_link", type=str)
parsed = args.parse_args()

if __name__ == "__main__":
    classes = {
        "Dangote": new_dangote.Dangote,
        "Google": google.Google,
        "Ecolab": ecolab.Ecolab,
        "Coinbase": coinbase.Coinbase,
        "Cisco": cisco.Cisco,
        "Capitech": capitec_bank.CapitecBank,
        "Bankofamerica": bankofamerica.BankOfAmerica,
        "Att": att.ATT,
        "Apple": apple.Apple,
        "Airbnb": airbnb.Airbnb,
        "Addidas": adidas.Adidas,
        "WorkdayJob": workdayjobs.Workday,
        "GreenHouse": greenhouse.GreenHouse,
        "Workable": workable.Workable,
        "Smartrecruiters": smartrecruiters.Smartrecruiters,
        "Lever": lever.Lever,
    }

    # 2. Get the class from the dictionary using the string from arguments
    target_class = classes.get(parsed.name)

    if target_class:
        # 3. Initialize the class and call main
        match parsed.name:
            case "WorkdayJob" | "GreenHouse" | "Workable" | "Smartrecruiters" | "Lever":
                if parsed.user_link is None:
                    print(
                        "Workday, GreenHouse, Smartrecruiters, Lever or Workable requires user_link"
                    )
                else:
                    scraper = target_class(
                        save=True if parsed.save == "yes" else False,
                        companyid=parsed.id,
                        user_link=parsed.user_link,
                        name=parsed.name,
                    )
                    scraper.main()
            case _:
                scraper = target_class(save=True if parsed.save == "yes" else False)
                scraper.main()
    else:
        print(f"Error: No class found for {parsed.name}")
