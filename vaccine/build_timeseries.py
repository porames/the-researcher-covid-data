#%%
from numpy import NaN, disp
import pandas as pd
import os
import json
import numpy as np

MAIN_URL = "https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data"
#%%
def json_load(file_path: str) -> dict:
    with open(file_path, encoding="utf-8") as json_file:
        return json.load(json_file)

def build_manufacturer_timeseries(mf_data):
    update_date = mf_data["update_date"]
    mf_data = calculate_mf_sum(mf_data)
    mf_data["date"] = pd.to_datetime(update_date).floor("D")
    START_DATE = "2021-07-02"
    mf_ts = pd.read_json(MAIN_URL + "/vaccination/vaccine-manufacturer-timeseries.json")
    mf_data = pd.DataFrame([mf_data])
    mf_data["date"] = pd.to_datetime(mf_data["date"])
    mf_ts["date"] = pd.to_datetime(mf_ts["date"])

    mf_ts.set_index("date", inplace=True)
    mf_data.set_index("date", inplace=True)
    mf_ts = mf_ts.combine_first(mf_data)
    mf_ts = mf_ts.fillna(0)
    mf_ts = mf_ts.asfreq(freq="D")
    mf_ts.reset_index(inplace=True)
    mf_ts.fillna(method="ffill", inplace=True)
    old_df = mf_ts[mf_ts["date"] < START_DATE].copy()
    new_df = mf_ts[mf_ts["date"] >= START_DATE].copy()

    new_df["AstraZeneca_rate"] = new_df["AstraZeneca"].diff()
    new_df["Sinopharm_rate"] = new_df["Sinopharm"].diff()
    new_df["Sinovac_rate"] = new_df["Sinovac"].diff()
    new_df["JnJ_rate"] = new_df["Johnson & Johnson"].diff()
    new_df["Pfizer_rate"] = new_df["Pfizer"].diff()
    mf_ts = old_df.append(new_df, ignore_index=True)
    mf_ts = mf_ts.fillna(0)
    return mf_ts


def calculate_national_sum(data):
    first_dose = 0
    second_dose = 0
    third_dose = 0
    for province in data["data"]:
        first_dose += province["total_1st_dose"]
        second_dose += province["total_2nd_dose"]
        third_dose += province["total_3rd_dose"]
    return {
        "first_dose": first_dose,
        "second_dose": second_dose,
        "third_dose": third_dose,
        "total_doses": first_dose+second_dose+third_dose,
    }


def calculate_mf_sum(data):
    AstraZeneca = 0
    Sinovac = 0
    Sinopharm = 0
    JnJ = 0
    Pfizer = 0
    for province in data["data"]:
        AstraZeneca += province["AstraZeneca"]
        Sinovac += province["Sinovac"]
        Sinopharm += province["Sinopharm"]
        JnJ += province["Johnson & Johnson"]
        Pfizer += province["Pfizer"]
    return {
        "AstraZeneca": AstraZeneca,
        "Sinovac": Sinovac,
        "Sinopharm": Sinopharm,
        "Johnson & Johnson": JnJ,
        "Pfizer": Pfizer,
    }


def get_delivery_data():
    delivery_data = pd.read_csv(
        "https://raw.githubusercontent.com/wiki/djay/covidthailand/vac_timeline.csv"
    )
    delivery_data["Date"] = pd.to_datetime(delivery_data["Date"])
    delivery_data = delivery_data.rename(
        columns={
            "Date": "date",
            "Vac Given 1 Cum": "first_dose",
            "Vac Given 2 Cum": "second_dose",
        }
    )
    delivery_data["total_doses"] = (
        delivery_data["first_dose"] + delivery_data["second_dose"]
    )
    delivery_data = delivery_data[["date", "first_dose", "second_dose", "total_doses"]]


def calculate_rate(df):
    # Fill empty dates with previous values
    df = df.asfreq(freq="D")
    
    df = df.fillna(0)
    df["total_doses"] = df["total_doses"].replace(to_replace=0, method="ffill")
    
    df["first_dose"] = df["first_dose"].replace(to_replace=0, method="ffill")
    df["second_dose"] = df["second_dose"].replace(to_replace=0, method="ffill")
    df["third_dose"] = df["third_dose"].replace(to_replace=0, method="ffill")
    df["daily_vaccinations"] = df["total_doses"].diff()
    return df

if __name__ == "__main__":
    moh_prompt_data = json_load("../dataset/provincial-vaccination.json")
    print(moh_prompt_data["update_date"])
    national_sum = calculate_national_sum(moh_prompt_data)
    vaccination_timeseries = pd.read_json(
        MAIN_URL + "/vaccination/national-vaccination-timeseries.json"
    )
    vaccination_timeseries["date"] = pd.to_datetime(vaccination_timeseries["date"])
    national_sum["date"] = pd.to_datetime(moh_prompt_data["update_date"]).floor("D")
    
    today_data = pd.DataFrame([national_sum])
    today_data = today_data.set_index("date")
    vaccination_timeseries = vaccination_timeseries.set_index("date")
    vaccination_timeseries = vaccination_timeseries.combine_first(today_data)    
    vaccination_timeseries = calculate_rate(vaccination_timeseries)
    vaccination_timeseries = vaccination_timeseries.reset_index()
    vaccination_timeseries["date"] = vaccination_timeseries["date"].dt.strftime(
        "%Y-%m-%d"
    )
    vaccination_timeseries.to_json(
        "../dataset/national-vaccination-timeseries.json",
        orient="records",
        indent=2,
        force_ascii=False,
    )
    
    mf_data = json_load("../dataset/provincial-vaccination-by-manufacturer.json")

    manufacturer_timeseries = build_manufacturer_timeseries(mf_data)
    manufacturer_timeseries["date"] = manufacturer_timeseries["date"].dt.strftime(
        "%Y-%m-%d"
    )

    manufacturer_timeseries = manufacturer_timeseries[
        [
            "date",
            "AstraZeneca",
            "AstraZeneca_rate",
            "Johnson & Johnson",
            "JnJ_rate",
            "Sinopharm",
            "Sinopharm_rate",
            "Sinovac",
            "Sinovac_rate",
            "Pfizer",
            "Pfizer_rate"
        ]
    ]

    manufacturer_timeseries.to_json(
        "../dataset/vaccine-manufacturer-timeseries.json",
        orient="records",
        indent=2,
        force_ascii=False,
    )
    manufacturer_timeseries.to_csv(
        "../dataset/vaccine-manufacturer-timeseries.csv"
    )
    print("success")