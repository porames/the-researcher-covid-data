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

f = open("../population_data/th-census-data.json", "r")
census = json.load(f)


def search_booster_doses():
    totalDose = 0
    for svg in wd.find_elements_by_tag_name("svg"):
        label = svg.get_attribute("aria-label")
        if "totalDose" in str(label):
            totalDose = (
                label.replace("totalDose", "")
                .replace(",", "")
                .replace(" ", "")
                .replace(".", "")
            )
            totalDose = int(totalDose)
            break
    return totalDose


def search_manufacturer():
    df = pd.DataFrame()
    soup = BeautifulSoup(wd.page_source)
    for svg in soup.findAll("g", {"class": "labelGraphicsContext"})[1]:
        x = svg["transform"].replace("translate(", "").replace(")", "").split(",")[0]
        df = df.append(
            {"3rd-dose": to_number(svg.get_text()), "x": x}, ignore_index=True
        )
    df = df.sort_values(by="x", ignore_index=True)
    for elm in soup.findAll("g", {"class": "columnChart"})[1]:
        i = 0
        for texts in elm.findAll("title"):
            df.loc[i, "manufacturer"] = texts.get_text()
            i += 1
    mf = df.drop("x", axis=1).set_index("manufacturer").transpose().to_dict()
    mf_dict = {}
    for key, value in mf.items():
        mf_dict[key] = value["3rd-dose"]
    return mf_dict


def open_province_dropdown():
    for menu in wd.find_elements_by_class_name("slicer-dropdown-menu"):
        label = menu.get_attribute("aria-label")
        if "จังหวัด" in label:
            menu.click()
            break


def select_province(prov_th):
    for elm in wd.find_elements_by_class_name("searchInput"):
        if elm.get_attribute("style") != "":
            elm.clear()
            elm.send_keys(prov_th)
            break
    time.sleep(1)
    wd.find_elements_by_class_name("slicerText")[-1].click()
    time.sleep(2)
    doses = search_booster_doses()
    mf = search_manufacturer()
    data = mf
    data["total-3rd-dose"] = doses
    data["province"] = prov_th
    time.sleep(2)
    wd.find_elements_by_class_name("slicerText")[-1].click()
    return data


def to_number(string : str) -> int :
    string = string.replace(",", "")
    if "K" in string:
        number = float(string.replace("K", "")) * 1000
        return int(number)
    elif "M" in string:
        number = float(string.replace("M", "")) * 1000 * 1000
        return int(number)
    else:
        return int(float(string))

def get_update_date(wd) -> str:
# TODO : Maybe a better solution or move somewhere else?
    update_date_thai = wd.find_element_by_css_selector("h3").get_attribute("innerHTML").split(" ")
    MONTH_MAPPING = {
        "มกราคม": "01",
        "กุมภาพันธ์": "02",
        "มีนาคม": "03",
        "เมษายน": "04",
        "พฤษภาคม": "05",
        "มิถุนายน": "06",
        "กรกฎาคม": "07",
        "สิงหาคม": "08",
        "กันยายน": "09",
        "ตุลาคม": "10",
        "พฤศจิกายน": "11",
        "ธันวาคม": "12",
    }
    return f"{int(update_date_thai[3])-543}-{MONTH_MAPPING[update_date_thai[2]]}-{update_date_thai[1].zfill(2)}"

wd = webdriver.Chrome("chromedriver", options=chrome_options)
wd.get("https://app.powerbi.com/view?r=eyJrIjoiOGFhYzhhMTUtMjBiNS00MWZiLTg4MmUtZTczZGEyMzIzMWYyIiwidCI6ImY3MjkwODU5LTIyNzAtNDc4ZS1iOTc3LTdmZTAzNTE0ZGQ4YiIsImMiOjEwfQ%3D%3D")
time.sleep(5)
wd.find_element_by_xpath("//div[@title='เข็มสาม']").click()
time.sleep(2)
open_province_dropdown()
dataset = pd.DataFrame()
time.sleep(2)
for p in census:
    province_data = select_province(p["province"])
    dataset = dataset.append(province_data, ignore_index=True)
    print(p["province"], province_data)

dataset = dataset.fillna(0)
dataset[["AstraZeneca","Johnson & Johnson","Sinopharm","Sinovac","total-3rd-dose"]] = dataset[["AstraZeneca","Johnson & Johnson","Sinopharm","Sinovac","total-3rd-dose"]].astype(int)
dataset = dataset[["province","AstraZeneca","Johnson & Johnson","Sinopharm","Sinovac","total-3rd-dose"]]

data_dict = {
    "update_date": get_update_date(wd),
    "data": dataset.to_dict(orient="records"),
}

with open("data/3rd-dose-provincial-vaccination.json", "w+") as json_file:
    json.dump(data_dict, json_file, ensure_ascii=False, indent=2)
