from selenium import webdriver
import time
import json
import pandas as pd
from bs4 import BeautifulSoup

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1000,3000")

wd = webdriver.Chrome("chromedriver", options=chrome_options)
wd.get("https://google.com")
time.sleep(5)
wd.get_screenshot_as_file("test.png")
