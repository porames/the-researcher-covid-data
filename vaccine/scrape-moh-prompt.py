
# In[1]:


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import pandas as pd
from bs4 import BeautifulSoup
from multiprocessing import Pool


# In[2]:


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=1000,3000")


# In[3]:


f = open('../population_data/th-census-data.json','r')
census=json.load(f)


# In[16]:


def search_doses_num(wd):
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


def search_manufacturer(wd):
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


def open_province_dropdown(wd):
    for menu in wd.find_elements_by_class_name("slicer-dropdown-menu"):
        label = menu.get_attribute("aria-label")
        if "จังหวัด" in label:
            menu.click()
            break


def select_province(prov_th,wd):
    for elm in wd.find_elements_by_class_name("searchInput"):
        if elm.get_attribute("style") != "":
            elm.clear()
            elm.send_keys(prov_th)
            break
    time.sleep(1.5)
    wd.find_elements_by_class_name("slicerText")[-1].click()
    time.sleep(1.5)
    doses = search_doses_num(wd)
    mf = search_manufacturer(wd)
    data = mf
    data["total-dose"] = doses
    data["province"] = prov_th
    time.sleep(1)
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
    time = update_date_thai[5].split(":")
    return f"{int(update_date_thai[3])-543}-{MONTH_MAPPING[update_date_thai[2]]}-{update_date_thai[1].zfill(2)}T{time[0].zfill(2)}:{time[1]}"

# In[17]:


def scrape_and_save_moh_prompt(dose_num):
    print("Spawning Chromium")
    wd = webdriver.Chrome("chromedriver", options=chrome_options)
    wd.get("https://app.powerbi.com/view?r=eyJrIjoiOGFhYzhhMTUtMjBiNS00MWZiLTg4MmUtZTczZGEyMzIzMWYyIiwidCI6ImY3MjkwODU5LTIyNzAtNDc4ZS1iOTc3LTdmZTAzNTE0ZGQ4YiIsImMiOjEwfQ%3D%3D")
    print("Rendering JS")
    time.sleep(10)
    print("Selecting Button")
    wait = WebDriverWait(wd, 10)
    if(dose_num==1):
        wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@title,'เข็มหนึ่ง')]"))).click()
        print("เข็มหนึ่ง Found")
    elif(dose_num==2):
        wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@title,'เข็มสอง')]"))).click()
        print("เข็มสอง Found")
    elif(dose_num==3):
        wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@title,'เข็มสาม')]"))).click()
        print("เข็มสาม Found")
    time.sleep(2)
    open_province_dropdown(wd)
    dataset = pd.DataFrame()
    time.sleep(2)
    for p in census:
        province_data = select_province(p["province"],wd)
        dataset = dataset.append(province_data, ignore_index=True)
        print(p["province"], province_data)

    dataset = dataset.fillna(0)
    dataset[["AstraZeneca","Johnson & Johnson","Sinopharm","Sinovac","total-dose"]] = dataset[["AstraZeneca","Johnson & Johnson","Sinopharm","Sinovac","total-dose"]].astype(int)
    dataset = dataset[["province","AstraZeneca","Johnson & Johnson","Sinopharm","Sinovac","total-dose"]]

    data_dict = {
        "update_date": get_update_date(wd),
        "data": dataset.to_dict(orient="records"),
    }
    if(dose_num==1):
        with open("data/1st-dose-provincial-vaccination.json", "w+") as json_file:
            json.dump(data_dict, json_file, ensure_ascii=False, indent=2)
    elif(dose_num==2):
        with open("data/2nd-dose-provincial-vaccination.json", "w+") as json_file:
            json.dump(data_dict, json_file, ensure_ascii=False, indent=2)
    elif(dose_num==3):
        with open("data/3rd-dose-provincial-vaccination.json", "w+") as json_file:
            json.dump(data_dict, json_file, ensure_ascii=False, indent=2)
    return data_dict


# In[14]:


if __name__ == '__main__':
   with Pool(5) as p:
       print(p.map(scrape_and_save_moh_prompt, [1, 2, 3]))

