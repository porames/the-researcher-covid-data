import pandas as pd
import datetime
import os


def main():
    SAVE_PATH = "../dataset/"
    # Get data.go.th COVID-19 test dataset
    url: str = "https://data.go.th/dataset/9f6d900f-f648-451f-8df4-89c676fce1c4/resource/0092046c-db85-4608-b519-ce8af099315e/download/testing_data.csv"
    df = pd.read_csv(url)

    # Select a specific column
    df = df[["Date", "positive", "Total Testing"]]
    # Remove cannot specify date and time and row with nan date
    df = df.drop(0).dropna(subset=["Date"]).reset_index(drop=True)
    # Map datetime to YYYY-MM-DD
    df["Date"] = df["Date"].apply(lambda dto: datetime.datetime.strptime(dto, "%d/%m/%Y").strftime("%Y-%m-%d"))
    df = df[(df['Date'] >= "2021-01-01")]
    df = df.rename(columns={"Date": "date", "Pos": "positive", "Total Testing": "tests"})

    # Write df as json table

    os.makedirs(SAVE_PATH, exist_ok=True)  # Make sure that we ABSOLUTELY have the target dir
    df.to_json("../dataset/testing-data.json", orient="records", indent=2)


if __name__ == '__main__':
    main()
