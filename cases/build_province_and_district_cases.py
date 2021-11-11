import os
import time
from util import find_similar_word, json_dump
import build_province_deaths
import pandas as pd
import json
import datetime
import re

XLS_URL_LATEST = "https://data.go.th/dataset/8a956917-436d-4afd-a2d4-59e4dd8e906e/resource/1c2f6045-c600-410a-995c-a37a88594ab4/download/confirmed-cases-since-271064.xlsx"

DEATHS_URL = "https://github.com/djay/covidthailand/wiki/cases_by_province.csv"

district_data_14days_out_path = "../dataset/district-cases-data-14days.json"
province_data_14days_out_path = "../dataset/province-cases-data-14days.json"
province_data_21days_out_path = "../dataset/province-cases-data-21days.json"

PROVINCE_MAP_PATH = "../geo-data/th-map-provinces-points.geojson"
DISTRICT_MAP_PATH = "../geo-data/th-map-amphoes-points.geojson"
CENSUS_DATA_PATH = "../population-data/th-census-data.json"

PROVINCE_IDS = {
    feature["properties"]["PROV_NAMT"]: feature["properties"]["PROV_CODE"]
    for feature in json.load(open(PROVINCE_MAP_PATH, encoding="utf-8"))["features"]
}
PROVINCE_NAMES = set(PROVINCE_IDS.keys())


