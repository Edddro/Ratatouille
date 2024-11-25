# -*- coding: utf-8 -*-

import requests
import random
import lxml
import cchardet
from bs4 import BeautifulSoup


class AllRecipes:
    BASE_URL = "https://allrecipes.com/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'Cookie': 'euConsent=true',
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"}

    def _fetch_page(self, url, params=None):
        response = self.session.get(url, params=params)
        return BeautifulSoup(response.text, 'lxml')

    def _parse_article(self, article):
        data = {}
        try:
            data["name"] = article.find(
                "span", {
                    "class": "card__title"}).get_text(
                strip=True)
            if len(data["name"]) > 80:
                data["name"] = data["name"][:80] + "..."
            data["url"] = article['href']
            data["rate"] = len(article.find_all("svg", {"class": "icon-star"}))
            if article.find_all("svg", {"class": "icon-star-half"}):
                data["rate"] += 0.5
            data["image"] = article.find('img').get(
                'data-src') or article.find('img').get('src')
        except Exception:
            pass
        return data

    def _extract_articles(self, soup):
        articles = soup.find_all("a", {"class": "mntl-card-list-items"})
        articles = [a for a in articles if a["href"].startswith(
            "https://www.allrecipes.com/recipe/")]
        return [self._parse_article(article) for article in articles]

    def search(self, search_string):
        url = f"{self.BASE_URL}search"
        soup = self._fetch_page(url, params={"q": search_string})
        return self._extract_articles(soup)

    def homepage(self):
        pages = [
            "/recipes/84/healthy-recipes",
            "/recipes/76/appetizers-and-snacks",
            "/",
            "/recipes/17562/dinner"
        ]
        soup = self._fetch_page(self.BASE_URL + random.choice(pages))
        return self._extract_articles(soup)

    @staticmethod
    def _get_name(soup):
        return soup.find(
            "h1", {"id": "article-heading_2-0"}).get_text(strip=True)

    @staticmethod
    def _get_rating(soup):
        return float(soup.find(
            "div", {"id": "mntl-recipe-review-bar__rating_2-0"}).get_text(strip=True))

    @staticmethod
    def _get_ingredients(soup):
        return [
            li.get_text(
                strip=True) for li in soup.find(
                "div", {
                    "id": "mntl-structured-ingredients_1-0"}).find_all("li")]

    @staticmethod
    def _get_steps(soup):
        return [
            li.get_text(
                strip=True) for li in soup.find(
                "div", {
                    "id": "recipe__steps_1-0"}).find_all("li")]

    @staticmethod
    def _get_times_data(soup, text):
        return soup.find("div",
                         {"id": "recipe-details_1-0"}).find("div",
                                                            text=text).parent.find("div",
                                                                                   {"class": "mntl-recipe-details__value"}).get_text(strip=True)

    @classmethod
    def _get_prep_time(cls, soup):
        return cls._get_times_data(soup, "Prep Time:")

    @classmethod
    def _get_cook_time(cls, soup):
        return cls._get_times_data(soup, "Cook Time:")

    @classmethod
    def _get_total_time(cls, soup):
        return cls._get_times_data(soup, "Total Time:")

    @classmethod
    def _get_nb_servings(cls, soup):
        return cls._get_times_data(soup, "Servings:")

    def get(self, url):
        soup = self._fetch_page(url)
        elements = [
            {"name": "name", "default_value": ""},
            {"name": "ingredients", "default_value": []},
            {"name": "steps", "default_value": []},
            {"name": "rating", "default_value": None},
            {"name": "prep_time", "default_value": ""},
            {"name": "cook_time", "default_value": ""},
            {"name": "total_time", "default_value": ""},
            {"name": "nb_servings", "default_value": ""},
        ]

        data = {"url": url}
        for element in elements:
            try:
                data[element["name"]] = getattr(
                    self, f"_get_{element['name']}")(soup)
            except Exception:
                data[element["name"]] = element["default_value"]

        return data
