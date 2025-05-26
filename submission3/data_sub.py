from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from datetime import datetime, timedelta
from valid import valid_and_trans
from valid_stop import valid_stop
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

    
    def listen(self, timeout=1500):
        streaming_pull_future = self.subscriber.subscribe(self.subscription_path, callback=self.callback)
        try:
            streaming_pull_future.result(timeout)
        except TimeoutError:
            streaming_pull_future.cancel()
            streaming_pull_future.result()
    

    def db_connect(self):
        conn =  psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password=os.environ.get("PASSWORD")
        )
        conn.autocommit = True
        return conn

   

    def log_error(self, file_name, message):
        with open(file_name, "a") as file:
            file.write(f"{self.formatted_timestamp} - {message}\n")

    def log_success(self, file_name, table):
        with open(file_name, "a") as file:
            file.write(f"{self.formatted_timestamp} - {table} - {self.count}\n")

class BreadcrumbSubscriber(BaseSubscriber):
    def __init__(self, project_id, subscription_id):
        super().__init__(project_id, subscription_id)

    def run(self):
        self.listen()

        if self.count == 0:
            return

        self.log_success("sub_log.txt", "Breadcrumb")
        df_raw = pd.DataFrame(self.messages)

        df_validated = valid_and_trans(df_raw)

        conn = self.db_connect()
        self.load_to_db(conn, df_validated)

            # Reset for next batch
        self.messages = []
        self.count = 0

    def load_to_db(self, conn, df):
        bc = df[['TIMESTAMP', 'GPS_LATITUDE', 'GPS_LONGITUDE', 'SPEED', 'EVENT_NO_TRIP']]

        try:
            with conn, conn.cursor() as cursor:
                csv_bc = bc.to_csv(index=False)
                f_bc = io.StringIO(csv_bc)
                next(f_bc)
                cursor.copy_from(f_bc, 'breadcrumb', sep=',', null='\\N')
        except Exception as e:
            self.log_error("db_err.txt", f"Error during BreadCrumb data load: {e}")





class StopSubscriber(BaseSubscriber):
    def __init__(self, project_id, subscription_id):
        super().__init__(project_id, subscription_id)

    def run(self):
        self.listen()

        if self.count == 0:
            return
        
        self.log_success("sub_log.txt", "Trip")
        df_raw = pd.DataFrame(self.messages)

        df_validated = valid_stop(df_raw)

        conn = self.db_connect()
        self.load_to_db(conn, df_validated)

            # Reset for next batch
        self.messages = []
        self.count = 0


    def load_to_db(self, conn, df):
        try:
            with conn, conn.cursor() as cursor:
                csv_trip = df.to_csv(index=False)
                trip = io.StringIO(csv_trip)
                next(trip)
                cursor.copy_from(trip, 'trip', sep=',', 
                                 columns=('trip_id', 'route_id', 
                                          'vehicle_id', 'service_key', 
                                          'direction'))
                
        except Exception as e:
            self.log_error("db_err.txt", f"Error during Trip data load: {e}")


def main():
    sub = StopSubscriber("data-eng-456118", "stop_events-sub")
    bc_sub = BreadcrumbSubscriber("data-eng-456118", "bus_breadcrumb-sub")
    while True:
        sub.run()
        bc_sub.run()

if __name__ == "__main__":
    main()


