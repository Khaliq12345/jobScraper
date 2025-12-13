# main.py
from src.scrapers.airbnb import Airbnb


def test_single_job(url: str):
    """Fonction pour tester UN SEUL lien Airbnb et voir tous les détails extraits"""
    print("=" * 80)
    print("TEST D'UN JOB AIRBNB – Affichage complet")
    print("=" * 80)
    print(f"URL → {url}\n")

    # On crée une instance temporaire du scraper
    scraper = Airbnb()

    # On récupère les détails du job
    job_details = scraper.get_position_details(url)

    if not job_details or not job_details.get("jobposition"):
        print("Erreur : impossible de récupérer les détails du job")
        return

    # Affichage propre et complet
    print("RÉSULTAT FINAL (prêt à être inséré en base) :\n")
    print("-" * 80)
    print(f"{'Champ':<20} → {'Valeur'}")
    print("-" * 80)
    for key, value in job_details.items():
        if isinstance(value, str) and len(value) > 100:
            display_value = value[:97] + "..."
        else:
            display_value = value
        print(f"{key:<20} → {display_value}")
    print("-" * 80)


if __name__ == "__main__":
    # Change ce lien pour tester n'importe quelle offre Airbnb
    TEST_URL = "https://careers.airbnb.com/positions/7450054/"  # Salaire + Remote
    # TEST_URL = "https://careers.airbnb.com/positions/7340027/"   # Paris (France)
    # TEST_URL = "https://careers.airbnb.com/positions/7341683/"   # Mexico City
    # TEST_URL = "https://careers.airbnb.com/positions/7288960/"   # Canada (French Speaking)

    test_single_job(TEST_URL)
