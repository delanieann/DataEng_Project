from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from datetime import datetime, timedelta
import threading
import json

timestamp_now = datetime.now()
formatted_timestamp = timestamp_now.strftime('%Y-%m-%d_%H:%M:%S')

timestamp = datetime.now() - timedelta(days=854)
date = timestamp.strftime('%Y-%m-%d')

project_id = "data-eng-456118"
subscription_id = "bus_breadcrumb-sub"
# Number of seconds the subscriber should listen for messages
timeout = 300.0

lock = threading.Lock()

count = 0

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    global date
    with lock:
        global count
        global formatted_timestamp
        message_data = message.data.decode("utf-8")
        if not message_data.strip().startswith("{"):
            with open("sub_err.txt", "a") as file:
                write(f"{formatted_timestamp} skipping nmn-JSON message: {repr(message_data)}")
            message.ack()
            return
        count += 1
        message_json = json.loads(message_data)
        bus_id = message_json.get("VEHICLE_ID")
        with open(f"{date}.json", "a") as file:
            json.dump(message_json, file, indent=4)
    message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

with subscriber:
    try:
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        streaming_pull_future.result(timeout=timeout)
    except TimeoutError:
        streaming_pull_future.cancel()  # Trigger the shutdown.
        streaming_pull_future.result()  # Block until the shutdown is complete.

with open("sub_log.txt", "a") as file:
    file.write(f"{formatted_timestamp} Message count: {count}")


