import pandas as pd
import os, requests, json, re
from io import StringIO
from bs4 import BeautifulSoup as soup
from concurrent import futures
from datetime import datetime
from google.oauth2 import service_account
from google.cloud import pubsub_v1

# ==== Base Publisher Class ====
class BasePublisher:
    def __init__(self, service_account_file, project_id, topic_id, vehicle_file, base_url):
        self.service_account_file = service_account_file
        self.project_id = project_id
        self.topic_id = topic_id
        self.vehicle_file = vehicle_file
        self.base_url = base_url
        self.timestamp = datetime.now()
        self.formatted_timestamp = self.timestamp.strftime('%Y-%m-%d_%H:%M:%S.%f')
        self.count = 0
        self.future_list = []

        self.pubsub_creds = service_account.Credentials.from_service_account_file(
            self.service_account_file)
        self.publisher = pubsub_v1.PublisherClient(credentials=self.pubsub_creds)
        self.topic_path = self.publisher.topic_path(self.project_id, self.topic_id)

        self.vehicle_df = pd.read_csv(self.vehicle_file)

    def future_callback(self, future):
        try:
            future.result()
        except Exception as e:
            print(f"{self.formatted_timestamp}: An error occurred: {e}")

    def publish_message(self, message):
        future = self.publisher.publish(self.topic_path, message)
        future.add_done_callback(self.future_callback)
        self.future_list.append(future)
        self.count += 1

    def log_error(self, bus_id, status_code):
        with open("pub_err.txt", "a") as file:
            file.write(f"{self.formatted_timestamp}, error: {status_code} for {bus_id}\n")

    def log_success(self, file_name):
        with open(file_name, "a") as file:
            file.write(f"{self.formatted_timestamp} logged {self.count} messages.\n")

    def wait_for_futures(self):
        for future in futures.as_completed(self.future_list):
            continue


class BCPublisher(BasePublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def fetch_and_publish(self):
        self.future_list = []
        self.count = 0

        for bus_id in self.vehicle_df["Whisker"]:
            complete_url = f"{self.base_url}{bus_id}"
            response = requests.get(complete_url)
            if response.status_code != 404:
                data = response.json()
                for item in data:
                    data_json = json.dumps(item).encode("utf-8")
                    self.publish_message(data_json)
            else:
                self.log_error(bus_id, response.status_code)

        self.wait_for_futures()
        self.log_success("bc_pub_log.txt")


class StopPublisher(BasePublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def fetch_and_publish(self):
        self.future_list = []
        self.count = 0

        for bus_id in self.vehicle_df["Whisker"]:
            complete_url = f"{self.base_url}{bus_id}"
            try:
                r = requests.get(complete_url)
                r.raise_for_status()
            except requests.exceptions.RequestException as e:
                self.log_error(bus_id, str(e))
                continue

            try:
                soup_obj = soup(r.text, "lxml")
                trip_sections = soup_obj.find_all("h2")
                stops_frames = []
                cols = ["vehicle_number", "route_number", "service_key", "direction"]

                for h2 in trip_sections:
                    trip_text = h2.get_text(strip=True)
                    trip_id_match = re.search(r"PDX_TRIP[_\s]+(-?\d+)", trip_text)
                    if not trip_id_match:
                        continue
                    trip_id = trip_id_match.group(1)
                    table = h2.find_next_sibling("table")
                    df = pd.read_html(StringIO(str(table)))[0]
                    df = df[cols].iloc[[0]].copy()
                    df["trip_id"] = trip_id
                    stops_frames.append(df)

                all_df = pd.concat(stops_frames, ignore_index=True) if stops_frames else pd.DataFrame()

            except Exception as e:
                self.log_error(bus_id, str(e))
                continue

            if all_df.empty:
                continue

            for _, row in all_df.iterrows():
                message = json.dumps(row.to_dict()).encode("utf-8")
                self.publish_message(message)

        self.wait_for_futures()
        self.log_success("stop_event_log.txt")

def main():

    #bc_publisher = BCPublisher(
    #    service_account_file="data-eng-456118-701fc22fd16c.json",
    #    project_id="data-eng-456118",
    #    topic_id="bus_breadcrumb",
    #    vehicle_file="vehicleGroupsIds.csv",
    #    base_url="https://busdata.cs.pdx.edu/api/getBreadCrumbs?vehicle_id="
    #)

    #bc_publisher.fetch_and_publish()

    stop_publisher = StopPublisher(
        service_account_file="data-eng-456118-701fc22fd16c.json",
        project_id="data-eng-456118",
        topic_id="stop_events",
        vehicle_file="vehicleGroupsIds.csv",
        base_url="https://busdata.cs.pdx.edu/api/getStopEvents?vehicle_num="
    )

    stop_publisher.fetch_and_publish()

if __name__ == "__main__":
    main()
