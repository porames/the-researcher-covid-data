#%%
import pandas as pd
import json
import requests
import os

#%%
YEAR_MONTH = "6406"
CENSUS_AGE_GROUP_OUT_PATH = "../population-data/th-census-age-group.json"

URL = f"https://stat.bora.dopa.go.th/stat/statnew/connectSAPI/stat_forward.php?API=/api/statpophouse/v1/statpop/list?action=21&yymm={YEAR_MONTH}&nat=999&popst=99&yymm=6407"
req = requests.get(URL)
data = req.json()
# %%
age_group = ["<18", "18-40", "40-60", "60-80", ">80"]
population_list = []
population_by_age = {}
for age in range(102):
    male = data[0][f"lsAge{age}"]
    female = data[1][f"lsAge{age}"]
    population_list.append(int(male+female))

population_by_age["<18"] = sum(population_list[0:18])
population_by_age["18-40"] = sum(population_list[18:40])
population_by_age["40-60"] = sum(population_list[40:60])
population_by_age["60-80"] = sum(population_list[60:80])
population_by_age[">80"] = sum(population_list[80:102])

with open(f"../population-data/national-population-age-group.json", "w+") as json_file:
    json.dump(population_by_age, json_file, ensure_ascii=False, indent=2)

# %%
