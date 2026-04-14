from datetime import datetime
from time import time_ns
import asyncio
import httpx
from selectolax.parser import HTMLParser
from src.scrapers.base.base_scraper import BaseScraper
from urllib.parse import urlparse
from src.storage.model import jobs

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0",
    "Accept": "application/json",
    "Accept-Language": "en-US",
    "Content-Type": "application/json",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=4",
}

MAX_CONCURRENT = 50


class Workday(BaseScraper):
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
        username = parsed_url.netloc.split(".")[0]
        domain = parsed_url.netloc
        path = parsed_url.path.split("/")[-1]
        super().__init__(
            name=f"Workday-{username}",
            link=f"https://{domain}/wday/cxs/{username}/{path}/jobs",
            domain=f"https://{domain}/wday/cxs/{username}/{path}",
            base_link=user_link,
            companyid=companyid,
            save=save,
            is_test=is_test,
            process_id=process_id,
        )

    def get_positions(self) -> list[str]:
        return asyncio.run(self._get_positions_async())

    async def _get_positions_async(self) -> list[str]:
        print(f"LINK = {self.link}")
        limit = 20
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        # Single shared client for all requests
        async with httpx.AsyncClient(headers=headers, timeout=60) as client:
            first_page = await self._fetch_page(client, offset=0, limit=limit)
            total = first_page["total"]
            postings = first_page["jobPostings"]
            print(f"TOTAL - {total}")

            jobs = self._extract_links(postings)

            if self.is_test or len(jobs) >= total:
                return jobs

            offsets = range(limit, total, limit)

            async def fetch_with_sem(offset):
                async with semaphore:
                    page = await self._fetch_page(client, offset=offset, limit=limit)
                    return self._extract_links(page["jobPostings"])

            results = await asyncio.gather(*[fetch_with_sem(o) for o in offsets])
            for links in results:
                jobs.extend(links)

        print(f"TOTAL FETCHED - {len(jobs)}")
        return jobs

    async def _fetch_page(
        self, client: httpx.AsyncClient, offset: int, limit: int
    ) -> dict:
        print(f"OFFSET - {offset} | LIMIT - {limit}")
        payload = {
            "appliedFacets": {},
            "limit": limit,
            "offset": offset,
            "searchText": "",
        }
        response = await client.post(self.link, json=payload)
        response.raise_for_status()
        return response.json()

    def _extract_links(self, postings: list) -> list[str]:
        links = []
        for job in postings:
            job_path = job.get("externalPath")
            if job_path:
                links.append(f"{self.domain}{job_path}")
        return links

    def get_position_details(self, link: str) -> dict | None:
        return asyncio.run(self._get_position_details_async_solo(link))

    async def _get_position_details_async_solo(self, link: str) -> dict | None:
        """Single-link fetch, creates its own client. Use get_all_details_async for bulk."""
        async with httpx.AsyncClient(headers=headers, timeout=10) as client:
            return await self._fetch_position_details(client, link)

    async def _fetch_position_details(
        self, client: httpx.AsyncClient, link: str
    ) -> dict | None:
        """Core fetch logic — reuses a shared client passed from outside."""
        response = await client.get(link)
        response.raise_for_status()
        json_data = response.json()

        job_info = json_data["jobPostingInfo"]
        try:
            country = job_info["country"]["descriptor"]
        except Exception:
            country = None

        return {
            "jobid": time_ns(),
            "companyid": self.companyid,
            "jobposition": job_info["title"],
            "jobdescription": HTMLParser(job_info["jobDescription"]).text(
                separator=" "
            ),
            "jobcountry": country,
            "jobaddress": job_info["location"],
            "jobpattern": job_info["timeType"],
            "scrapedsource": job_info["externalUrl"],
            "parse_location": True,
            "jobdate": job_info["postedOn"],
        }

    async def get_all_details_async(self, links: list[str]) -> list[dict]:
        """Bulk fetch with a single shared client and semaphore-controlled concurrency."""
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        # ✅ Client is created once and shared — connection pool is actually reused
        async with httpx.AsyncClient(headers=headers, timeout=10) as client:

            async def fetch_with_sem(link):
                async with semaphore:
                    return await self._fetch_position_details(client, link)

            results = await asyncio.gather(
                *[fetch_with_sem(link) for link in links],
                return_exceptions=True,
            )

        return [r for r in results if isinstance(r, dict)]

    async def main_async(self) -> None:
        print(self.name)
        self.link = self.clean_url(self.link)
        successful = 0
        failed = 0
        idx = 0
        status = "running"
        total = 0

        self._update_progress(
            {
                "site": self.name,
                "total": total,
                "current": 0,
                "successful": 0,
                "failed": 0,
                "status": status,
                "last_updated": datetime.now().isoformat(),
            }
        )

        try:
            positions = await self._get_positions_async()
            total = len(positions)
            self._update_progress(
                {
                    "site": self.name,
                    "total": total,
                    "current": 0,
                    "successful": 0,
                    "failed": 0,
                    "status": "running",
                    "last_updated": datetime.now().isoformat(),
                }
            )

            semaphore = asyncio.Semaphore(MAX_CONCURRENT)
            lock = asyncio.Lock()  # protect shared counters

            async def process_position(position):
                nonlocal successful, failed, idx
                async with semaphore:
                    try:
                        job_details = await self._get_position_details_async_solo(
                            position
                        )
                        parsed_position = self.validate_data(job_details)
                        if not parsed_position.jobposition:
                            return
                        if self.save:
                            job_data = parsed_position.model_dump(exclude={"jobid"})
                            self.send_job(jobs(**job_data))
                        async with lock:
                            successful += 1
                    except Exception as e:
                        print(f"ERROR - {str(e)}")
                        async with lock:
                            failed += 1
                    finally:
                        async with lock:
                            idx += 1
                            self._update_progress(
                                {
                                    "site": self.name,
                                    "total": total,
                                    "current": idx,
                                    "successful": successful,
                                    "failed": failed,
                                    "status": "running",
                                    "last_updated": datetime.now().isoformat(),
                                }
                            )

            await asyncio.gather(*[process_position(p) for p in positions])
            status = "completed"

        except KeyboardInterrupt:
            print("\n⚠️  Interrupted!")
            status = "interrupted"
            raise
        except Exception as e:
            print(f"\n❌ Fatal error: {str(e)}")
            status = "failed"
            raise
        finally:
            self._update_progress(
                {
                    "site": self.name,
                    "total": total,
                    "current": idx,
                    "successful": successful,
                    "failed": failed,
                    "status": status,
                    "last_updated": datetime.now().isoformat(),
                }
            )

    def main(self) -> None:
        asyncio.run(self.main_async())
