import pandas as pd


def valid_and_trans(file):
    df = pd.read_json(file)
    df = df.drop(columns=["EVENT_NO_STOP", "GPS_SATELLITES", "GPS_HDOP"])

    # 1 Limit - METERS cannot be negative, it is a distance measurement
    df = df[df["METERS"] >= 0]

    # 2 Limit - ACT_TIME cannot be negative, time measurement
    df = df[df["ACT_TIME"] >= 0]

    # 3 Existence - TIMESTAMP column with date and time
    # Transform OPD_DATE and ACT_TIME to TIMESTAMP column
    df["OPD_DATE"] = df["OPD_DATE"].str.split(':').str[0]
    df["TIMESTAMP"] = (pd.to_datetime(df["OPD_DATE"]) + pd.to_timedelta(df["ACT_TIME"], unit='s'))
    df = df.drop(columns=['ACT_TIME', 'OPD_DATE'])


    df = df.sort_values(by=["TIMESTAMP", "EVENT_NO_TRIP"])

    # 4 Existence - Every record must have a EVENT_NO_TRIP
    # Iterate over the DataFrame by index, skipping first and last
    # Transform - if previous and next EVENT_NO_TRIP match, 
    # fill value with the same EVENT_NO_TRIP
    for i in range(1, len(df) - 1):
        if pd.isna(df.loc[i, "EVENT_NO_TRIP"]):
            prev_val = df.loc[i - 1, "EVENT_NO_TRIP"]
            next_val = df.loc[i + 1, "EVENT_NO_TRIP"]
            
            if pd.notna(prev_val) and prev_val == next_val:
                df.loc[i, "EVENT_NO_TRIP"] = prev_val

    # Drop remaining rows where EVENT_NO_TRIP is still missing
    df.dropna(subset=["EVENT_NO_TRIP"], inplace=True)

    # 5 Referential Integerity - VEHICLE_ID must be within Team1's assignment
    bus = pd.read_csv("vehicleGroupsIds.csv")
    df = df[df["VEHICLE_ID"].isin(bus["Whisker"])]

    # Transform Meters and Timestamp into Speed column
    # 6 Intra-Record Validation - Speed is determined based on delta 
    # distance over delta time for all data within the 
    # same EVENT_NO_TRIP

    # 7 Existence - Speed must exist
    # Transform empty speed cell with next valid value. 
    def trip_speed(group):
        group = group.sort_values("TIMESTAMP")
        group['dMETERS'] = group['METERS'].diff()
        group['dTIME'] = group['TIMESTAMP'].diff().dt.total_seconds()
        group['SPEED'] = group['dMETERS'] / group['dTIME']
        group["SPEED"] = group["SPEED"].bfill()
        group = group.drop(columns=["dMETERS", "dTIME"])
        return group

    df = df.groupby(by="EVENT_NO_TRIP", group_keys=False)[df.columns].apply(trip_speed).reset_index(drop=True)


    # 8 Existence - Longitude exists
    df.dropna(subset=["GPS_LONGITUDE"])

    # 9 Existence - Latitude exists
    df.dropna(subset=["GPS_LATITUDE"])

    # 10 Statistical - Average speed is less than 60 miles per hour
    if df['SPEED'].mean() > 60:
        print("Average speed was greater than 60 mph")


    return(df)
