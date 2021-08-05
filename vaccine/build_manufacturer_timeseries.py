import sys

import pandas as pd
import json

MAIN_URL = "https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data"


def json_load(file_path: str) -> dict:
    with open(file_path, encoding="utf-8") as json_file:
        return json.load(json_file)


def calculate_manufacturer_sum(data: dict) -> pd.DataFrame:
    df = pd.DataFrame(data["data"])
    today_manufacturer_sum = pd.DataFrame(index=[0], data={
        "date": pd.to_datetime(data["update_date"]).floor("D"),
        "AstraZeneca": df["AstraZeneca"].to_numpy().sum(),
        "Sinovac": df["Sinovac"].to_numpy().sum(),
        "Sinopharm": df["Sinopharm"].to_numpy().sum(),
        "Johnson & Johnson": df["Johnson & Johnson"].to_numpy().sum(),
        "Pfizer": df["Pfizer"].to_numpy().sum(),
    })  # Numpy sum is faster (even faster than pandas sum)
    #today_manufacturer_sum.index.name = "date"
    return today_manufacturer_sum


def build_manufacturer_timeseries(manufacturer_data: dict) -> pd.DataFrame:
    manufacturer_data_sum = calculate_manufacturer_sum(manufacturer_data)

    # Historical Manufacturer timeseries
    START_DATE = "2021-07-02"
    timeseries = pd.read_json(MAIN_URL + "/vaccination/vaccine-manufacturer-timeseries.json")
    timeseries["date"] = pd.to_datetime(timeseries["date"])
    timeseries = timeseries.merge(manufacturer_data_sum, how="outer").drop_duplicates(subset=["date"], keep="last")
    timeseries.set_index("date", inplace=True)

    timeseries = timeseries.fillna(0).asfreq(freq="D", method="ffill").reset_index()
    old_df = timeseries[timeseries["date"] < START_DATE].copy()
    new_df = timeseries[timeseries["date"] >= START_DATE].copy()

    # Calculate vaccination rate
    new_df[["AstraZeneca_rate", "Sinovac_rate", "Sinopharm_rate", "JnJ_rate", "Pfizer_rate"]] = \
        new_df[["AstraZeneca", "Sinovac", "Sinopharm", "Johnson & Johnson", "Pfizer"]].diff()

    # Add new data to timeseries
    timeseries = old_df.append(new_df, ignore_index=True).fillna(0)
    # Convert rate to int
    timeseries[["AstraZeneca_rate", "Sinovac_rate", "Sinopharm_rate", "JnJ_rate", "Pfizer_rate"]] = \
        timeseries[["AstraZeneca_rate", "Sinovac_rate", "Sinopharm_rate", "JnJ_rate", "Pfizer_rate"]].astype(int)
    return timeseries


if __name__ == '__main__':
    manufacturer_data = json_load("../wiki/vaccination/provincial-vaccination-by-manufacturer.json")
    print(manufacturer_data["update_date"])

    manufacturer_timeseries = build_manufacturer_timeseries(manufacturer_data)
    manufacturer_timeseries["date"] = manufacturer_timeseries["date"].dt.strftime("%Y-%m-%d")

    # Sort columns name
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

    # Save data as json and csv
    manufacturer_timeseries.to_json(
        "../dataset/vaccine-manufacturer-timeseries.json",
        orient="records",
        indent=2,
        force_ascii=False,
    )
    manufacturer_timeseries.to_csv("../dataset/vaccine-manufacturer-timeseries.csv")
    print("Processed Manufacturer Timeseries")
