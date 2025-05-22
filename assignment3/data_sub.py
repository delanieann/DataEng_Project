from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from datetime import datetime, timedelta
from valid import valid_and_trans
from dotenv import load_dotenv

import threading, json, psycopg2, io, os
import pandas as pd

load_dotenv()


class BaseSubscriber:
    def __init__(self, project_id, sub_id):
        self.project_id = project_id
        self.sub_id = sub_id
        self.messages = []
        self.count = 0
        self.lock = threading.Lock()
        self.timestamp = datetime.now()
        self.formatted_timestamp = self.timestamp.strftime('%Y-%m-%d_%H:%M:%S')
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(self.project_id, self.sub_id)

    def callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        with self.lock:
            message_data = message.data.decode("utf-8")
            try:
                message_json = json.loads(message_data)
                self.messages.append(message_json)
                self.count += 1
            except json.JSONDecodeError as e:
                self.log_error("sub_err.txt", f"JSON decode error: {e}")
        message.ack()

    def listen(self, timeout=500):
        streaming_pull_future = self.subscriber.subscribe(self.subscription_path, callback=self.callback)
        try:
            streaming_pull_future.result(timeout)
        except TimeoutError:
            streaming_pull_future.cancel()
            streaming_pull_future.result()

    def log_error(self, file_name, message):
        with open(file_name, "a") as file:
            file.write(f"{self.formatted_timestamp} - {message}\n")

    def log_success(self, file_name):
        with open(file_name, "a") as file:
            file.write(f"{self.formatted_timestamp} - {self.count}\n")

class BreadcrumbSubscriber(BaseSubscriber):
    def __init__(self, project_id, subscription_id):
        super().__init__(project_id, subscription_id)

    def run(self):
        #while True:
        self.listen()

        #if self.count == 0:
        #    continue

        self.log_success("sub_log.txt")
        df_raw = pd.DataFrame(self.messages)
        print(df_raw)
            #df_validated = valid_and_trans(df_raw)

            #conn = self.db_connect()
            #self.load_to_db(conn, df_validated)

            # Reset for next batch
        self.messages = []
        self.count = 0

    def db_connect(self):
        return psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password=os.environ.get("PASSWORD")
        )

    def load_to_db(self, conn, df):
        bc = df[['TIMESTAMP', 'GPS_LATITUDE', 'GPS_LONGITUDE', 'SPEED', 'EVENT_NO_TRIP']]
        trip = df[['EVENT_NO_TRIP', 'VEHICLE_ID']].drop_duplicates(subset='EVENT_NO_TRIP')
        trip.rename(columns={'EVENT_NO_TRIP': 'trip_id', 'VEHICLE_ID': 'vehicle_id'}, inplace=True)

        try:
            with conn, conn.cursor() as cursor:
                csv_trip = trip.to_csv(index=False)
                f_trip = io.StringIO(csv_trip)
                next(f_trip)
                cursor.copy_from(f_trip, 'trip', sep=',', columns=['trip_id', 'vehicle_id'])

                csv_bc = bc.to_csv(index=False)
                f_bc = io.StringIO(csv_bc)
                next(f_bc)
                cursor.copy_from(f_bc, 'breadcrumb', sep=',', null='\\N')
        except Exception as e:
            self.log_error("db_err.txt", f"Error during data load: {e}")

if __name__ == "__main__":
    #sub = BreadcrumbSubscriber("data-eng-456118", "bus_breadcrumb-sub")
    sub = BreadcrumbSubscriber("data-eng-456118", "stop_events-sub")
    sub.run()




























timestamp = datetime.now()
formatted_timestamp = timestamp.strftime('%Y-%m-%d_%H:%M:%S')
date = timestamp.strftime('%Y-%m-%d')

project_id = "data-eng-456118"
subscription_id = "bus_breadcrumb-sub"

lock = threading.Lock()

messages = []
count = 0

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    global messages, count, formatted_timestamp
    with lock:
        message_data = message.data.decode("utf-8")
        
        if not message_data.strip().startswith("{"):
            with open("sub_err.txt", "a") as file:
                file.write(f"{formatted_timestamp} skipping non-JSON message: {repr(message_data)}")
            message.ack()
            return
        
        count += 1
        message_json = json.loads(message_data)
        messages.append(message_json)
    message.ack()


def db_connect():
    connection = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password=os.environ.get("PASSWORD"),
    )
    connection.autocommit = True
    return connection

def load(conn, df):
    bc = df[['TIMESTAMP', 'GPS_LATITUDE', 
                 'GPS_LONGITUDE', 'SPEED', 
                 'EVENT_NO_TRIP']]
    
    trip = df[['EVENT_NO_TRIP', 
                   'VEHICLE_ID']].drop_duplicates(subset='EVENT_NO_TRIP')
    
    trip.rename(columns={'EVENT_NO_TRIP': 'trip_id', 'VEHICLE_ID': 'vehicle_id'}, inplace=True)
        
    with conn.cursor() as cursor:
        try:
            csv_trip = trip.to_csv(index=False)
            f_trip = io.StringIO(csv_trip)
            next(f_trip)
            cursor.copy_from(f_trip, 'trip', sep=',', columns=['trip_id', 'vehicle_id'])

            csv = bc.to_csv(index=False)
            f = io.StringIO(csv)
            next(f)
            cursor.copy_from(f, 'breadcrumb', sep=',', null='\\N')
        except Exception as e:
            with open("db_err.txt", "a") as file:
                file.write(f"{datetime.now()} - Error during data load: {e}\n")


def main():
    
    while True:
        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
        try:
            streaming_pull_future.result(1500)
        except TimeoutError as e:
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.
    
        if count > 0:
            with open("sub_log.txt", "a") as file:
                file.write(f"{formatted_timestamp} Message count: {count}\n")

        #Validate next
        unfiltered = pd.DataFrame(messages)
        df = valid_and_trans(unfiltered)
    
        #Connect to db and put in db
        conn = db_connect()
        load(conn, df)

if __name__ == "__main__":
    main()

