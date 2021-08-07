# The Researcher COVID data
[![bot-tasks-scheduler](https://github.com/porames/the-researcher-covid-data/actions/workflows/main.yml/badge.svg)](https://github.com/porames/the-researcher-covid-data/actions/workflows/main.yml)
  
Automated data scraper for Thailand COVID-19 data.  
[The Researcher COVID Tracker](https://covid-19.researcherth.co)

## ข้อมูลวัคซีน
- การฉีดวัคซีนรายจังหวัด แยกตามโดสที่ฉีด [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/provincial-vaccination.json)
- การฉีดวัคซีนรายจังหวัด แยกตามชนิดวัคซีน [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/provincial-vaccination-by-manufacturer.json)
- การฉีดวัคซีนเข็ม 1 รายจังหวัด [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/1st-dose-provincial-vaccination.json)
- การฉีดวัคซีนเข็ม 2 รายจังหวัด [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/2nd-dose-provincial-vaccination.json)
- การฉีดวัคซีนเข็ม 3 รายจังหวัด [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/3rd-dose-provincial-vaccination.json)
- อัตราการฉีดวัคซีนของแต่ละผู้ผลิต [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/vaccine-manufacturer-timeseries.json), [CSV](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/vaccine-manufacturer-timeseries.csv)  
- อัตราการฉีดวัคซีนทั้งประเทศ [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/national-vaccination-timeseries.json), [CSV](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/national-vaccination-timeseries.csv)

### ข้อควรรู้เกี่ยวกับข้อมูลการฉีดวัคซีน
- เข็ม 1 หมายถึงจำนวนคนที่ได้รับวัคซีนอย่างน้อย 1 เข็ม
- เข็ม 2 หมายถึงจำนวนคนที่ได้รับวัคซีนอย่างน้อย 2 เข็ม
- เข็ม 3 หมายถึงจำนวนคนที่ได้รับวัคซีนกระตุ้นเข็มที่ 3
- เซตของคนฉีดวัคซีนอย่างน้อย 2 เข็มเป็นเซตย่อยของคนฉีดวัคซีนอย่างน้อย 1 เข็ม เวลารายงานร้อยละการฉีดวัคซีนจะเอาเข็ม 1 มารวมกับเข็ม 2 ไม่ได้ (นะครับ 😏)

