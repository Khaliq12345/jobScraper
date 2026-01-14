"""
Progress display component for showing scraper status
"""

from typing import Any
from nicegui import ui
import os
import signal
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware
from interface.utils.start_scraper import start_custom_task


class ProgressDisplay:
    """Progress display component"""

    def __init__(self, db: Database, auth: AuthMiddleware, name: str):
        self.db = db
        self.auth = auth
        self.status_filter = "all"
        self.search_query = ""
        self.container = None
        self.name = name
        self.page = 1
        self._render()

    def _render(self):
        """Render the progress display"""
        # Control buttons row
        with ui.row().classes("w-full gap-4 mb-4 items-center"):
            ui.button("Refresh", on_click=self._refresh, icon="refresh").props(
                "flat color=primary"
            )
        ui.separator()

        # Filter and search row
        with ui.row().classes("w-full gap-4 mb-4 items-center"):
            # Status filter
            ui.label("Filter by status:").classes("text-sm font-medium")
            all_progress = self.db.get_all_process(self.name, page=self.page)
            statuses = ["all"] + list(set(data.status for data in all_progress))
            status_select = (
                ui.select(
                    statuses,
                    value="all",
                    on_change=lambda e: self._filter_changed(e.value),
                )
                .props("outlined dense")
                .classes("w-40")
            )
            # Search by name
            ui.label("Search by name:").classes("text-sm font-medium ml-4")
            search_input = (
                ui.input(placeholder="Enter platform name or URL...")
                .props("outlined dense clearable")
                .classes("flex-1")
            )
            search_input.on_value_change(lambda e: self._search_changed(e.value))

        ui.separator()

        # Progress container
        self.container = ui.column().classes("w-full gap-4")

        # Pagination controls
        with ui.row().classes("w-full gap-4 mt-4 items-center justify-center"):
            ui.button(
                "Previous", on_click=self._previous_page, icon="chevron_left"
            ).props("flat color=primary").bind_enabled_from(
                self, "page", lambda p: p > 1
            )

            self.page_label = ui.label(f"Page {self.page}").classes(
                "text-sm font-medium mx-4"
            )

            ui.button("Next", on_click=self._next_page, icon="chevron_right").props(
                "flat color=primary"
            )

        self._update_display()

    def _filter_changed(self, new_filter: str):
        """Handle filter change"""
        self.page = 1
        self.status_filter = new_filter
        self._update_display()

    def _search_changed(self, search_value: str):
        """Handle search query change"""
        self.page = 1
        self.search_query = search_value.lower() if search_value else ""
        self._update_display()

    def _refresh(self):
        """Refresh the display"""
        self._update_display()
        ui.notify("Refreshed", type="info")

    def _update_display(self):
        """Update the progress display"""
        if not self.container:
            return
        self.container.clear()

        all_progress = self.db.get_all_process(
            name=self.name,
            page=self.page,
            filter={"search": self.search_query, "status": self.status_filter},
        )

        if not all_progress:
            with self.container:
                ui.label("No progress data available yet.").classes("text-gray-500")
            return

        # Show result count
        with self.container:
            ui.label(f"Showing {len(all_progress)} scrapers").classes(
                "text-sm text-gray-500 mb-2"
            )

        # Render each process card
        with self.container:
            for data in all_progress:
                self._render_process_card(data)

    def _render_process_card(self, data):
        """Render a single process card"""
        progress = data.current / data.total if data.total > 0 else 0
        badge_class = f"badge-{data.status}"

        with ui.card().classes("w-full p-4"):
            # Header
            with ui.row().classes("w-full items-center justify-between mb-4"):
                ui.label(f"📊 {data.platform}").classes("text-lg font-bold")
                ui.chip(data.status.upper(), icon="status")

            # Main metrics
            with ui.row().classes("w-full gap-8 mb-4"):
                with ui.column():
                    ui.label("Platform").classes("metric-label text-xs")
                    ui.label(str(data.platform)).classes(
                        "metric-value text-sm font-bold"
                    )

                with ui.column():
                    ui.label("ID").classes("metric-label text-xs")
                    ui.label(str(data.id)).classes("metric-value text-sm font-bold")

            with ui.row().classes("w-full mb-4"):
                with ui.column().classes("flex-1"):
                    ui.label("URL").classes("metric-label text-md")
                    ui.label(str(data.platform_url)).classes("text-lg break-all")

            # Expandable details
            with ui.expansion("View Details", icon="info", value=True).classes(
                "w-full"
            ):
                # Progress bar
                ui.linear_progress(progress).props("stripe").classes("mb-4")

                # Detailed metrics
                with ui.row().classes("w-full gap-8 mb-4"):
                    with ui.column():
                        ui.label("Progress").classes("metric-label text-xs")
                        ui.label(f"{data.current}/{data.total}").classes(
                            "metric-value text-sm"
                        )

                    with ui.column():
                        ui.label("Completion").classes("metric-label text-xs")
                        ui.label(f"{progress*100:.1f}%").classes("metric-value text-sm")

                    with ui.column():
                        ui.label("✅ Successful").classes("metric-label text-xs")
                        ui.label(str(data.successful)).classes("metric-value text-sm")

                    with ui.column():
                        ui.label("❌ Failed").classes("metric-label text-xs")
                        ui.label(str(data.failed)).classes("metric-value text-sm")

                ui.label(f"Last updated: {data.last_updated}").classes(
                    "caption text-xs"
                )
                ui.label(f"Process ID: {data.process_id}").classes("caption text-xs")

            # Action buttons
            with ui.row().classes("gap-2 mt-4"):
                if data.status == "running" and data.process_id > 0:
                    ui.button(
                        "Stop",
                        on_click=lambda d=data: self._stop_process(d),
                        icon="stop",
                    ).props("color=negative")

                ui.button(
                    "Delete",
                    on_click=lambda d=data: self._delete_process(d),
                    icon="delete",
                ).props("color=negative outline")
                ui.button(
                    "Refresh",
                    on_click=lambda d=data: self._refresh_process(d),
                    icon="refresh",
                ).props("color=success outline")

    def _stop_process(self, data):
        """Stop a running process"""
        try:
            if data.process_id > 0:
                try:
                    os.kill(data.process_id, signal.SIGKILL)
                except ProcessLookupError:
                    print(f"Process {data.process_id} not found")
                except Exception as e:
                    print(f"Error killing process: {e}")

                self.db.update_process_status("stopped", data.platform)
                ui.notify(f"Stopped {data.platform}", type="positive")
                self._update_display()
        except Exception as e:
            ui.notify(f"Error stopping process: {str(e)}", type="negative")

    def _delete_process(self, data):
        """Delete a process record"""
        try:
            self.db.delete_process(data.process_id)
            ui.notify(f"Deleted {data.platform}", type="positive")
            self._update_display()
        except Exception as e:
            ui.notify(f"Error deleting process: {str(e)}", type="negative")

    def _refresh_process(self, data):
        """Refresh a process record"""
        try:
            is_started = start_custom_task(
                self.db,
                jobserver_id=data.id,
                platform_link=data.platform_url,
                name=data.platform,
                save_to_db=True,
                is_test=False,
            )
            if is_started:
                ui.notify(f"Started {data.platform}", type="positive")
            else:
                ui.notify(f"Error Starting {data.platform}", type="negative")
            self._update_display()
        except Exception as e:
            ui.notify(f"Error Starting {data.platform} - {str(e)}", type="negative")

    def _previous_page(self):
        """Go to previous page"""
        if self.page > 1:
            self.page -= 1
            self.page_label.set_text(f"Page {self.page}")
            self._update_display()

    def _next_page(self):
        """Go to next page"""
        self.page += 1
        self.page_label.set_text(f"Page {self.page}")
        self._update_display()
