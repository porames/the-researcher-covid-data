import pandas as pd


def interpolate_national_timeseries():
    df = pd.read_csv("../the-researcher-covid-data.wiki/vaccination/national-vaccination-timeseries.csv")
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df_reindexed = df.reindex(pd.date_range(start=df.index.min(), end=df.index.max(), freq="1D"))
    df_interpolated = df_reindexed.interpolate(method='linear')
    df_interpolated.loc[pd.to_datetime("2021-11-21"):pd.to_datetime("2021-11-24"),
    "data_anomaly"] = "ช้อมูลมาจากการประมาณ เนื่องระบบดึงข้อมูลขัดข้อง"
    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        print(df_reindexed.loc[pd.to_datetime("2021-11-20"):pd.to_datetime("2021-11-27")])
        print(df_interpolated.loc[pd.to_datetime("2021-11-20"):pd.to_datetime("2021-11-27")])
    df_interpolated = df_interpolated.reset_index()
    df_interpolated.rename(columns={"index": "date"}, inplace=True)
    df_interpolated[["daily_vaccinations", "first_dose", "second_dose", "third_dose", "total_doses"]] = df_interpolated[
        ["daily_vaccinations", "first_dose", "second_dose", "third_dose", "total_doses"]].astype(int)

    df_interpolated["date"] = df_interpolated["date"].dt.strftime("%Y-%m-%d")
    df_interpolated.to_json(
        "../dataset/national-vaccination-timeseries.json",
        orient="records",
        indent=2,
        force_ascii=False,
    )
    df_interpolated.to_csv("../dataset/national-vaccination-timeseries.csv",
                           index=False)


if __name__ == '__main__':
    interpolate_national_timeseries()
