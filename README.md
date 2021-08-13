# The Researcher COVID data

[![bot-tasks-scheduler](https://github.com/porames/the-researcher-covid-data/actions/workflows/main.yml/badge.svg)](https://github.com/porames/the-researcher-covid-data/actions/workflows/main.yml)

Automated data scraper for Thailand COVID-19 data.  
[The Researcher COVID Tracker](https://covid-19.researcherth.co)

## ข้อมูลสถานการณ์การระบาด

- ข้อมูลสถิติการระบาด เสียชีวิต รักษาในโรงพยาบาล ทั่วประเทศรายวัน [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/cases/national-timeseries.json)
- ข้อมูลการระบาดระดับอำเภอ [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/cases/district-cases-data-14days.json)
- ข้อมูลการระบาดระดับจังหวัดในรอบ 14 วัน [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/cases/province-cases-data-14days.json)
- การตรวจเชื้อทางห้องปฏิบัติการ RT-PCR [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/cases/testing-data.json)

## ข้อมูลวัคซีน

- การฉีดวัคซีนรายจังหวัด แยกตามโดสที่ฉีด [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/provincial-vaccination.json), [CSV](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/provincial-vaccination.csv)
- การฉีดวัคซีนรายจังหวัด แยกตามชนิดวัคซีน [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/provincial-vaccination-by-manufacturer.json), [CSV](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/provincial-vaccination-by-manufacturer.csv)
- การจัดสรรวัคซีน (จำนวนวัคซีนของรัฐบาลที่จัดส่งลงพื้นที่) [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/vaccine-delivery.json)
- อัตราการฉีดวัคซีนของแต่ละผู้ผลิต [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/vaccine-manufacturer-timeseries.json), [CSV](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/vaccine-manufacturer-timeseries.csv)
- อัตราการฉีดวัคซีนทั้งประเทศ [JSON](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/national-vaccination-timeseries.json), [CSV](https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data/vaccination/national-vaccination-timeseries.csv)

### ข้อควรรู้เกี่ยวกับข้อมูลการฉีดวัคซีน

- เข็ม 1 หมายถึงจำนวนคนที่ได้รับวัคซีนอย่างน้อย 1 เข็ม
- เข็ม 2 หมายถึงจำนวนคนที่ได้รับวัคซีนอย่างน้อย 2 เข็ม
- เข็ม 3 หมายถึงจำนวนคนที่ได้รับวัคซีนกระตุ้นเข็มที่ 3
- เซตของคนฉีดวัคซีนอย่างน้อย 2 เข็มเป็นเซตย่อยของคนฉีดวัคซีนอย่างน้อย 1 เข็ม เวลารายงานร้อยละการฉีดวัคซีนจะเอาเข็ม 1 มารวมกับเข็ม 2 ไม่ได้ (นะครับ 😏)

## ที่มาข้อมูล

- ข้อมูลจำนวนผู้ป่วยรายวันจาก [กรมควบคุมโรค กระทรวงสาธารณสุข](https://ddc.moph.go.th/covid19-dashboard/) ประมวลผลโดยคุณ [Noppakorn](https://github.com/noppakorn/ddc-dashboard-scraping)
- ข้อมูลตำแหน่งที่พบผู้ป่วยประจำวันจาก [กรมควบคุมโรค กระทรวงสาธารณสุข](https://data.go.th/dataset/covid-19-daily)
- ข้อมูลการตรวจเชื้อรายวันจาก [กรมวิทยาศาสตร์การแพทย์ กระทรวงสาธารณสุข](http://data.go.th/dataset/covid-19-testing-data)
- ข้อมูลการฉีดวัคซีนจาก [หมอพร้อม](https://dashboard-vaccine.moph.go.th/dashboard.html)
- ข้อมูลจำนวนการฉีดวัคซีนรายวันจาก [รายงานการฉีดวัคซีนประจำวัน กรมควบคุมโรค กระทรวงสาธารณสุข](https://ddc.moph.go.th/vaccine-covid19/diaryReport) ประมวลผลจาก PDF โดยคุณ [Dylan Jay](https://github.com/djay/covidthailand)
- ข้อมูลการฉีดวัคซีนรายจังหวัดและรายศูนย์ให้บริการฉีดวัคซีนจาก [ระบบติดตามตรวจสอบย้อนกลับโซ่ความเย็นวัคซีนโควิด-19](https://datastudio.google.com/u/0/reporting/731713b6-a3c4-4766-ab9d-a6502a4e7dd6/page/JMn3B) มหาวิทยาลัยมหิดล (โดนสั่งปิดไปแล้ว)
- จำนวนประชากรแต่ละจังหวัดแยกตามกลุ่มอายุ อ้างอิงจาก[สถิติประชากรศาสตร์](http://statbbi.nso.go.th/staticreport/page/sector/th/01.aspx) สำนักงานสถิติแห่งชาติ รายงานสำรวจล่าสุดเมื่อปี พ.ศ. 2563
