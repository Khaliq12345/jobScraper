"""
Scraper form component for starting new scrapers
"""

import json
import tempfile
import os
from time import sleep
from nicegui import ui, run
from urllib.parse import urlparse
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware
from interface.utils.start_scraper import start_custom_task


def _write_progress(
    filepath: str, current: int, total: int, label: str, done: bool = False
):
    """Write progress state to a temp file as JSON."""
    with open(filepath, "w") as f:
        json.dump({"current": current, "total": total, "label": label, "done": done}, f)


def start_all_scraper(name: str, progress_filepath: str):
    """
    Runs all scrapers sequentially, writing progress to a temp file
    so the UI process can poll it safely.
    """
    db = Database()
    processes = db.get_all_process(name=name, all=True)
    total = len(processes)

    _write_progress(progress_filepath, 0, total, "Starting...")

    for index, process in enumerate(processes):
        label = f"Running {process.platform} ({index + 1}/{total})"
        _write_progress(progress_filepath, index, total, label)

        print(process.id, process.platform_url, process.platform)
        is_started = start_custom_task(
            db,
            jobserver_id=process.id,
            platform_link=process.platform_url,
            name=process.platform,
            save_to_db=True,
            is_test=False,
        )

        if is_started:
            while True:
                process_update = db.get_process(process.id)
                print(process_update)
                if process_update.status != "running":
                    break
                sleep(10)

    _write_progress(
        progress_filepath, total, total, "All scrapers completed!", done=True
    )


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

        # --- Progress UI (hidden until "Start All" is running) ---
        progress_section = ui.column().classes("w-full mt-4 gap-1")
        progress_section.set_visibility(False)

        with progress_section:
            progress_label = ui.label("").classes("text-sm text-gray-500")
            progress_bar = ui.linear_progress(value=0).props("color=primary rounded")

        def start_scraper():
            message_container.clear()

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

            try:
                parsed_url = urlparse(platform_link.value)
                username = parsed_url.path.replace("/", "")
                name = f"{self.name}-{username}"
            except Exception as e:
                with message_container:
                    ui.notify(f"Invalid URL: {str(e)}", type="negative")
                return

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

                    platform_link.value = ""
                    jobserver_id.value = ""
                    save_to_db.value = False
                    is_test.value = False

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

        async def start_all_scraper_process():
            # Create a temp file to share progress between processes.
            # A plain filepath string is fully picklable — no Queue needed.
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            progress_filepath = tmp.name
            tmp.close()

            # Reset and show progress UI
            progress_section.set_visibility(True)
            progress_bar.set_value(0)
            progress_label.set_text("Initializing...")

            def poll_progress():
                try:
                    with open(progress_filepath, "r") as f:
                        state = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    return  # File not ready yet, try again next tick

                total = state.get("total", 1) or 1  # avoid division by zero
                current = state.get("current", 0)
                label = state.get("label", "")
                done = state.get("done", False)

                progress_label.set_text(label)
                progress_bar.set_value(current / total)

                if done:
                    timer.cancel()
                    os.unlink(progress_filepath)  # Clean up temp file

            timer = ui.timer(1.0, poll_progress)

            # Pass only the filepath (a plain string) — fully picklable
            await run.cpu_bound(start_all_scraper, self.name, progress_filepath)

        with ui.element("div").classes("flex space-x-4"):
            ui.button("Start Scraper", on_click=start_scraper, icon="play_arrow").props(
                "color=primary"
            ).classes("mt-4")
            ui.button(
                "Start All Scrapers",
                on_click=start_all_scraper_process,
                icon="play_arrow",
            ).props("color=primary").classes("mt-4")
