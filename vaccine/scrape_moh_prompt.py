from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import sys
import os
import time
import json
import pandas as pd
from bs4 import BeautifulSoup
from multiprocessing import Pool


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1000,3000")

with open("../population-data/th-census-data.json", encoding="utf-8") as file:
    census = json.load(file)


def get_age_group(wd):
    wd.switch_to.frame(wd.find_element_by_css_selector(".visual-sandbox"))
    age_chart = BeautifulSoup(wd.page_source, "html.parser")
    age_groups = [">80", "61-80", "41-60", "21-40", "18-20"]
    age_group_doses = {}
    i = 0
    for label in age_chart.find("g", {"class": "labels"}).findAll("text"):
        if label.get_text():
            if age_groups[i % 5] in age_group_doses.keys():
                age_group_doses[age_groups[i % 5]] += (to_number(label.get_text()))
            else:
                age_group_doses[age_groups[i % 5]] = (to_number(label.get_text()))

            i += 1
    wd.switch_to.default_content()
    return age_group_doses


def search_doses_num(wd) -> int:
    total_dose = 0
    for svg in wd.find_elements_by_tag_name("svg"):
        label = svg.get_attribute("aria-label")
        if "totalDose" in str(label):
            total_dose = int(label.replace("totalDose", "").replace(",", "").replace(" ", "").replace(".", ""))
            break
    return total_dose


def search_manufacturer(wd) -> dict:
    df = pd.DataFrame()
    soup = BeautifulSoup(wd.page_source, "html.parser")
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
    return {key: value["3rd-dose"] for key, value in mf.items()}

def get_mf(wd):    
    actionChains = ActionChains(wd)
    az=wd.find_element_by_xpath("//*[text()[contains(.,'AstraZeneca')]]")
    actionChains.context_click(az).perform()
    time.sleep(0.5)
    wd.find_element_by_xpath("//*[text()[contains(.,'Show as a table')]]").click()
    time.sleep(1)
    wait = WebDriverWait(wd, 10)
    wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "rowHeaders")))
    mf_dict = {}
    names = []
    doses = []
    for cell in wd.find_element_by_class_name("rowHeaders").find_elements_by_tag_name("div"):
        mf=cell.get_attribute("title")
        if mf: names.append(mf)
    for cell in wd.find_element_by_class_name("bodyCells").find_elements_by_tag_name("div"):
        dose = cell.get_attribute("title").replace(",","")
        if dose: doses.append(dose)
    for i in range(len(names)):
        mf_dict[names[i]] = doses[i]        
    wd.find_element_by_xpath("//*[text()[contains(.,'Back to report')]]").click()
    return mf_dict

def open_province_dropdown(wd) -> None:
    for menu in wd.find_elements_by_class_name("slicer-dropdown-menu"):
        label = menu.get_attribute("aria-label")
        if "จังหวัด" in label:
            menu.click()
            break


def get_province(prov_th: str, wd) -> dict:
    open_province_dropdown(wd)
    time.sleep(0.5)
    for elm in wd.find_elements_by_class_name("searchInput"):
        if elm.get_attribute("style") != "":
            elm.clear()
            elm.send_keys(prov_th)
            break
    wait = WebDriverWait(wd, 10)
    wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[@title='{prov_th}']"))).click()
    # wd.find_elements_by_class_name("slicerText")[-1].click()
    time.sleep(1)
    doses = search_doses_num(wd)    
    groups = get_age_group(wd)
    mf = get_mf(wd)
    data = mf
    data["total-dose"] = doses
    data["province"] = prov_th
    data.update(groups)
    time.sleep(1)
    return data


def to_number(string: str) -> int:
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
    month_mapping = {
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
    update_date_th = wd.find_element_by_css_selector("h3").get_attribute("innerHTML").split(" ")
    year = int(update_date_th[3]) - 543
    month = month_mapping[update_date_th[2]]
    day = update_date_th[1].zfill(2)
    hour, minute = update_date_th[5].split(":")
    return f"{year}-{month}-{day}T{hour.zfill(2)}:{minute}"


def scrape_and_save_moh_prompt(dose_num:int):
    dose_to_khem = {
        1: "เข็มหนึ่ง",
        2: "เข็มสอง",
        3: "เข็มสาม"
    }
    print(dose_to_khem[dose_num])
    print("Spawning Chromium")
    wd = webdriver.Chrome("chromedriver", options=chrome_options)
    wd.get(
        "https://app.powerbi.com/view?r=eyJrIjoiOGFhYzhhMTUtMjBiNS00MWZiLTg4MmUtZTczZGEyMzIzMWYyIiwidCI6ImY3MjkwODU5LTIyNzAtNDc4ZS1iOTc3LTdmZTAzNTE0ZGQ4YiIsImMiOjEwfQ%3D%3D")
    print("Rendering JS for 10 s")
    wait = WebDriverWait(wd, 10)
    time.sleep(10)
    print("Selecting Button")
    
    wait.until(
        EC.visibility_of_element_located((By.XPATH, f"//div[contains(@title,'{dose_to_khem[dose_num]}')]"))).click()
    print(f"{dose_to_khem[dose_num]} Found")
    time.sleep(2)
    dataset = pd.DataFrame()
    
    start = time.time()
    i = 0
    for province_name in census:
        province_data = get_province(province_name["province"], wd)
        dataset = dataset.append(province_data, ignore_index=True)
        print(province_data)
        print(str(i + 1) + "/77 Provinces")
        print("Time elapsed: " + str(round(time.time() - start, 2)) + "s")
        i += 1

    dataset = dataset.fillna(0)
    dataset[[
        "AstraZeneca",
        "Johnson & Johnson",
        "Sinopharm",
        "Sinovac",
        "total-dose",
        ">80",
        "61-80",
        "41-60",
        "21-40",
        "18-20"
    ]] = dataset[[
        "AstraZeneca",
        "Johnson & Johnson",
        "Sinopharm",
        "Sinovac",
        "total-dose",
        ">80",
        "61-80",
        "41-60",
        "21-40",
        "18-20"
    ]].astype(int)

    # Sort dataframe row for json
    dataset = dataset[[
        "province",
        "AstraZeneca",
        "Johnson & Johnson",
        "Sinopharm",
        "Sinovac",
        "total-dose",
        ">80",
        "61-80",
        "41-60",
        "21-40",
        "18-20"
    ]]

    data_dict = {
        "update_date": get_update_date(wd),
        "data": dataset.to_dict(orient="records"),
    }

    # JSON file name according to dose number
    car_to_or = {
        1: "1st",
        2: "2nd",
        3: "3rd",
    }
    json_dir = "../dataset/"
    os.makedirs(json_dir, exist_ok=True)  # Make sure that we ABSOLUTELY have the target dir
    with open(f"{json_dir}{car_to_or[dose_num]}-dose-provincial-vaccination.json", "w+") as json_file:
        json.dump(data_dict, json_file, ensure_ascii=False, indent=2)

    wd.quit()
    return data_dict


if __name__ == "__main__":
    scrape_and_save_moh_prompt(int(sys.argv[1]))
