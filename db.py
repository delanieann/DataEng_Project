from valid import valid_and_trans

import time
import psycopg2
import re

def db_connect():
    connection = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres",
    )
    connection.autocommit = True
    return connection


def create_tables(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            drop table if exists BreadCrumb;
            drop table if exists Trip;
            drop type if exists service_type;
            drop type if exists tripdir_type;

            create type service_type as enum ('Weekday', 'Saturday', 'Sunday');
            create type tripdir_type as enum ('Out', 'Back');

            create table Trip (
                trip_id integer,
                route_id integer,
                vehicle_id integer,
                service_key service_type,
                direction tripdir_type,
                PRIMARY KEY (trip_id)
            );

            create table BreadCrumb (
                tstamp timestamp,
                latitude float,
                longitude float,
                speed float,
                trip_id integer,
                FOREIGN KEY (trip_id) REFERENCES Trip
            );
            """)

def load(conn, df):
    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute(
                """
                INSERT INTO Trip (trip_id, vehicle_id) 
                VALUES (%s, %s) 
                ON CONFLICT (trip_id) DO NOTHING;
                """,
                (row['EVENT_NO_TRIP'], row['VEHICLE_ID']))
            cursor.execute(
                """
                INSERT INTO BreadCrumb (tstamp, latitude, longitude, speed, trip_id)
                VALUES (%s, %s, %s, %s, %s)
                """, (row['TIMESTAMP'], row['GPS_LATITUDE'], row['GPS_LONGITUDE'], row['SPEED'], row['EVENT_NO_TRIP']))

def row_count(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM BreadCrumb
            """)
        print(f"Total rows: {cursor.fetchone()[0]}")
            

def main():
    
    conn = db_connect()

    create_tables(conn)
   
    json_files = ["2025-04-09_f.json", "2025-04-10_f.json", "2025-04-11_f.json",
                  "2025-04-14_f.json", "2025-04-15_f.json", "2025-04-16_f.json", 
                  "2025-04-17_f.json", "2025-04-18_f.json", "2025-04-19_f.json", 
                  "2025-04-20_f.json", "2025-04-21_f.json", "2025-04-22_f.json",
                  "2025-04-23_f.json", "2025-04-24_f.json","2025-04-25_f.json",
                  "2025-04-26_f.json","2025-04-27_f.json", "2025-04-28_f.json", 
                  "2025-04-29_f.json", "2025-04-30_f.json", "2025-05-01_f.json", 
                  "2025-05-02_f.json", "2025-05-03_f.json", "2025-05-04_f.json", 
                  "2025-05-05_f.json", "2025-05-06_f.json", "2025-05-07_f.json", 
                  "2025-05-08_f.json"]

    for file in json_files:
        df = valid_and_trans(file)
        load(conn, df)

    row_count(conn)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
