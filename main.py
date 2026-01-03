from argparse import ArgumentParser
from src.scrapers import new_dangote, google, ecolab, coinbase, cisco, capitec_bank,bankofamerica, att, apple, airbnb, adidas, workdayjobs

args = ArgumentParser()
args.add_argument('--save', choices=['yes', 'no'], default="no")
args.add_argument('--name', type=str, required=True)
args.add_argument('--id', type=int, required=True)
args.add_argument('--user_link', type=str)
parsed = args.parse_args()

if __name__ == "__main__":
    classes = {
        "Dangote": new_dangote.Dangote,
        "Google": google.Google,
        'Ecolab': ecolab.Ecolab,
        'Coinbase': coinbase.Coinbase,
        'Cisco': cisco.Cisco,
        'Capitech': capitec_bank.CapitecBank,
        'Bankofamerica': bankofamerica.BankOfAmerica,
        'Att': att.ATT,
        'Apple': apple.Apple,
        'Airbnb': airbnb.Airbnb,
        'Addidas': adidas.Adidas,
        'WorkdayJob': workdayjobs.Workday
    }

    # 2. Get the class from the dictionary using the string from arguments
    target_class = classes.get(parsed.name)

    if target_class:
        # 3. Initialize the class and call main
        if (parsed.name == 'WorkdayJob') and (parsed.user_link is None):
            print("Workday requires username")
        elif (parsed.name == 'WorkdayJob') and (parsed.user_link is not None):
            scraper = target_class(
                save=True if parsed.save == 'yes' else False, 
                companyid=parsed.id, 
                user_link=parsed.user_link,
                name=parsed.name,
            ) 
            scraper.main()
        else:
            scraper = target_class(save=True if parsed.save == 'yes' else False, companyid=parsed.id) 
            scraper.main()
    else:
        print(f"Error: No class found for {parsed.name}")
