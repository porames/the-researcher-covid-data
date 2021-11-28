from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
import sys
import os
import time
import json
import pandas as pd
from bs4 import BeautifulSoup

firefox_options = webdriver.FirefoxOptions()
firefox_options.add_argument("--headless")
firefox_options.add_argument("--no-sandbox")
firefox_options.add_argument("--disable-dev-shm-usage")


with open("./population-data/th-census-data.json", encoding="utf-8") as file:
    census = json.load(file)

def get_over_60(wd):
    wait = WebDriverWait(wd, 10)
    total_doses = search_doses_num(wd)
    over_60_btn = wd.find_element_by_xpath("//*[text()[contains(.,'60 ปีขึ้นไป')]]/..")
    print(over_60_btn.get_attribute("innerHTML"))
    over_60_btn.click()
    time.sleep(1)    
    over_60_1st_dose = search_doses_num(wd)
    try_count = 0
    while over_60_1st_dose/total_doses > 0.8:
        if try_count>5:
            raise ValueError("Try exceeded. Task killed.")
        over_60_1st_dose = search_doses_num(wd)
        print("Over 60 doses too high. Trying it again...")        
        time.sleep(1)
        try_count+=1
    over_60_btn.click()
    return over_60_1st_dose

def get_age_group(wd):
    wd.switch_to.frame(wd.find_element_by_css_selector(".visual-sandbox"))
    age_chart = BeautifulSoup(wd.page_source, "html.parser")
    age_groups = [">80", "61-80", "41-60", "21-40", "18-20", "12-17", "03-11"]
    age_group_doses = {}
    i = 0
    for title in age_chart.findAll("title",{"class": "label-title"}):
        dose = title.get_text()
        if (dose):
            print(f"{age_groups[i % len(age_groups)]} {dose}")
            if age_groups[i % len(age_groups)] in age_group_doses.keys():
                age_group_doses[age_groups[i % len(age_groups)]] += int(dose)
            else:
                age_group_doses[age_groups[i % len(age_groups)]] = int(dose)
            i+=1
    wd.switch_to.default_content()
    return age_group_doses


def search_doses_num(wd) -> int:
    total_dose = 0
    for svg in wd.find_elements_by_tag_name("svg"):
        label = svg.get_attribute("aria-label")
        if "ฉีดสะสม" in str(label):
            total_dose = int(label.replace("ฉีดสะสม", "").replace(",", "").replace(" ", "").replace(".", ""))
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
    go_back = wd.find_element_by_xpath("//*[text()[contains(.,'Back to report')]]")
    wd.execute_script('arguments[0].click()', go_back)
    return mf_dict

def open_province_dropdown(wd) -> None:    
    for menu in wd.find_elements_by_class_name("slicer-dropdown-menu"):
        label = menu.get_attribute("aria-label")
        if "จังหวัด" in label:
            wd.execute_script('arguments[0].click()', menu)
            break


def get_province(prov_th: str, wd, dose_num) -> dict:    
    open_province_dropdown(wd)
    time.sleep(1)    
    wd.execute_script("document.getElementsByClassName('searchHeader')[2].style.display = 'block';")
    wd.execute_script("document.getElementsByClassName('searchHeader')[2].style.overflow = 'visible';")    
    wd.execute_script(f"document.getElementsByClassName('searchInput')[2].value = '{prov_th}';")    
    # wd.find_elements_by_class_name("searchInput")[2].clear()      
    wd.find_elements_by_class_name("searchInput")[2].send_keys(Keys.ENTER)
    wait = WebDriverWait(wd, 10)
    time.sleep(1.5)
    wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[@class='glyphicon checkbox']"))).click()
    time.sleep(3)
    doses = search_doses_num(wd)    
    data = {}
    data["total_doses"] = doses
    data["province"] = prov_th    
    if (dose_num == 1):
        print(prov_th)
        over_60 = get_over_60(wd)
        data.update({"over_60_1st_dose": over_60})
    if (dose_num == 0):
        mf = get_mf(wd) 
        data.update(mf)    
    if (dose_num > 1):
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[contains(.,'{prov_th}')]"))).click()
        open_province_dropdown(wd)
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
    year = int(update_date_th[3])
    # Dirty hack for checking for BE or AD, Will break in about 480 years.
    if year > 2500:
        print("Year is BE, converting to AD")
        year -= 543
    month = month_mapping[update_date_th[2]]
    day = update_date_th[1].zfill(2)
    hour, minute = update_date_th[5].split(":")
    return f"{year}-{month}-{day}T{hour.zfill(2)}:{minute}"


