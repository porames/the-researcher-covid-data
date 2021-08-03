import pandas as pd
import os

if __name__ == '__main__':
    MAIN_URL="https://raw.githubusercontent.com/wiki/porames/the-researcher-covid-data"
    df=pd.read_json(MAIN_URL+"/vaccination/national-vaccination-timeseries.json")
    print(df)