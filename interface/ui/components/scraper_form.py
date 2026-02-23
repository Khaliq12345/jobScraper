"""
Scraper form component for starting new scrapers
"""

from time import sleep
from nicegui import ui
from urllib.parse import urlparse
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware
from interface.utils.start_scraper import start_custom_task
from multiprocessing import Process


class ScraperForm:
    """Scraper form component"""

    def __init__(self, db: Database, auth: AuthMiddleware, name: str):
        self.db = db
        self.auth = auth
        self.name = name
        self._render()

    def _render(self):
        """Render the scraper form"""
        # Platform link input
        platform_link = (
            ui.input(label="Platform Link", placeholder="https://...")
            .classes("w-full")
            .props("outlined")
        )

        # Job server ID input
        jobserver_id = (
            ui.input(label="Job Server ID", placeholder="Enter job server ID")
            .classes("w-full")
            .props("outlined")
        )

        # Checkboxes
        save_to_db = ui.checkbox("Save to DB", value=True)
        is_test = ui.checkbox("Perform Test Run", value=False)

        # Error/message container
        message_container = ui.row().classes("w-full mt-4")

        def start_scraper():
            message_container.clear()

            # Validate inputs
            if not platform_link.value or not jobserver_id.value:
                with message_container:
                    ui.notify("Please fill in all required fields", type="negative")
                return

            try:
                job_id = int(jobserver_id.value)
            except ValueError:
                with message_container:
                    ui.notify("Job Server ID must be a number", type="negative")
                return

            # Parse platform name from URL
            try:
                parsed_url = urlparse(platform_link.value)
                username = parsed_url.path.replace("/", "")
                name = f"{self.name}-{username}"
            except Exception as e:
                with message_container:
                    ui.notify(f"Invalid URL: {str(e)}", type="negative")
                return

            # Start scraper in background process
            try:
                is_started = start_custom_task(
                    self.db,
                    save_to_db.value,
                    job_id,
                    platform_link.value,
                    name,
                    is_test.value,
                )
                if is_started:
                    with message_container:
                        ui.notify("Scraper started successfully!", type="positive")

                    # Clear form
                    platform_link.value = ""
                    jobserver_id.value = ""
                    save_to_db.value = False
                    is_test.value = False

                    # Refresh the page to show new scraper
                    ui.timer(
                        1.0,
                        lambda: ui.navigate.to(f"/{self.name.lower()}-scraper"),
                        once=True,
                    )
                else:
                    with message_container:
                        ui.notify(
                            "Failed to start scraper: Process ID is null",
                            type="negative",
                        )

            except Exception as e:
                with message_container:
                    ui.notify(f"Error starting scraper: {str(e)}", type="negative")

        def start_all_scraper_process(self):
            p = Process(target=self.start_all_scraper)
            p.start()
            p.join()

        def start_all_scraper():
            processes = self.db.get_all_process(name=self.name)
            for process in processes:
                print(process.id, process.platform_url, process.platform)
                is_started = start_custom_task(
                    self.db,
                    jobserver_id=process.id,
                    platform_link=process.platform_url,
                    name=process.platform,
                    save_to_db=True,
                    is_test=False,
                )
                if is_started:
                    while True:
                        process_update = self.db.get_process(process.id)
                        print(process_update)
                        if process_update.status != "running":
                            break
                        sleep(10)

        with ui.element("div").classes("flex space-x-4"):
            ui.button("Start Scraper", on_click=start_scraper, icon="play_arrow").props(
                "color=primary"
            ).classes("mt-4")
            ui.button(
                "Start All Scrapers",
                on_click=start_all_scraper_process,
                icon="play_arrow",
            ).props("color=primary").classes("mt-4")
