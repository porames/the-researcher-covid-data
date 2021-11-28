import pandas as pd
import json

MAIN_URL = "https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data"


def json_load(file_path: str) -> dict:
    with open(file_path, encoding="utf-8") as json_file:
        return json.load(json_file)


def calculate_national_sum_today(data: dict) -> pd.DataFrame:
    df = pd.DataFrame(data["data"])
    today_national_sum = pd.DataFrame(index=[0], data={
        "date": pd.to_datetime(data["update_date"]).floor("D"),
        "first_dose": df["total_1st_dose"].to_numpy().sum(),
        "second_dose": df["total_2nd_dose"].to_numpy().sum(),
        "third_dose": df["total_3rd_dose"].to_numpy().sum(),
        "total_doses": df[["total_1st_dose", "total_2nd_dose", "total_3rd_dose"]].to_numpy().sum(),
    })  # Numpy sum is faster (even faster than pandas sum)
    return today_national_sum


if __name__ == "__main__":
    # Parse today scraped data
    moh_prompt_data = json_load("../dataset/provincial-vaccination.json")
    print(moh_prompt_data["update_date"])
    today_data = calculate_national_sum_today(moh_prompt_data)

    # Get Historical Data
    vaccination_timeseries = pd.read_json(MAIN_URL + "/vaccination/national-vaccination-timeseries.json")
    vaccination_timeseries["date"] = pd.to_datetime(vaccination_timeseries["date"])

    # Add today data to timeseries
    dose_col = ["total_doses", "first_dose", "second_dose", "third_dose"]
    vaccination_timeseries = vaccination_timeseries.merge(today_data, how="outer").drop_duplicates(subset=["date"], keep="last")
    vaccination_timeseries.set_index("date", inplace=True)
    # Fill missing data with previous values
    vaccination_timeseries[dose_col] = vaccination_timeseries[dose_col].replace(to_replace=0, method="ffill")
    vaccination_timeseries[dose_col] = vaccination_timeseries[dose_col].astype(int)

    # Calculate daily vaccinations
    vaccination_timeseries["daily_vaccinations"] = vaccination_timeseries["total_doses"].diff().fillna(0).astype(int)
    vaccination_timeseries = vaccination_timeseries.reset_index()
    vaccination_timeseries["date"] = vaccination_timeseries["date"].dt.strftime("%Y-%m-%d")

    # Save data as json and csv
    vaccination_timeseries.to_json(
        "./dataset/national-vaccination-timeseries.json",
        orient="records",
        indent=2,
        force_ascii=False,
    )
    vaccination_timeseries.to_csv("./dataset/national-vaccination-timeseries.csv", index=False)
    print("Processed National Timeseries")
