from time import time_ns
from country_named_entity_recognition import find_countries
import requests
from selectolax.parser import HTMLParser
from src.scrapers.base.base_scraper import BaseScraper
from urllib.parse import urlparse


class Ashbyhq(BaseScraper):
    def __init__(
        self,
        save: bool,
        name: str,
        user_link: str,
        companyid: int,
        process_id: int = 0,
        is_test: bool = False,
    ) -> None:
        parsed_url = urlparse(user_link)
        splits = parsed_url.path.split("/")
        super().__init__(
            name=f"Ashbyhq-{splits[-1]}",
            link=f"https://jobs.ashbyhq.com/{splits[-1]}",
            domain="",
            base_link=user_link,
            companyid=companyid,
            save=save,
            is_test=is_test,
            process_id=process_id,
        )

    def get_positions(self) -> list[str]:
        all_jobs = []
        org_name = self.link.split("/")[-1]
        url = "https://jobs.ashbyhq.com/api/non-user-graphql"
        params = {"op": "ApiJobBoardWithTeams"}
        headers = {
            "content-type": "application/json",
            "apollographql-client-name": "frontend_non_user",
            "apollographql-client-version": "0.1.0",
        }
        json_data = {
            "operationName": "ApiJobBoardWithTeams",
            "variables": {
                "organizationHostedJobsPageName": org_name,
            },
            "query": (
                "query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {\n"
                "  jobBoard: jobBoardWithTeams(\n"
                "    organizationHostedJobsPageName: $organizationHostedJobsPageName\n"
                "  ) {\n"
                "    teams {\n      id\n      name\n      externalName\n      parentTeamId\n      __typename\n    }\n"
                "    jobPostings {\n"
                "      id\n      title\n      teamId\n      locationId\n      locationName\n"
                "      workplaceType\n      employmentType\n"
                "      secondaryLocations {\n        ...JobPostingSecondaryLocationParts\n        __typename\n      }\n"
                "      compensationTierSummary\n      __typename\n"
                "    }\n"
                "    __typename\n  }\n}\n\n"
                "fragment JobPostingSecondaryLocationParts on JobPostingSecondaryLocation {\n"
                "  locationId\n  locationName\n  __typename\n}"
            ),
        }
        print(f"LINK = {url}?op=ApiJobBoardWithTeams")
        response = requests.post(
            url, params=params, headers=headers, json=json_data, timeout=60
        )
        data = response.json()
        job_postings = data.get("data", {}).get("jobBoard", {}).get("jobPostings", [])
        for job in job_postings:
            job_id = job.get("id")
            if job_id:
                all_jobs.append(f"https://jobs.ashbyhq.com/{org_name}/{job_id}")
        print(f"FETCHED JOBS - {len(all_jobs)}")
        return all_jobs

    def get_position_details(self, job_link: str) -> dict | None:
        parts = job_link.rstrip("/").split("/")
        org_name = parts[-2]
        job_id = parts[-1]

        url = "https://jobs.ashbyhq.com/api/non-user-graphql"
        params = {"op": "ApiJobPosting"}
        headers = {
            "content-type": "application/json",
            "apollographql-client-name": "frontend_non_user",
            "apollographql-client-version": "0.1.0",
        }
        json_data = {
            "operationName": "ApiJobPosting",
            "variables": {
                "organizationHostedJobsPageName": org_name,
                "jobPostingId": job_id,
            },
            "query": (
                "query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) {\n"
                "  jobPosting(\n"
                "    organizationHostedJobsPageName: $organizationHostedJobsPageName\n"
                "    jobPostingId: $jobPostingId\n"
                "  ) {\n"
                "    id\n    title\n    departmentName\n    locationName\n    locationAddress\n"
                "    workplaceType\n    employmentType\n    descriptionHtml\n"
                "    secondaryLocationNames\n    compensationTierSummary\n"
                "    scrapeableCompensationSalarySummary\n"
                "    __typename\n  }\n}"
            ),
        }

        response = requests.post(
            url, params=params, headers=headers, json=json_data, timeout=60
        )
        data = response.json()
        job = data.get("data", {}).get("jobPosting")
        if not job:
            return None

        # Parse description HTML to plain text
        description_html = job.get("descriptionHtml") or ""
        jobdescription = (
            HTMLParser(description_html).text() if description_html else None
        )

        # Build location string from available fields
        location_parts = filter(
            None,
            [
                job.get("locationAddress"),
                job.get("locationName"),
            ],
        )
        jobaddress = ", ".join(location_parts)
        country = None
        country_finder = find_countries(jobaddress)
        if not country_finder:
            country = country if country else "United States"
        else:
            country = country_finder[0][0].name
            if country in jobaddress:
                country = country

        job_dict = {
            "jobid": time_ns(),
            "companyid": self.companyid,
            "jobposition": job.get("title"),
            "jobdescription": jobdescription,
            "jobcountry": country,
            "jobaddress": jobaddress,
            "jobpattern": job.get("employmentType"),
            "scrapedsource": job_link,
            "jobnice": job.get("departmentName"),
            "parse_location": True,
            "jobdate": "",  # not provided by API
            "jobsalary": job.get("scrapeableCompensationSalarySummary"),
        }
        return job_dict
