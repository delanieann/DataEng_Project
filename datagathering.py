import pandas as pd
import requests, json, os
from datetime import datetime, timedelta

timestamp = datetime.now() - timedelta(days=854)
formatted_timestamp = timestamp.strftime('%Y-%m-%d_%H:%M:%S')
date = timestamp.strftime('%Y-%m-%d')

if not os.path.exists(date):
    os.makedirs(date)


base_url = "https://busdata.cs.pdx.edu/api/getBreadCrumbs?vehicle_id="

bus = pd.read_csv("vehicleGroupsIds.csv")

for bus_id in bus["Whisker"]:
    complete_url = base_url + f"{bus_id}"
    response = requests.get(complete_url)
    if response.status_code != 404:
        file_path = os.path.join(date, f"{bus_id}_{formatted_timestamp}.json")
        with open(file_path, "a") as file:
            file.write(response.text)

