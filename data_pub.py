from google.cloud import pubsub_v1
import pandas as pd
import os, requests, json
from concurrent import futures
from datetime import datetime
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = os.path.join("data-eng-456118-701fc22fd16c.json")
project_id = "data-eng-456118"
topic_id = "bus_breadcrumb"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)
future_list = []

timestamp = datetime.now()
formatted_timestamp = timestamp.strftime('%Y-%m-%d_%H:%M:%S')

count = 0

base_url = "https://busdata.cs.pdx.edu/api/getBreadCrumbs?vehicle_id="
bus = pd.read_csv("vehicleGroupsIds.csv")

def future_callback(future):
    try:
        future.result()
    except Exception as e:
        print(f"An error occured: {e}")

pubsub_creds =  (
    service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE
        )
    )


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
            future.add_done_callback(future_callback) 
            future_list.append(future)
            count += 1
    else:
        with open("pub_err.txt", "a") as file:
            file.write(f"{formatted_timestamp}, error: {response.status_code} for {bus_id} \n")

for future in futures.as_completed(future_list):
    continue

with open("pub_log.txt", "a") as file:
    file.write(f"{formatted_timestamp} logged {count} messages.\n")

