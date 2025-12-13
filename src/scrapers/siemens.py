from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from src.scrapers.base.base_scraper import BaseScraper


class Siemens(BaseScraper):
    def __init__(self) -> None:
        super().__init__(
            name="Siemens",
            link="https://jobs.siemens.com/fr_FR/externaljobs/SearchJobs",
            domain="https://jobs.siemens.com",
            companyid=10,
        )

    def get_positions(self) -> list[str]:
        position_links = []
        page = 0
        page_size = 6

        while True:
            offset = page * page_size
            url = f"{self.link}/?folderRecordsPerPage={page_size}&folderOffset={offset}&folderId="

            print(f"PAGE ==> {page} | OFFSET ==> {offset}")

            html = self.get_html(url)
            if not html:  # En cas d'erreur/timeout
                print("Erreur lors de la récupération de la page, arrêt.")
                break

            soup = HTMLParser(html)
            positions = soup.css("article.article--result")
            print(f"FOUND JOBS ==> {len(positions)}")

            if len(positions) == 0:
                print("NO MORE JOBS")
                break

            for position in positions:
                title_link = position.css_first("h3.title a.link")
                if not title_link:
                    button_link = position.css_first("a.button--primary")
                    if button_link:
                        href = button_link.attributes.get("href")
                    else:
                        continue
                else:
                    href = title_link.attributes.get("href")

                if href:
                    position_links.append(urljoin(self.domain, href))

            page += 1

            # Petite pause pour ne pas surcharger le serveur
            import time

            time.sleep(0.5)

        return position_links

    def get_position_details(self, position_link: str) -> dict:
        html = self.get_html(position_link)
        soup = HTMLParser(html)

        # Titre du poste
        jobposition = soup.css_first("h3.section__header__text__title")
        if not jobposition:
            jobposition = soup.css_first("h1.title--gradient")
        jobposition = jobposition.text(strip=True) if jobposition else ""

        # ID de l'offre
        job_id = position_link.split("/")[-1]  # Extraire l'ID depuis l'URL

        # Rechercher les informations dans les champs réguliers
        fields = soup.css(".article__content__view__field")

        # Initialiser les variables
        job_id_detail = ""
        published_date = ""
        organization = ""
        category = ""
        company = ""
        experience_level = ""
        job_type = ""
        work_mode = ""
        contract_type = ""
        locations = []

        for field in fields:
            label_element = field.css_first(".article__content__view__field__label")
            value_element = field.css_first(".article__content__view__field__value")

            if label_element and value_element:
                label = label_element.text(strip=True)
                value = value_element.text(strip=True)

                # Mapper les labels aux variables
                if "ID de l'offre" in label:
                    job_id_detail = value
                elif "Publié depuis" in label:
                    published_date = value
                elif "Organisation" in label:
                    organization = value
                elif "Domaine d'activité" in label:
                    category = value
                elif "Entreprise" in label:
                    company = value
                elif "Niveau d'expérience" in label:
                    experience_level = value
                elif "Type de poste" in label:
                    job_type = value
                elif "Modalités de travail" in label:
                    work_mode = value
                elif "Type de contrat" in label:
                    contract_type = value
                elif "Lieu" in label:
                    # Extraire les localisations
                    location_items = field.css(".list--locations .list__item")
                    locations = [item.text(strip=True) for item in location_items]

        # Description du poste
        description_field = soup.css_first(
            ".article__content__view__field.tf_replaceFieldVideoTokens"
        )
        job_description = ""

        if description_field:
            description_value = description_field.css_first(
                ".article__content__view__field__value"
            )
            if description_value:
                # Nettoyer le HTML de la description
                job_description = description_value.text(strip=True, separator="\n")

        # Pays/Ville/État (parsing depuis la localisation)
        country = ""
        city = ""
        state = ""

        if locations:
            # Prendre la première localisation
            location = locations[0]
            parts = [part.strip() for part in location.split("-")]

            if len(parts) >= 1:
                city = parts[0]
            if len(parts) >= 2:
                state = parts[1]
            if len(parts) >= 3:
                country = parts[2]

        job_dict = {
            "jobid": job_id_detail
            or job_id,  # Utiliser l'ID détaillé ou extrait de l'URL
            "jobposition": jobposition,
            "jobdescription": job_description,
            "jobsalary": "",  # Non disponible dans le HTML fourni
            "jobniche": category,
            "jobcountry": country,
            "jobcity": city,
            "jobstate": state,
            "joblocation": ", ".join(locations) if locations else "",
            "contracttype": contract_type,
            "workmode": work_mode,
            "jobtype": job_type,
            "experiencelevel": experience_level,
            "organization": organization,
            "company": company,
            "publisheddate": published_date,
            "scrapedsource": position_link,
            "companyid": self.companyid,
            "companyname": self.name,
        }
        return job_dict
