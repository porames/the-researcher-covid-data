#%%
from numpy import disp
import pandas as pd
import os
import json

#%%


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
        total_doses += province["all_dose"]["total-dose"]
        first_dose += province["1st_dose"]["total-dose"]
        second_dose += province["2nd_dose"]["total-dose"]
        third_dose += province["3rd_dose"]["total-dose"]

        for mf in manufacturer.keys():
            manufacturer[mf] += province["all_dose"][mf]
    return {
        "manufacturer": manufacturer,
        "first_dose": first_dose,
        "second_dose": second_dose,
        "third_dose": third_dose,
        "total_doses": total_doses,
    }


if __name__ == "__main__":
    MAIN_URL = (
        "https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data"
    )
    moh_prompt_data = json_load("../dataset/provincial-vaccination.json")
    print(moh_prompt_data["update_date"])
    national_sum = calculate_national_sum(moh_prompt_data)
    print(national_sum)

    # %%

    delivery_data = pd.read_csv(
        "https://raw.githubusercontent.com/wiki/djay/covidthailand/vac_timeline.csv"
    )

    vaccination_timeseries = pd.read_json(
        MAIN_URL + "/vaccination/national-vaccination-timeseries.json"
    )
    vaccination_timeseries["date"] = pd.to_datetime(vaccination_timeseries["date"])
    moh_prompt_data["update_date"] = pd.to_datetime(moh_prompt_data["update_date"])
    delivery_data["Date"] = pd.to_datetime(delivery_data["Date"])

    # Add data from moh prompt

    # Add delivery data from DDC PDF report
    delivery_latest_update = delivery_data.iloc[-1]["Date"]
    moh_prompt_latest_update = moh_prompt_data["update_date"][0]
    delivery_data = delivery_data[
        delivery_data["Date"] > vaccination_timeseries.iloc[-1]["date"]
    ]


# %%
