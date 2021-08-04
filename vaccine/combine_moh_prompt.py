import json
import pandas as pd
import os

from pandas.core.frame import DataFrame


def json_load(file_path: str) -> dict:
    with open(file_path, encoding="utf-8") as json_file:
        return json.load(json_file)


if __name__ == '__main__':
    vaccination_data_dir = "../wiki/vaccination/"
    first_dose = json_load(os.path.join(vaccination_data_dir, "1st-dose-provincial-vaccination.json"))
    second_dose = json_load(os.path.join(vaccination_data_dir, "2nd-dose-provincial-vaccination.json"))
    third_dose = json_load(os.path.join(vaccination_data_dir, "3rd-dose-provincial-vaccination.json"))
    population_data = json_load("../population-data/th-census-with-hidden-pop.json")
    age_group_data = json_load("../population-data/th-censusage-group.json")
    if len({first_dose["update_date"], second_dose["update_date"], third_dose["update_date"]}) != 1:
        print("Update date not matched!")
        raise AssertionError

    df_first_dose = pd.DataFrame(first_dose["data"]).set_index("province").T
    df_second_dose = pd.DataFrame(second_dose["data"]).set_index("province").T
    df_third_dose = pd.DataFrame(third_dose["data"]).set_index("province").T
    df_population = pd.DataFrame(population_data)
    df_age_group = pd.DataFrame(age_group_data)
    manufacturer = ["AstraZeneca", "Johnson & Johnson", "Sinopharm", "Sinovac", "total_doses"]
    df_all_dose = df_first_dose.loc[manufacturer, :] + df_second_dose.loc[manufacturer, :] + df_third_dose.loc[manufacturer, :]
    
    combined_data = {
        "update_date": first_dose["update_date"],
        "data": [
            {
                "province": province,
                "1st_dose": df_first_dose[province].to_dict(),
                "2nd_dose": df_second_dose[province].to_dict(),
                "3rd_dose": df_third_dose[province].to_dict(),
                "all_dose": df_all_dose[province].to_dict(),
                "population_data": population_data[population_data["province"] == province][["population", "estimated_living_population"]]
            }
            for province in sorted(df_first_dose.columns)
        ],
    }

    out_dir = "../dataset"
    os.makedirs(out_dir, exist_ok=True) # Make sure that we ABSOLUTELY have target dir
    with open(os.path.join(out_dir, "provincial-vaccination.json"), "w+", encoding="utf-8") as fout:
        json.dump(combined_data, fout, ensure_ascii=False, indent=2)
