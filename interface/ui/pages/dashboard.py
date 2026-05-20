"""
Dashboard page for the application
"""

from typing import Any
from nicegui import ui
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware
from interface.ui.components.sidebar import Sidebar
from interface.ui.components.scraper_form import ScraperForm
from interface.ui.components.progress_display import ProgressDisplay

scrapers = [
    {
        "name": "Workday",
        "icon": "business",
        "color": "#2563eb",
        "path": "/workday-scraper",
    },
    {
        "name": "Greenhouse",
        "icon": "forest",
        "color": "#16a34a",
        "path": "/greenhouse-scraper",
    },
    {
        "name": "Workable",
        "icon": "work",
        "color": "#dc2626",
        "path": "/workable-scraper",
    },
    {
        "name": "Lever",
        "icon": "engineering",
        "color": "#ca8a04",
        "path": "/lever-scraper",
    },
    {
        "name": "Ashbyhq",
        "icon": "person_search",
        "color": "#ea580c",
        "path": "/ashbyhq-scraper",
    },
    {
        "name": "Smartrecruiters",
        "icon": "manage_search",
        "color": "#9333ea",
        "path": "/smartrecruiters-scraper",
    },
]


class DashboardPage:
    """Dashboard page handler"""

    def __init__(self, db: Database, auth: AuthMiddleware, name: str):
        self.db = db
        self.auth = auth
        self._register_page()
        self.name = name

    def _register_page(self):
        """Register the dashboard page route"""
        # Redirect to login if not authenticated
        if not self.auth.is_authenticated():
            ui.navigate.to("/login")
            return

    def universal_header(self):
        with (
            ui.header(elevated=True)
            .classes("items-center justify-between px-4 py-0")
            .style(
                "background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); "
                "border-bottom: 1px solid rgba(255,255,255,0.08); "
                "min-height: 64px;"
            )
        ):
            # Left: Logo / App name
            with ui.row().classes("items-center gap-3"):
                ui.icon("travel_explore").style("color: #60a5fa; font-size: 28px;")
                ui.label("JobScraper").style(
                    "color: white; font-size: 1.25rem; font-weight: 700; "
                    'letter-spacing: 0.5px; font-family: "Segoe UI", sans-serif;'
                )
                ui.separator().props("vertical").style(
                    "height: 28px; background: rgba(255,255,255,0.15); margin: 0 8px;"
                )

            # Center: Scraper nav buttons
            with ui.row().classes("items-center gap-1"):
                for s in scrapers:
                    with (
                        ui.button(on_click=lambda path=s["path"]: ui.navigate.to(path))
                        .props("flat no-caps dense")
                        .style(
                            f"color: white; padding: 6px 10px; border-radius: 8px; "
                            f"font-size: 0.78rem; font-weight: 500; transition: background 0.2s;"
                        )
                        .classes("scraper-btn") as btn
                    ):
                        with ui.row().classes("items-center gap-1 no-wrap"):
                            ui.icon(s["icon"]).style(
                                f'color: {s["color"]}; font-size: 18px;'
                            )
                            ui.label(s["name"]).style("font-size: 0.78rem;")

    def main(self):
        """Render the dashboard UI"""
        self.universal_header()
        with ui.row().classes("w-full min-h-screen"):
            # Sidebar
            with ui.column().classes("w-64 bg-gray-100 dark:bg-gray-800 p-4"):
                Sidebar(self.db, self.auth)

            # Main content
            with ui.column().classes("flex-1 p-6"):
                ui.label(f"{self.name} Scraper 👋").classes("text-3xl font-bold mb-6")

                # Scraper form
                with ui.card().classes("w-full p-6 mb-6"):
                    ui.label("Start New Scraper").classes("text-xl font-bold mb-4")
                    ScraperForm(self.db, self.auth, self.name)

                # Progress display
                with ui.card().classes("w-full p-6"):
                    ui.label("Scraper Progress").classes("text-xl font-bold mb-4")
                    ProgressDisplay(self.db, self.auth, self.name)