def scrape_and_save_moh_prompt(dose_num:int):
    dose_to_khem = {
        0: "Total doses and Manufacturer data",
        1: "เข็มหนึ่ง",
        2: "เข็มสอง",
        3: "เข็มสาม"
    }
    print(dose_to_khem[dose_num])
    print("Spawning Firefox")
    wd = webdriver.Firefox(options=firefox_options)
    wd.set_window_size(1000, 3000)
    wd.get("https://dashboard-vaccine.moph.go.th/dashboard.html")
    print("Rendering JS for 5S")
    time.sleep(5)
    today_powerbi = wd.find_element_by_tag_name("iframe").get_attribute("src")
    print(today_powerbi)
    wd.get(today_powerbi)
    print("Found Power Bi URL. Rendering JS for 10S")
    time.sleep(10)
    wait = WebDriverWait(wd, 10)
    print("Selecting Button")
    os.makedirs("./debug",exist_ok=True)
    wd.get_screenshot_as_file("./debug/1.png")
    if ((dose_num>0) & (dose_num<4)):        
        dose_btn = wd.find_elements_by_class_name("slicer-dropdown-menu")[-1]
        wd.execute_script('arguments[0].click()', dose_btn)
        time.sleep(1)
        wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//span[contains(.,'{dose_to_khem[dose_num]}')]"))
        ).click()
        print(f"{dose_to_khem[dose_num]} Found")
    elif dose_num == 0:
        print("retreive manufacturer data") 
    else:
        print("function doesn't exist")
    time.sleep(2)
    initial_total_doses=search_doses_num(wd)
    print(initial_total_doses)
    dataset = pd.DataFrame()    
    start = time.time()
    i = 0
    for province_name in census:
        province_data = get_province(province_name["province"], wd, dose_num)        
        print(province_data)
        province_total_doses = province_data["total_doses"]
        try_count=0
        while (province_total_doses / initial_total_doses > 0.6):
            if try_count>3:
                raise ValueError("Try exceeded. Task killed.")
            print("Doses number too high. Trying it again.")    
            province_data = get_province(province_name["province"], wd, dose_num)
            province_total_doses = province_data["total_doses"]
            print(province_data)
            try_count+=1
        dataset = dataset.append(province_data, ignore_index=True)        
        print(str(i + 1) + "/77 Provinces")
        print("Time elapsed: " + str(round(time.time() - start, 2)) + "s")
        i += 1

    dataset = dataset.fillna(0)
    # Key names according to dose number
    car_to_or = {
        1: "1st",
        2: "2nd",
        3: "3rd",
    }
    if dose_num == 0:
      dataset[[
          "AstraZeneca",
          "Johnson & Johnson",
          "Sinopharm",
          "Sinovac",
          "Pfizer",
          "total_doses"
      ]] = dataset[[
          "AstraZeneca",
          "Johnson & Johnson",
          "Sinopharm",
          "Sinovac",
          "Pfizer",          
          "total_doses"
      ]].astype(int)
    else:
       dataset["total_"+car_to_or[dose_num]+"_dose"] = dataset["total_doses"].astype(int)
       dataset = dataset.drop('total_doses', axis=1)

    data_dict = {
        "update_date": get_update_date(wd),
        "data": dataset.to_dict(orient="records"),
    }
    
    json_dir = "./dataset"
    os.makedirs(json_dir, exist_ok=True)
    if dose_num != 0:
        with open(f"{json_dir}/{car_to_or[dose_num]}-dose-provincial-vaccination.json", "w+") as json_file:
            json.dump(data_dict, json_file, ensure_ascii=False, indent=2)
    else:
        with open(f"{json_dir}/provincial-vaccination-by-manufacturer.json", "w+") as json_file:
            json.dump(data_dict, json_file, ensure_ascii=False, indent=2)
    wd.quit()
    return data_dict

def scrape_age_group():
    dose_to_khem = {
        1: "เข็มหนึ่ง",
        2: "เข็มสอง",
        3: "เข็มสาม"
    }
    car_to_or = {
        1: "1st",
        2: "2nd",
        3: "3rd",
    }
    print("Spawning Firefox")
    wd = webdriver.Firefox(options=firefox_options)
    wd.set_window_size(1000, 3000)
    wd.get("https://dashboard-vaccine.moph.go.th/dashboard.html")
    print("Rendering JS for 5S")
    time.sleep(5)
    today_powerbi = wd.find_element_by_tag_name("iframe").get_attribute("src")
    print(today_powerbi)
    wd.get(today_powerbi)
    print("Found Power Bi URL. Rendering JS for 10S")
    time.sleep(10)
    wait = WebDriverWait(wd, 10)
    print("Selecting Button")
    dataset = {}
    dataset["update_date"] = get_update_date(wd)
    for dose_num in range(1,4):
        dose_btn = wd.find_elements_by_class_name("slicer-dropdown-menu")[-1]
        wd.execute_script('arguments[0].click()', dose_btn)
        time.sleep(1)
        wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//span[contains(.,'{dose_to_khem[dose_num]}')]"))
        ).click()
        print(f"{dose_to_khem[dose_num]} Found")
        time.sleep(5)
        doses_by_age = get_age_group(wd)
        dataset[f"total_{car_to_or[dose_num]}_dose"] = doses_by_age
    json_dir = "./dataset"
    os.makedirs(json_dir, exist_ok=True)    
    with open(f"{json_dir}/vaccination-by-age-group.json", "w+") as json_file:
        json.dump(dataset, json_file, ensure_ascii=False, indent=2)
    wd.quit()
    return dataset

if __name__ == "__main__":
    if(int(sys.argv[1]) < 4):
        scrape_and_save_moh_prompt(int(sys.argv[1]))
    else:
        scrape_age_group()
