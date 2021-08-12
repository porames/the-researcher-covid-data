#%%
import json
from numpy import disp
import pandas as pd
import os

from pandas.core.frame import DataFrame

#%%
def json_load(file_path: str) -> dict:
    with open(file_path, encoding="utf-8") as json_file:
        return json.load(json_file)


if __name__ == '__main__':
    car_to_or = {
        1: "1st",
        2: "2nd",
        3: "3rd",
    }
    vaccination_data_dir = "../wiki/vaccination/"
    first_dose = json_load(os.path.join(vaccination_data_dir, "1st-dose-provincial-vaccination.json"))
    second_dose = json_load(os.path.join(vaccination_data_dir, "2nd-dose-provincial-vaccination.json"))
    third_dose = json_load(os.path.join(vaccination_data_dir, "3rd-dose-provincial-vaccination.json"))
    if len({first_dose["update_date"], second_dose["update_date"], third_dose["update_date"]}) != 1:
        print("Update date not matched!")
        raise AssertionError

    df_first_dose = pd.DataFrame(first_dose["data"]).set_index("province").T
    df_second_dose = pd.DataFrame(second_dose["data"]).set_index("province").T
    df_third_dose = pd.DataFrame(third_dose["data"]).set_index("province").T
    
    combined_data = {
        "update_date": first_dose["update_date"],
        "data": [
            {
                "province": province,
                "over_60_1st_dose": int(df_first_dose[province]["over_60_1st_dose"]),
                "total_1st_dose": int(df_first_dose[province]["total_1st_dose"]),
                "total_2nd_dose": int(df_second_dose[province]["total_2nd_dose"]),
                "total_3rd_dose": int(df_third_dose[province]["total_3rd_dose"]),
            }
            for province in sorted(df_first_dose.columns)
        ],
    }

    df_combined = pd.DataFrame(combined_data["data"])
    df_combined["date"] = combined_data["update_date"]
#%%
    out_dir = "../dataset/"
    os.makedirs(out_dir, exist_ok=True) # Make sure that we ABSOLUTELY have target dir
    df_combined.to_csv(f"{out_dir}provincial-vaccination.csv")
    with open(os.path.join(out_dir, "provincial-vaccination.json"), "w+", encoding="utf-8") as fout:
        json.dump(combined_data, fout, ensure_ascii=False, indent=2)

# %%
