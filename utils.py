import time
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

SCROLL_PAUSE_TIME = 0.5

count_regex = re.compile('x(\d+)')

minutes_regex = re.compile('(\d+)м')
hours_regex = re.compile('(\d+)ч')


class Item:
    def __init__(self, price, fee):
        self.link = ""
        self.price = price
        self.fee = fee
        self.count = 0


class Recipe:
    def __init__(self):
        self.items = []
        self.result = None
        self.time = 0


def get_full_page(driver, name):
    driver.get("https://tarkov-market.com/ru/hideout")
    btn = driver.find_element_by_link_text(name)
    btn.click()

    time.sleep(0.5)

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def get_number(soup, text):
    market_data = soup.find_all("div", {"class": "market-data"})
    market_price = soup.find_all(text=re.compile(text))
    if len(market_price) == 0:
        return None
    return market_price[0].parent.findNext('div').text


def get_trader_price(soup):
    market_price = soup.find_all(text=re.compile('Продать торговцу'))
    return market_price[0].parent.findNext("div").find("div", {"class", "bold alt"}).text


def price_to_float(price):
    return float(price.replace('₽', '').replace(' ', ''))


def item_info(address):
    page = requests.get(address)

    page_soup = BeautifulSoup(page.text, "html.parser")

    price = get_number(page_soup, 'Цена на барахолке')
    fee = get_number(page_soup, 'Комиссия')
    if price is None:
        price = get_trader_price(page_soup)
        fee = "0₽"

    price = price_to_float(price)
    fee = price_to_float(fee)

    return price, fee


def get_recipe(recipe):
    craft = recipe.find_all("div", recursive=False)[1]
    items = craft.find_all("div", recursive=False)

    craft_recipe = Recipe()

    for i in range(len(items)):
        item = items[i]
        if item.has_attr("class") and "process" in item["class"]:
            craft_time = item.find("div", {"class": "no-wrap"}).text
            minutes = minutes_regex.findall(craft_time)
            hours = hours_regex.findall(craft_time)

            hours_time = (float(minutes[0]) / 60.0 if len(minutes) > 0 else 0) + (
                float(hours[0]) if len(hours) > 0 else 0)
            craft_recipe.time = hours_time

            # print(craft_time, hours_time)
        else:
            link = item.find_all("a", {"class": "item-img"})[0]["href"]
            link = "https://tarkov-market.com" + link
            item_divs = item.find_all("div", recursive=False)
            count = int(count_regex.findall(item_divs[2].text)[0])

            price, fee = item_info(link)

            craft_item = Item(price, fee)

            craft_item.link = link
            craft_item.count = count

            if i < len(items) - 1:
                craft_recipe.items.append(craft_item)
            else:
                craft_recipe.result = craft_item

    return craft_recipe


def link_name(link):
    return link.split('/')[-1]


def get_df(crafts):
    incomes = []
    incomes_h = []
    names = []

    for craft in crafts:
        components_price = 0
        for item in craft.items:
            components_price += item.price * item.count

        sell_price = (craft.result.price - craft.result.fee) * craft.result.count
        income = sell_price - components_price
        income_h = income / craft.time
        incomes.append(income)
        incomes_h.append(income_h)
        names.append(link_name(craft.result.link))

        # print(income, income_h, link_name(craft.result.link),  craft.result.count)

    data = {'Name': names, 'income': incomes, 'income/h': incomes_h}

    df = pd.DataFrame(data).sort_values(by=['income/h'], ascending=False)
    return df
