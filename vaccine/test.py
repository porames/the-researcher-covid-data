import requests
req=requests.get(url="https://app.powerbi.com/view?r=eyJrIjoiOGFhYzhhMTUtMjBiNS00MWZiLTg4MmUtZTczZGEyMzIzMWYyIiwidCI6ImY3MjkwODU5LTIyNzAtNDc4ZS1iOTc3LTdmZTAzNTE0ZGQ4YiIsImMiOjEwfQ%3D%3D")
print(req)
req.content
"""
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
wd.get("https://dashboard-vaccine.moph.go.th/dashboard.html")
time.sleep(8)
wd.get_screenshot_as_file("test.png")
"""