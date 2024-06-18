import requests
import json
from bs4 import BeautifulSoup
from moviedb.config import RATINGS_SOURCES, build_ratings
import re

class Scraper:

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }


    def __init__(self):
        self = self
        self.parsers = {
            "Letterboxd": self._parse_letterboxd,
            "Rotten Tomatoes": self._parse_rotten_tomatoes,
            "IMDB": self._parse_imdb,
            "Metacritic": self._parse_metacritic,
        }


    def _get_the_soup(self, url):
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        else: 
            return None


    def _parse_imdb(self, soup):
        data = soup.find('script', type="application/ld+json")
        if data:
            json_data = json.loads(data.get_text())
            rating = json_data.get("aggregateRating", {}).get("ratingValue")
            return [rating]
        return None


    def _parse_letterboxd(self, soup):
        data = soup.find('script', type="application/ld+json")
        if data:
            json_data = json.loads(data.get_text(strip=True).replace('/* <![CDATA[ */', '').replace('/* ]]> */', ''))
            rating = json_data.get("aggregateRating", {}).get("ratingValue")
            return [rating]
        return None


    def _parse_rotten_tomatoes(self, soup):
        data = soup.find('script', id="media-scorecard-json")
        if data:
            json_data = json.loads(data.get_text())
            tomatometer = json_data.get("criticsScore", {}).get('score')
            usermeter = json_data.get("audienceScore", {}).get('score')
            return [tomatometer, usermeter]
        return None


    def _parse_metacritic(self, soup):
        parent_div = soup.find('div', class_='c-siteReviewScore_background-critic_medium')
        if parent_div:
            score_span = parent_div.find('span', attrs={'data-v-4cdca868': ''})
            if score_span:
                score = score_span.text.strip()
                return [score]
        return None
            

    def get_ratings(self, site, url):
        soup = self._get_the_soup(url)
        if soup:
            parser = self.parsers.get(site)
            if parser:
                ratings = parser(soup)
                if ratings:
                    return build_ratings(site, ratings)
        return None

