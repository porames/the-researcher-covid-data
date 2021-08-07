from util import json_load, json_dump, get_provinces_name, get_population, get_vaccines, moving_average
import matplotlib.pyplot as plt
import datetime
import os

data = json_load("../wiki/cases/province-cases-data-21days.json")
end = datetime.datetime.fromisoformat(max(data[0]["cases"].keys()))
provinces_name = get_provinces_name(json_load("../geo-data/th-map-provinces-points.geojson"))
population_data = json_load("../population-data/th-census-with-hidden-pop.json")
vaccines_data = json_load("../wiki/vaccination/provincial-vaccination.json")
populations = get_population(population_data)
vaccines = get_vaccines(vaccines_data)

dataset = []
i = 1
out_dir = "../wiki/cases/infection-graphs-build/"
os.makedirs(out_dir, exist_ok=True)  # Make sure that we ABSOLUTELY have target dir
for province in data:
    name = province["name"]
    names = list(province["cases"])
    ys = list(province["cases"].values())
    moving_aves = moving_average(ys)
    fig = plt.gcf()
    plt.cla()
    fig.set_size_inches(10, 5)
    if max(moving_aves[-14:]) < 10:
        plt.ylim(0, 10)
    else:
        plt.ylim(0, max(moving_aves[-14:]) + 0.05 * max(moving_aves[-14:]))
    plt.fill_between(names[-14:], 0, moving_aves[-14:], alpha=0.3, color="#dc3545", zorder=2)
    plt.plot(names[-14:], moving_aves[-14:], color="#dc3545", linewidth=25)
    plt.box(False)
    plt.xticks([])
    plt.yticks([])
    plt.savefig("../wiki/cases/infection-graphs-build/" + str(provinces_name.index(name) + 1) + ".svg", bbox_inches=0,
                transparent=True)

    if moving_aves[-14] > 0:
        change = int((moving_aves[-1] - moving_aves[-14]) * 100 / (moving_aves[-14]))
    else:
        change = int((moving_aves[-1] - 0) * 100 / 1)

    dataset.append({
        "graph_path": str(provinces_name.index(name) + 1) + ".svg",
        "change": change,
        "total_14days": sum(ys[-14:]),
        "province": name,
        "vax_1st_dose_coverage": round((vaccines[name]["total_1st_dose"] / populations[name]) * 100, 2),
        "vax_2nd_dose_coverage": round((vaccines[name]["total_2nd_dose"] / populations[name]) * 100, 2),
        "total_vaccine_doses": vaccines[name]["total_1st_dose"] + vaccines[name]["total_2nd_dose"] + vaccines[name][
            "total_3rd_dose"],
        "population": populations[name],
        "deaths_total_14days": sum(tuple(province["deaths"].values())[-14:])
    })
    i += 1

data = {"dataset": dataset,
        "job": {
            "ran_on": datetime.date.today().strftime("%m/%d/%Y %H:%M"),
            "dataset_updated_on": end.strftime("%m/%d/%Y %H:%M")
        },
        }
json_dump(data, "../wiki/cases/build_job.json")

print("Finished building province graph")
