import pandas as pd
import json

MAIN_URL = "https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data"


def json_load(file_path: str) -> dict:
    with open(file_path, encoding="utf-8") as json_file:
        return json.load(json_file)


def build_manufacturer_timeseries(manufacturer_data: dict) -> pd.DataFrame:
    update_date = manufacturer_data["update_date"]
    manufacturer_data = calculate_mf_sum(manufacturer_data)
    manufacturer_data["date"] = pd.to_datetime(update_date).floor("D")
    START_DATE = "2021-07-02"
    mf_ts = pd.read_json(MAIN_URL + "/vaccination/vaccine-manufacturer-timeseries.json")
    manufacturer_data = pd.DataFrame([manufacturer_data])
    manufacturer_data["date"] = pd.to_datetime(manufacturer_data["date"])
    mf_ts["date"] = pd.to_datetime(mf_ts["date"])

    mf_ts.set_index("date", inplace=True)
    manufacturer_data.set_index("date", inplace=True)
    mf_ts = mf_ts.combine_first(manufacturer_data)
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


def calculate_national_sum_today(data: dict) -> pd.DataFrame:
    df = pd.DataFrame(data["data"])
    today_national_sum = pd.DataFrame(index=[pd.to_datetime(data["update_date"]).floor("D")], data={
        "first_dose": df["total_1st_dose"].to_numpy().sum(),
        "second_dose": df["total_2nd_dose"].to_numpy().sum(),
        "third_dose": df["total_3rd_dose"].to_numpy().sum(),
        "total_doses": df[["total_1st_dose", "total_2nd_dose", "total_3rd_dose"]].to_numpy().sum(),
    })  # Numpy sum is faster (even faster than pandas sum)
    today_national_sum.index.name = "date"
    return today_national_sum


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


if __name__ == "__main__":
    # Parse today scraped data
    moh_prompt_data = json_load("../dataset/provincial-vaccination.json")
    print(moh_prompt_data["update_date"])
    today_data = calculate_national_sum_today(moh_prompt_data)

    # Get Historical Data
    vaccination_timeseries = pd.read_json(MAIN_URL + "/vaccination/national-vaccination-timeseries.json")
    vaccination_timeseries["date"] = pd.to_datetime(vaccination_timeseries["date"])
    vaccination_timeseries = vaccination_timeseries.set_index("date")

    # Add today data to timeseries
    vaccination_timeseries = vaccination_timeseries.combine_first(today_data).asfreq("D").fillna(0)
    dose_col = ["total_doses", "first_dose", "second_dose", "third_dose"]
    # Fill missing data with previous values
    vaccination_timeseries[dose_col] = vaccination_timeseries[dose_col].replace(to_replace=0, method="ffill")
    vaccination_timeseries[dose_col] = vaccination_timeseries[dose_col].astype(int)

    # Calculate daily vaccinations
    vaccination_timeseries["daily_vaccinations"] = vaccination_timeseries["total_doses"].diff().fillna(0).astype(int)
    vaccination_timeseries = vaccination_timeseries.reset_index()
    vaccination_timeseries["date"] = vaccination_timeseries["date"].dt.strftime("%Y-%m-%d")

    # Save data as json and csv
    vaccination_timeseries.to_json(
        "../dataset/national-vaccination-timeseries.json",
        orient="records",
        indent=2,
        force_ascii=False,
    )
    vaccination_timeseries.to_csv("../dataset/national-vaccination-timeseries.csv", index=False)

    mf_data = json_load("../wiki/vaccination/provincial-vaccination-by-manufacturer.json")

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
