import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import camelot
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
    month = month_mapping[update_date_th[3]]
    year = int(update_date_th[-1])-543
    day = update_date_th[2].zfill(2)
    return (f"{year}-{month}-{day}")

def parse_report_by_url(url):
  response = requests.get(url)
  os.makedirs('tmp', exist_ok=True) 
  file = open("tmp/daily_report.pdf", "wb")
  file.write(response.content)
  file.close()
  tables = camelot.read_pdf('tmp/daily_report.pdf', pages='2,3',split_text=True)
  raw_table = pd.DataFrame()
  for i in range(2):
    df=tables[i].df
    df=df[df[1].str.isdigit()]
    df.drop([2], axis=1, inplace=True)
    raw_table = raw_table.append(df,ignore_index=True)
  table_dict=raw_table.transpose().to_dict()
  rows=[]
  for row_num in table_dict:
    cleaned_row=[]
    for (key,value) in table_dict[row_num].items():
      for col in value.replace(" ", "").split('\n'):
        if(col): cleaned_row.append(col)
    rows.append(cleaned_row)
  cleaned_table = pd.DataFrame(rows)
  return cleaned_table

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
    update_date = parse_month(report_name)
    print(update_date)
    delivery_data = parse_report_by_url(report_url)
    delivery_data = delivery_data.iloc[:,0:6]
    provinces = pd.read_csv("/content/drive/MyDrive/Colab Notebooks/moph_provinces.csv", header=None)
    delivery_data["province"] = list(provinces[1])
    delivery_data.columns = ["health_area", "population","delivered_sinovac","delivered_astrazeneca","delivered_pfizer","delivered_total","province"]
    delivery_data['delivered_pfizer'] = delivery_data['delivered_pfizer'].str.replace('-',"0")
    num_cols = ['population','delivered_sinovac','delivered_astrazeneca','delivered_pfizer','delivered_total']
    for col in num_cols:
      delivery_data[col] = delivery_data[col].str.replace(',','')
      delivery_data[col] = delivery_data[col].astype(int)
    os.makedirs('../dataset/vaccination', exist_ok=True) 
    prov_data = {}
    prov_data["data"] = delivery_data.to_dict(orient="records")
    prov_data["update_date"] = update_date
    with open('../dataset/vaccination/vaccine-delivery.json', 'w+', encoding="utf-8") as f:
        json.dump(prov_data, f, indent=2, ensure_ascii=False)