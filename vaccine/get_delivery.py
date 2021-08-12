import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import tabula
import os
import json

def parse_month(date_th):
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
    update_date_th = date_th.split(" ")
    print(update_date_th)
    if (len(update_date_th[3])>3):
      month = month_mapping[update_date_th[3]]
    else:
      month = month_mapping[update_date_th[4]]
    year = int(update_date_th[-1])-543
    day = update_date_th[2].zfill(2)
    return (f"{year}-{month}-{day}")

def parse_report_by_url(url):
    response = requests.get(url)
    os.makedirs('tmp', exist_ok=True)
    file = open("tmp/daily_report.pdf", "wb")
    file.write(response.content)
    file.close()
    tables = tabula.read_pdf('tmp/daily_report.pdf', pages='2,3,4',pandas_options={'header': None})
    raw_table = pd.DataFrame()
    for i in range(2):
        df=tables[i]
        df=df.fillna("N/A")
        df=df[df[0].str.isnumeric()]
        raw_table = raw_table.append(df,ignore_index=True)
    raw_table.fillna("N/A",inplace=True)
    rows=[]
    for row in raw_table.to_dict(orient="records"):
        cleaned_row=[]
        for (key,value) in row.items():
            for col in str(value).split(' '):
                if (len(col)>0 & (str(col) != "N/A")): cleaned_row.append(col)
        rows.append(cleaned_row)
    cleaned_table = pd.DataFrame(rows)
    cleaned_table = cleaned_table.iloc[:,0:7]
    cleaned_table = cleaned_table.drop(1, axis=1)
    return cleaned_table

def format_table(df):
    #Add province names
    provinces = pd.read_csv("../geo-data/moph_provinces.csv", header=None)
    df["province"] = list(provinces[1])
    df.columns = ["health_area", "population","delivered_sinovac","delivered_astrazeneca","delivered_pfizer","delivered_total","province"]
    df['delivered_pfizer'] = delivery_data['delivered_pfizer'].str.replace('-',"0")
    num_cols = ['population','delivered_sinovac','delivered_astrazeneca','delivered_pfizer','delivered_total']
    for col in num_cols:
      df[col] = df[col].str.replace(',','')
      df[col] = df[col].astype(int)
      
    os.makedirs('../dataset/vaccination', exist_ok=True) 
    prov_data = {}
    prov_data["data"] = df.to_dict(orient="records")
    prov_data["update_date"] = update_date
    return prov_data

if __name__ == "__main__":
    latest_date = pd.to_datetime("today")
    url = "https://ddc.moph.go.th/vaccine-covid19/diaryReportMonth/0" + str(latest_date.month) + "/9/2021"
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    rows = soup.find_all("td", text=re.compile('รายงานสรุปวัคซีน'))
    row = rows[-1]
    tr = row.parent
    report_url = tr.find("a").get("href")
    print('--'+tr.text.strip()+'--')
    report_name = tr.text.strip()
    print(report_name)
    update_date = parse_month(report_name)
    delivery_data = parse_report_by_url(report_url)
    prov_data = format_table(delivery_data)
    with open('../dataset/vaccination/vaccine-delivery.json', 'w+', encoding="utf-8") as f:
        json.dump(prov_data, f, indent=2, ensure_ascii=False)
