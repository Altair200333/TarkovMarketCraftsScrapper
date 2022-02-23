import numpy as np
import requests
from bs4 import BeautifulSoup

URL = "https://tarkov-market.com/ru/hideout"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")

mydivs = soup.find_all("div", {"class": "row recipe"})

print(mydivs[0])