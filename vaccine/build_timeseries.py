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


def calculate_national_sum(data):
    total_doses = 0
    first_dose = 0
    second_dose = 0
    third_dose = 0
    manufacturer = {
        "AstraZeneca": 0,
        "Sinovac": 0,
        "Sinopharm": 0,
        "Johnson & Johnson": 0,
    }
    for province in data["data"]:
        total_doses += province["all_dose"]["total_doses"]
        first_dose += province["1st_dose"]["total_doses"]
        second_dose += province["2nd_dose"]["total_doses"]
        third_dose += province["3rd_dose"]["total_doses"]

        for mf in manufacturer.keys():
            manufacturer[mf] += province["all_dose"][mf]
    return {
        "manufacturer": manufacturer,
        "first_dose": first_dose,
        "second_dose": second_dose,
        "third_dose": third_dose,
        "total_doses": total_doses,
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
    df["total_doses"] = df["total_doses"].replace(to_replace=0, method="ffill")
    df["first_dose"] = df["first_dose"].replace(to_replace=0, method="ffill")
    df["second_dose"] = df["second_dose"].replace(to_replace=0, method="ffill")
    df["daily_vaccinations"] = df["total_doses"].diff()
    return df


# %%
def build_manufacturer_timeseries(mf_data):
    START_DATE = "2021-07-02"
    mf_ts = pd.read_json(MAIN_URL + "/vaccination/vaccine-manufacturer-timeseries.json")
    mf_ts["date"] = pd.to_datetime(mf_ts["date"])

    if len(mf_ts[mf_ts["date"] >= pd.to_datetime(mf_data["date"]).floor("D")]) == 0:
        mf_ts = mf_ts.append(mf_data, ignore_index=True)
        mf_ts["date"] = pd.to_datetime(mf_ts["date"])
        mf_ts.set_index("date", inplace=True)
        mf_ts = mf_ts.asfreq(freq="D")
        mf_ts.reset_index(inplace=True)
        mf_ts.fillna(method="ffill", inplace=True)
        old_df = mf_ts[mf_ts["date"] < START_DATE].copy()
        new_df = mf_ts[mf_ts["date"] >= START_DATE].copy()
        new_df["AstraZeneca_rate"] = new_df["AstraZeneca"].diff()
        new_df["Sinopharm_rate"] = new_df["Sinopharm"].diff()
        new_df["Sinovac_rate"] = new_df["Sinovac"].diff()
        new_df["JnJ_rate"] = new_df["Johnson & Johnson"].diff()
        mf_ts = old_df.append(new_df, ignore_index=True)
        mf_ts = mf_ts.fillna(0)
    return mf_ts


#%%
if __name__ == "__main__":

    moh_prompt_data = json_load("../dataset/provincial-vaccination.json")
    print(moh_prompt_data["update_date"])
    national_sum = calculate_national_sum(moh_prompt_data)
    vaccination_timeseries = pd.read_json(
        MAIN_URL + "/vaccination/national-vaccination-timeseries.json"
    )
    vaccination_timeseries["date"] = pd.to_datetime(vaccination_timeseries["date"])

    # Add data from moh prompt
    vaccination_timeseries = vaccination_timeseries[
        ["date", "total_doses", "first_dose", "second_dose", "data_anomaly"]
    ]

    today_data = vaccination_timeseries[
        vaccination_timeseries["date"]
        == pd.to_datetime(moh_prompt_data["update_date"]).floor("D")
    ]

    if len(today_data) == 0:
        vaccination_timeseries = vaccination_timeseries.append(
            {
                "date": pd.to_datetime(moh_prompt_data["update_date"]).floor("D"),
                "total_doses": national_sum["total_doses"],
                "first_dose": national_sum["first_dose"],
                "second_dose": national_sum["second_dose"],
                "third_dose": national_sum["third_dose"],
            },
            ignore_index=True,
        )
    else:
        vaccination_timeseries.loc[
            vaccination_timeseries["date"]
            == pd.to_datetime(moh_prompt_data["update_date"]).floor("D")
        ]["total_doses"] = national_sum["total_doses"]
        vaccination_timeseries.loc[
            vaccination_timeseries["date"]
            == pd.to_datetime(moh_prompt_data["update_date"]).floor("D")
        ]["first_dose"] = national_sum["first_dose"]
        vaccination_timeseries.loc[
            vaccination_timeseries["date"]
            == pd.to_datetime(moh_prompt_data["update_date"]).floor("D")
        ]["second_dose"] = national_sum["second_dose"]
        vaccination_timeseries.loc[
            vaccination_timeseries["date"]
            == pd.to_datetime(moh_prompt_data["update_date"]).floor("D")
        ]["third_dose"] = national_sum["third_dose"]

    vaccination_timeseries = calculate_rate(vaccination_timeseries)
    vaccination_timeseries["date"] = vaccination_timeseries["date"].dt.strftime(
        "%Y-%m-%d"
    )
    vaccination_timeseries.to_json(
        "../dataset/national-vaccination-timeseries.json",
        orient="records",
        indent=2,
        force_ascii=False,
    )

    mf_data = national_sum["manufacturer"]
    mf_data["date"] = pd.to_datetime(moh_prompt_data["update_date"]).floor("D")
    mf_data
    manufacturer_timeseries = build_manufacturer_timeseries(mf_data)
    manufacturer_timeseries["date"] = manufacturer_timeseries["date"].dt.strftime(
        "%Y-%m-%d"
    )
    manufacturer_timeseries.to_json(
        "../dataset/vaccine-manufacturer-timeseries.json",
        orient="records",
        indent=2,
        force_ascii=False,
    )
    print("success")


# %%

# %%
