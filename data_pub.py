from google.cloud import pubsub_v1
import pandas as pd
import requests, json
from datetime import datetime

timestamp = datetime.now()
formatted_timestamp = timestamp.strftime('%Y-%m-%d_%H:%M:%S')

count = 0

base_url = "https://busdata.cs.pdx.edu/api/getBreadCrumbs?vehicle_id="

bus = pd.read_csv("vehicleGroupsIds.csv")

project_id = "data-eng-456118"
topic_id = "bus_breadcrumb"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

for bus_id in bus["Whisker"]:
    complete_url = base_url + f"{bus_id}"
    response = requests.get(complete_url)
    if response.status_code != 404:
        # proceed with pub
        data = response.json()
        for item in data: 
            # split up file into individual readings
            data_s = json.dumps(item)
            data_item = data_s.encode("utf-8")
            future = publisher.publish(topic_path, data_item)
            count += 1
    else:
        with open("pub_err.txt", "a") as file:
            file.write(f"{formatted_timestamp}, error: {response.status_code} for {bus_id} \n")

with open("pub_log.txt", "a") as file:
    file.write(f"{formatted_timestamp} logged {count} messages.\n")

