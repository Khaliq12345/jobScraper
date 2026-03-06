"""
Scraper selection page - Choose between Generic and Workday scrapers
"""

from nicegui import ui
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware


class ScraperSelectionPage:
    """Main dashboard for selecting scraper type"""

    def __init__(self, db: Database, auth: AuthMiddleware):
        self.db = db
        self.auth = auth
        self._register_page()

    def _register_page(self):
        """Register the dashboard page route"""
        # Redirect to login if not authenticated
        if not self.auth.is_authenticated():
            ui.navigate.to("/login")
            return

    def main(self):
        """Render the scraper selection UI"""
        session_info = self.auth.get_session_info()
        username = session_info["username"]

        with ui.column().classes(
            "w-full min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-8"
        ):
            # Header with user info
            with ui.row().classes("w-full max-w-6xl justify-between items-center mb-8"):
                ui.label(f"👤 {username}").classes("text-lg font-semibold")

                def handle_logout():
                    self.auth.logout()
                    ui.notify("Logged out successfully", type="info")
                    ui.navigate.to("/")

                ui.button("Logout", on_click=handle_logout, icon="logout").props(
                    "flat color=negative"
                )

            # Main content card
            with ui.card().classes("w-full max-w-4xl p-12 shadow-2xl"):
                # Title
                ui.label("🚀 Welcome to Scraper Dashboard").classes(
                    "text-4xl font-bold text-center mb-4"
                )
                ui.label("Choose your scraper type to get started").classes(
                    "text-xl text-gray-600 dark:text-gray-400 text-center mb-12"
                )

                ui.separator().classes("mb-12")

                # Scraper options
                with ui.row().classes("w-full gap-8 justify-center items-stretch"):
                    # Generic Scraper Card
                    with ui.card().classes(
                        "flex-1 max-w-md p-8 hover:shadow-xl transition-shadow cursor-pointer border-2 border-transparent hover:border-blue-500"
                    ):
                        with ui.column().classes("w-full items-center gap-6"):
                            # Icon
                            ui.icon("language", size="64px").classes("text-blue-500")

                            # Title
                            ui.label("Generic Scraper").classes(
                                "text-2xl font-bold text-center"
                            )

                            # Button
                            ui.button(
                                "Select Generic Scraper",
                                on_click=lambda: ui.navigate.to("/generic-scraper"),
                                icon="arrow_forward",
                            ).props("size=lg color=blue").classes("w-full mt-6")

                # 1. Define your scrapers with unique metadata
                scrapers = [
                    {
                        "name": "Workday",
                        "icon": "business",
                        "color": "blue-600",
                        "path": "/workday-scraper",
                    },
                    {
                        "name": "Greenhouse",
                        "icon": "forest",
                        "color": "green-600",
                        "path": "/greenhouse-scraper",
                    },
                    {
                        "name": "Workable",
                        "icon": "work",
                        "color": "red-600",
                        "path": "/workable-scraper",
                    },
                    {
                        "name": "Lever",
                        "icon": "engineering",
                        "color": "yellow-600",
                        "path": "/lever-scraper",
                    },
                ]

                # 2. Use a responsive grid container (1 col on mobile, 2 on tablet, 3 on desktop)
                with ui.element("div").classes(
                    "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full p-4"
                ):
                    for scraper in scrapers:
                        # We use a wrapper div to handle the hover border without shifting the layout
                        with (
                            ui.card()
                            .classes(
                                "p-6 hover:shadow-2xl transition-all cursor-pointer border-t-4 ring-1 ring-gray-200"
                            )
                            .style(f"border-color: var(--tw-color-{scraper['color']});")
                        ):

                            with ui.column().classes(
                                "w-full items-center text-center gap-4"
                            ):
                                # Icon Background
                                with ui.element("div").classes(
                                    f"p-4 rounded-full bg-{scraper['color'].split('-')[0]}-50"
                                ):
                                    ui.icon(scraper["icon"], size="48px").classes(
                                        f"text-{scraper['color']}"
                                    )

                                # Title & Subtitle
                                with ui.column().classes("gap-0"):
                                    ui.label(scraper["name"]).classes(
                                        "text-xl font-black text-gray-800"
                                    )
                                    ui.label("Automated Scraper").classes(
                                        "text-xs uppercase tracking-widest text-gray-400"
                                    )

                                ui.separator().classes("my-2 opacity-50")

                                # Button - Clean and modern
                                ui.button(
                                    "Launch Scraper",
                                    on_click=lambda s=scraper: ui.navigate.to(
                                        s["path"]
                                    ),
                                    icon="rocket_launch",
                                ).props("flat color=primary").classes(
                                    "w-full font-bold"
                                )

    def _render_feature(self, text: str):
        """Render a feature item"""
        ui.label(text).classes("text-sm text-gray-700 dark:text-gray-300")

    def _render_stat(self, label: str, value: str, icon: str):
        """Render a stat card"""
        with ui.column().classes("items-center gap-2"):
            ui.icon(icon, size="32px").classes("text-gray-500")
            ui.label(value).classes("text-2xl font-bold")
            ui.label(label).classes("text-xs text-gray-500 uppercase")
