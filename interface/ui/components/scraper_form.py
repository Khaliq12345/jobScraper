"""
Scraper form component for starting new scrapers
"""

import json
import signal
import tempfile
import os
from time import sleep
from nicegui import ui, run
from urllib.parse import urlparse
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware
from interface.utils.start_scraper import start_custom_task


# ── Persistent session registry ──────────────────────────────────────────────
# Maps scraper name → {"progress": filepath, "stop": filepath}
# Lives in the module so it survives page reloads within the same server process.
_ACTIVE_SESSIONS: dict[str, dict] = {}


def _session_file(name: str) -> str:
    """Return a stable path for the session-state JSON for this scraper name."""
    return os.path.join(tempfile.gettempdir(), f"scraper_session_{name}.json")


def _save_session(name: str, progress_filepath: str, stop_filepath: str):
    data = {"progress": progress_filepath, "stop": stop_filepath}
    _ACTIVE_SESSIONS[name] = data
    with open(_session_file(name), "w") as f:
        json.dump(data, f)


def _load_session(name: str) -> dict | None:
    """Try memory first, then disk."""
    if name in _ACTIVE_SESSIONS:
        return _ACTIVE_SESSIONS[name]
    path = _session_file(name)
    try:
        with open(path) as f:
            data = json.load(f)
        _ACTIVE_SESSIONS[name] = data
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _clear_session(name: str):
    _ACTIVE_SESSIONS.pop(name, None)
    try:
        os.unlink(_session_file(name))
    except FileNotFoundError:
        pass


def _is_session_active(session: dict) -> bool:
    """Return True if the progress file exists and done != True."""
    try:
        with open(session["progress"]) as f:
            state = json.load(f)
        return not state.get("done", False)
    except (FileNotFoundError, json.JSONDecodeError):
        return False


# ── Shared helpers (same as before) ──────────────────────────────────────────


def _should_stop(stop_filepath: str) -> bool:
    try:
        with open(stop_filepath, "r") as f:
            data = json.load(f)
            print("SHOULD IT STOP - ", data)
            return data.get("stop", False)
    except (FileNotFoundError, json.JSONDecodeError):
        return False


def _write_progress(
    filepath: str, current: int, total: int, label: str, done: bool = False
):
    with open(filepath, "w") as f:
        json.dump({"current": current, "total": total, "label": label, "done": done}, f)


def start_all_scraper(name: str, progress_filepath: str, stop_filepath: str):
    db = Database()
    processes = db.get_all_process(name=name, all=True)
    total = len(processes)

    _write_progress(progress_filepath, 0, total, "Starting...")

    for index, process in enumerate(processes):
        if _should_stop(stop_filepath):
            _write_progress(
                progress_filepath, index, total, "Stopped by user", done=True
            )
            return

        label = f"Running {process.platform} ({index + 1}/{total})"
        _write_progress(progress_filepath, index, total, label)

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
                if _should_stop(stop_filepath):
                    _write_progress(
                        progress_filepath, index, total, "Stopping...", done=True
                    )
                    if process.process_id > 0:
                        try:
                            os.kill(process.process_id, signal.SIGKILL)
                        except ProcessLookupError:
                            print(f"Process {process.process_id} not found")
                        except Exception as e:
                            print(f"Error killing process: {e}")
                    db.update_process_status("stopped", process.platform)
                    return
                process_update = db.get_process(process.id)
                if process_update.status != "running":
                    break
                sleep(10)

    _write_progress(
        progress_filepath, total, total, "All scrapers completed!", done=True
    )


# ── Component ─────────────────────────────────────────────────────────────────


