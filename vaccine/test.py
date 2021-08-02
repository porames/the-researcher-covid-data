import requests

if __name__ == "__main__":
    req = requests.get("https://app.powerbi.com/view?r=eyJrIjoiOGFhYzhhMTUtMjBiNS00MWZiLTg4MmUtZTczZGEyMzIzMWYyIiwidCI6ImY3MjkwODU5LTIyNzAtNDc4ZS1iOTc3LTdmZTAzNTE0ZGQ4YiIsImMiOjEwfQ%3D%3D")
    print(req.status_code)
    print(req.text)
    with open("test.txt", "w+") as fout:
        fout.write(req.text)