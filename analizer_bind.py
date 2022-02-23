from selenium import webdriver

import pandas as pd
from utils import *
import numpy as np
import requests
from bs4 import BeautifulSoup


def analize_crafts(tab_name, consider_fuel=True, start_headless=True):
    options = webdriver.ChromeOptions()

    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    if start_headless:
        options.add_argument('--headless')

    driver = webdriver.Chrome(".\chromedriver.exe", chrome_options=options)

    get_full_page(driver, tab_name)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    recipes = soup.find_all("div", {"class": "row recipe"})
    print("recipes loaded: ", len(recipes))

    crafts = []
    for i in range(len(recipes)):
        rec = get_recipe(recipes[i])
        crafts.append(rec)

    df = get_df(crafts)

    if consider_fuel:
        fuel_price, _ = item_info("https://tarkov-market.com/ru/item/Metal_fuel_tank")
        print("Fuel price: ", fuel_price)

        df["income/h w fuel"] = df["income/h"] - fuel_price / 21

    return df, crafts
