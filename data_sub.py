from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from datetime import datetime, timedelta
from valid import valid_and_trans
from dotenv import load_dotenv

import threading
import json
import psycopg2
import io
import pandas as pd
import os

timestamp = datetime.now()
formatted_timestamp = timestamp.strftime('%Y-%m-%d_%H:%M:%S')
date = timestamp.strftime('%Y-%m-%d')

project_id = "data-eng-456118"
subscription_id = "bus_breadcrumb-sub"
# Number of seconds the subscriber should listen for messages
timeout = 600.0

lock = threading.Lock()

count = 0

messages = []

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    #global date
    global messages
    with lock:
        global count
        global formatted_timestamp
        message_data = message.data.decode("utf-8")
        
        if not message_data.strip().startswith("{"):
            with open("sub_err.txt", "a") as file:
                write(f"{formatted_timestamp} skipping non-JSON message: {repr(message_data)}")
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

    trip = df[['EVENT_NO_TRIP', 'VEHICLE_ID']].drop_duplicates(subset='EVENT_NO_TRIP')
    trip.rename(columns={'EVENT_NO_TRIP': 'trip_id', 'VEHICLE_ID': 'vehicle_id'}, inplace=True)
    bc = df[['TIMESTAMP', 'GPS_LATITUDE', 'GPS_LONGITUDE', 'SPEED', 'EVENT_NO_TRIP']]
    with conn.cursor() as cursor:
        try:
            csv_trip = trip.to_csv(index=False)
            f_trip = io.StringIO(csv)
            next(f_trip)
            cursor.copy_from(f_trip, 'trip', sep=',', columns=['trip_id', 'vehicle_id'])

            csv = bc.to_csv(index=False)
            f = io.StringIO(csv)
            next(f)
            cursor.copy_from(f, 'breadcrumb', sep=',', null='\\N')
        except Exception as e:
            with open("db_err.txt", "a") as file:
                file.write(f"Error during data load: {e}")


def main():
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    with subscriber:
        while True:
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
                streaming_pull_future.result(timeout=timeout)

    if count > 0:
        with open("sub_log.txt", "a") as file:
            file.write(f"{formatted_timestamp} Message count: {count}\n")

    #Validate next
    unfiltered = pd.DataFrame(messages)
    df = valid_and_trans(unfiltered)
    
    #Connect to db and put in db
    conn = db_connect()
    if df.empty:
        with open("db_err.txt", "a") as file:
            file.write("Empty dataframe.")
    else:
        load(conn, df)

if __name__ == "__main__":
    main()