class ScraperForm:
    """Scraper form component"""

    def __init__(self, db: Database, auth: AuthMiddleware, name: str):
        self.db = db
        self.auth = auth
        self.name = name
        self.stop_filepath: str | None = None
        self._render()

    def _render(self):
        platform_link = (
            ui.input(label="Platform Link", placeholder="https://...")
            .classes("w-full")
            .props("outlined")
        )
        jobserver_id = (
            ui.input(label="Job Server ID", placeholder="Enter job server ID")
            .classes("w-full")
            .props("outlined")
        )
        save_to_db = ui.checkbox("Save to DB", value=True)
        is_test = ui.checkbox("Perform Test Run", value=False)
        message_container = ui.row().classes("w-full mt-4")

        # ── Progress UI ───────────────────────────────────────────────────────
        progress_section = ui.column().classes("w-full mt-4 gap-1")
        progress_section.set_visibility(False)

        with progress_section:
            progress_label = ui.label("").classes("text-sm text-gray-500")
            progress_bar = ui.linear_progress(value=0).props("color=primary rounded")

        # ── Restore progress if a run is still active after reload ────────────
        existing_session = _load_session(self.name)
        if existing_session and _is_session_active(existing_session):
            self.stop_filepath = existing_session["stop"]
            progress_section.set_visibility(True)
            progress_label.set_text("Reconnecting to running batch…")

            def _make_restore_poll(progress_filepath: str):
                def poll_progress():
                    try:
                        with open(progress_filepath) as f:
                            state = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        return

                    total = state.get("total", 1) or 1
                    current = state.get("current", 0)
                    label = state.get("label", "")
                    done = state.get("done", False)

                    progress_label.set_text(label)
                    progress_bar.set_value(current / total)

                    if done:
                        restore_timer.cancel()
                        _clear_session(self.name)
                        try:
                            os.unlink(progress_filepath)
                        except FileNotFoundError:
                            pass

                return poll_progress

            restore_timer = ui.timer(
                1.0, _make_restore_poll(existing_session["progress"])
            )

        # ── Handlers ──────────────────────────────────────────────────────────

        def start_scraper():
            message_container.clear()

            if not platform_link.value or not jobserver_id.value:
                ui.notify("Please fill in all required fields", type="negative")
                return

            try:
                job_id = int(jobserver_id.value)
            except ValueError:
                ui.notify("Job Server ID must be a number", type="negative")
                return

            try:
                parsed_url = urlparse(platform_link.value)
                username = parsed_url.path.replace("/", "")
                name = f"{self.name}-{username}"
            except Exception as e:
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
                    ui.notify(
                        "Failed to start scraper: Process ID is null", type="negative"
                    )
            except Exception as e:
                ui.notify(f"Error starting scraper: {str(e)}", type="negative")

        async def start_all_scraper_process():
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            progress_filepath = tmp.name
            tmp.close()

            tmp_stop = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            )
            self.stop_filepath = tmp_stop.name
            tmp_stop.close()

            with open(self.stop_filepath, "w") as f:
                json.dump({"stop": False}, f)

            # ✅ Persist so reloads can reconnect
            _save_session(self.name, progress_filepath, self.stop_filepath)

            progress_section.set_visibility(True)
            progress_bar.set_value(0)
            progress_label.set_text("Initializing...")

            def poll_progress():
                try:
                    with open(progress_filepath) as f:
                        state = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    return

                total = state.get("total", 1) or 1
                current = state.get("current", 0)
                label = state.get("label", "")
                done = state.get("done", False)

                progress_label.set_text(label)
                progress_bar.set_value(current / total)

                if done:
                    timer.cancel()
                    _clear_session(self.name)
                    try:
                        os.unlink(progress_filepath)
                    except FileNotFoundError:
                        pass

            timer = ui.timer(1.0, poll_progress)

            await run.cpu_bound(
                start_all_scraper, self.name, progress_filepath, self.stop_filepath
            )

        def stop_all_scrapers():
            if not getattr(self, "stop_filepath", None):
                # Try to recover stop file from session
                session = _load_session(self.name)
                if session:
                    self.stop_filepath = session["stop"]
                else:
                    return

            try:
                with open(self.stop_filepath, "w") as f:
                    json.dump({"stop": True}, f)
            except Exception as e:
                print("Stop failed:", e)

        with ui.element("div").classes("flex space-x-4"):
            ui.button("Start Scraper", on_click=start_scraper, icon="play_arrow").props(
                "color=primary"
            ).classes("mt-4")
            ui.button(
                "Start All Scrapers",
                on_click=start_all_scraper_process,
                icon="play_arrow",
            ).props("color=primary").classes("mt-4")
            ui.button("Stop (Batch Processing)", on_click=stop_all_scrapers).props(
                "color=primary"
            ).classes("mt-4")
