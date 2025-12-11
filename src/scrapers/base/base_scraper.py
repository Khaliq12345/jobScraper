import httpx
from selectolax.parser import HTMLParser


class BaseScraper:
    def __init__(self, name: str, link: str, positions_selector: str) -> None:
        self.name = name
        self.link = link
        self.positions_selector = positions_selector


    def get_html(self, url: str) -> str:
        """Extract the html from a url"""
        response = httpx.get(url)
        print(response)
        response.raise_for_status()
        return response.text

    def get_positions(self) -> list[str]:
        """Extract the position links"""
        position_links = []

        html = self.get_html(self.link)
        soup = HTMLParser(html)

        positions = soup.css(self.positions_selector)
        print(f"ALL JOBS - {len(positions)}")

        for position in positions:
            position_link = position.css_first("a")
            if not position_link:
                continue
            position_link = position_link.attributes.get("href")
            position_links.append(position_link)
        return position_links

    def get_position_details(self, position_link: str) -> dict:
        """Extract position details"""
        html = self.get_html(position_link)

        soup = HTMLParser(html)
        

        return {}



    def main(self) -> None:
        print(self.name)
        positions = self.get_positions()
        print(positions)

        
