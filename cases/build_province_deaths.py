import pandas as pd
import datetime
import json
import time

PROVINCE_MAP_PATH = "../geo-data/th-map-provinces-points.geojson"

PROVINCE_EN_TO_TH = {feature["properties"]["PROV_NAME"].replace(" ", ""):feature["properties"]["PROV_NAMT"] for feature in
               json.load(open(PROVINCE_MAP_PATH, encoding="utf-8"))["features"]}


def province_en_to_th(province_en : str, province_dict : dict) -> str:
    province_en_clean = province_en.upper().replace(" ","")
    if province_en_clean in province_dict : 
        return province_dict[province_en_clean]
    else :
        print("Invalid Province:", province_en_clean)
        return province_en_clean

def get_province_deaths(deaths_df : pd.DataFrame, days : int = 14, province_dict : dict = PROVINCE_EN_TO_TH) -> pd.DataFrame:
    # Select column and filter to end (14 days)
    df = deaths_df[["Date", "Province", "Deaths"]]
    df.fillna(0, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    end = df["Date"].iloc[-1]
    df = df[df["Date"] > end - datetime.timedelta(days=days)]
    df["Date"] = df["Date"].apply(lambda dto : dto.isoformat())
    
    df["Province"] = df["Province"].apply(lambda province : province_en_to_th(province, province_dict=province_dict))
    df = df[df["Province"].isin(province_dict.values())]

    df_grouped_by_province = df.pivot_table(index="Date", columns="Province", values="Deaths", fill_value=0)
    return df_grouped_by_province
    

if __name__ == "__main__":
    DEATHS_URL = "https://github.com/djay/covidthailand/wiki/cases_by_province.csv"
    DEATH_DATA_14DAYS_OUT_PATH = "../wiki/dataset/province-deaths-data-14days.json"
    CENSUS_DATA_PATH = "../population-data/th-census-data.json"

    province_population = {i["province"]: i["population"] for i in
                           json.load(open(CENSUS_DATA_PATH, encoding="utf-8"))}
    
    print("Downloading Deaths Dataset")
    start = time.time()
    df_deaths = pd.read_csv(DEATHS_URL)
    print("Downloaded Deaths Dataset took:", time.time()-start, "seconds")

    death_by_province_14days = []
    for province, death_by_date in get_province_deaths(df_deaths).to_dict().items() :
        deaths_count = sum(death_by_date.values())
        death_by_province_14days.append({
            "name": province,
            "deaths": death_by_date,
            "deathsCount": deaths_count,
            "deaths-per-100k" : round(deaths_count * 100000 / province_population[province], 2)
        })
    
    with open(DEATH_DATA_14DAYS_OUT_PATH, "w+", encoding="utf-8") as fout:
        json.dump(death_by_province_14days, fout, ensure_ascii=False, indent=2)