def main():
    os.makedirs("../dataset", exist_ok=True)

    # Confirmed case from 2020-01-12 to 2021-08-11
    df = pd.read_csv("confirmed-cases-2020-01-12-2021-08-11.zip", compression="zip")
    df["announce_date"] = pd.to_datetime(df["announce_date"], format="%d/%m/%Y")
    # Confirmed case from 2021-08-12 to 2021-10-26
    df2 = pd.read_csv("confirmed-cases-2021-08-12-2021-10-26.zip", compression="zip")
    df2["announce_date"] = pd.to_datetime(df2["announce_date"], format="%d/%m/%Y")
    # Format Date for CSV only

    # Latest Dataset
    print("Downloading Latest Provincial Dataset")
    start = time.time()
    df_latest = pd.read_excel(XLS_URL_LATEST, header=None, names=df.columns)
    print("Downloaded Latest Provincial Dataset took", time.time() - start, "seconds")

    df = pd.concat([df, df2, df_latest])

    # Drop unused (By the site) column
    df = df.drop(
        [
            "No.",
            "Notified date",
            "nationality",
            "sex",
            "age",
            "risk",
            "Unit",
        ],
        axis=1,
    )
    print(df.info())

    # Remove data with unknown province
    df['province_of_onset'].fillna(df['province_of_isolation'], inplace=True)
    df = df.fillna(0)
    df = df[df["province_of_onset"] != 0]
    df = df.drop("province_of_isolation", axis=1)
    # Correct province name typo
    df_invalid = df[(~df["province_of_onset"].isin(PROVINCE_NAMES))]
    # Regex for some special cases
    regex_ay = re.compile(r"^(อยุธยา|อยุธนา)$")
    df_invalid["province_of_onset"].replace(regex_ay, "พระนครศรีอยุธยา", inplace=True)
    regex_bkk = re.compile(r"^(กทม|กทม.)$")
    df_invalid["province_of_onset"].replace(regex_bkk, "กรุงเทพมหานคร", inplace=True)
    # Replace by finding most similar province
    df_invalid_correted = df_invalid["province_of_onset"].apply(
        lambda pro: find_similar_word(pro, PROVINCE_NAMES)
    )
    df.update(df_invalid_correted)

    # Print uncorrectable province
    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        df_uncorreted = df[~df["province_of_onset"].isin(PROVINCE_NAMES)]
        print(df_uncorreted)
        print(df_uncorreted.info())

    # Filter from start date
    end = df.tail(1)["announce_date"].iloc[0]
    # 21 days for build_province_graph.py
    start = end - datetime.timedelta(days=21)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    df = df[(df["announce_date"] > start) & (df["announce_date"] <= end)]

    # Change อำเภอ เมือง -> อำเภอ เมือง + จังหวัด
    mueng_df = df[df.district_of_onset == "เมือง"]
    df.district_of_onset.update(mueng_df.district_of_onset + mueng_df.province_of_onset)

    # Load province and district name in to sets
    json_data = json.load(open(DISTRICT_MAP_PATH, encoding="utf-8"))
    district_and_province_names = pd.DataFrame(
        i["properties"] for i in json_data["features"]
    )[["fid", "P_NAME_T", "A_NAME_T"]]
    district_and_province_names = district_and_province_names.rename(
        columns={"fid": "id", "P_NAME_T": "province", "A_NAME_T": "district"}
    )
    province_names = district_and_province_names["province"]
    district_names = district_and_province_names["district"]

    # Filter by district name (Select only 14 days)
    df_14days = df[
        (df["announce_date"] > end - datetime.timedelta(days=14))
        & (df["announce_date"] <= end)
        ]
    df_no_date = df_14days.drop("announce_date", axis=1).rename(
        columns={"province_of_onset": "province", "district_of_onset": "district"}
    )

    df_filtered_by_district = df_no_date[df_no_date.district.isin(district_names)]
    # Count values by district
    df_district_case_14days = (
        df_filtered_by_district.value_counts(sort=True)
            .to_frame(name="caseCount")
            .reset_index()
    )
    df_district_case_14days = df_district_case_14days.rename(
        columns={"province_of_onset": "province", "district_of_onset": "district"}
    )

    # Merge only valid district and province pair
    df_district_case_14days_with_id = district_and_province_names.merge(
        df_district_case_14days, how="left", on=["province", "district"]
    )
    df_district_case_14days_with_id = df_district_case_14days_with_id.rename(
        columns={"district": "name"}
    )
    df_district_case_14days_with_id = df_district_case_14days_with_id.fillna(0)
    df_district_case_14days_with_id["caseCount"] = df_district_case_14days_with_id[
        "caseCount"
    ].astype(int)

    # Write df to json
    df_district_case_14days_with_id.to_json(
        district_data_14days_out_path, orient="records", indent=2, force_ascii=False
    )

    # Start generating provincial data
    # Filter by province name
    df_no_district = df.drop("district_of_onset", axis=1)

    df_filtered_by_province = df_no_district[
        df_no_district.province_of_onset.isin(province_names)
    ]

    # Count values by provinces by date (count 21 days cases as well)
    province_cases_each_day = pd.crosstab(
        df_filtered_by_province.announce_date, df_filtered_by_province.province_of_onset
    ).to_dict()
    # Count values by provinces (for all 14 days)
    df_filtered_by_province_14days = df_filtered_by_province[
        df_filtered_by_province["announce_date"] > (end - datetime.timedelta(days=14))
        ]
    province_cases_14days = df_filtered_by_province_14days.drop(
        "announce_date", axis=1
    ).value_counts(sort=True)
    # Get census data
    province_population = {
        i["province"]: i["population"]
        for i in json.load(open(CENSUS_DATA_PATH, encoding="utf-8"))
    }

    # Deaths by province
    print("Downloading Deaths Dataset")
    start = time.time()
    df_deaths = pd.read_csv(DEATHS_URL)
    print("Downloaded Deaths Dataset took:", time.time() - start, "seconds")

    province_deaths_each_day = build_province_deaths.get_province_deaths(
        deaths_df=df_deaths
    ).to_dict()
    province_deaths_each_day_21days = build_province_deaths.get_province_deaths(
        deaths_df=df_deaths, days=21
    ).to_dict()

    # Create a dict with all data combined
    province_cases_each_day_with_total = []
    province_cases_each_day_21days = []
    for name, cases in province_cases_each_day.items():
        deaths_by_date = province_deaths_each_day[name]
        deaths_count = sum(deaths_by_date.values())
        province_cases_each_day_with_total.append(
            {
                "name": name,
                "cases": {
                    dto.isoformat(): caseCount
                    for dto, caseCount in cases.items()
                    if dto > (end - datetime.timedelta(days=14))
                },
                "id": int(PROVINCE_IDS[name]),
                "caseCount": int(province_cases_14days[name]),
                "cases-per-100k": (int(province_cases_14days[name]) * 100000)
                                  // province_population[name],
                "deaths": deaths_by_date,
                "deathsCount": deaths_count,
                "deaths-per-100k": round(
                    deaths_count * 100000 / province_population[name], 2
                ),
            }
        )
        province_cases_each_day_21days.append(
            {
                "name": name,
                "cases": {dto.isoformat(): caseCount for dto, caseCount in cases.items()},
                "deaths": province_deaths_each_day_21days[name],
            }
        )

    # Write province data to json file
    json_dump(province_cases_each_day_with_total, province_data_14days_out_path)
    json_dump(province_cases_each_day_21days, province_data_21days_out_path)

    print("Built province and district cases")


if __name__ == "__main__":
    main()
