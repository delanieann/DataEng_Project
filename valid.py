import pandas as pd

def write_error(e):
    with open("validation_err.txt", "a") as file:
        file.write(e)

def empty_df(df):
    try:
        assert not df.empty, "DF is empty"
        assert not df.shape[1] == 0, "DF has no rows"
    except AssertionError as e:
        write_error(e)

def drop_cols(df):
    try:
        df = df.drop(columns=["EVENT_NO_STOP", "GPS_SATELLITES", "GPS_HDOP"])
        required_cols =  {"OPD_DATE", "ACT_TIME", "GPS_LATITUDE", 
                          "GPS_LONGITUDE", "SPEED", "EVENT_NO_TRIP"}
        assert required_cols.issubset(df.columns), f"Columns present: {set(df.columns)}"
    except AssertionError as e:
        write_error(e)
    return df

def neg_meters(df):
    try:
    # 1 Limit - METERS cannot be negative, it is a distance measurement
        df = df[df["METERS"] >= 0]
        assert (df["METERS"] < 0).sum() == 0, "Negative meters still present."
    except AssertionError as e:
        write_error(e)
    return df

def neg_time(df):
    try:
    # 2 Limit - ACT_TIME cannot be negative, time measurement
        df = df[df["ACT_TIME"] >= 0]
        assert (df["ACT_TIME"] < 0).sum() == 0, "Negative time still present."
    except AssertionError as e:
        write_error(e)
    return df

def timestamp_col(df):
    # 3 Existence - TIMESTAMP column with date and time
    # Transform OPD_DATE and ACT_TIME to TIMESTAMP column
    try:
        df["OPD_DATE"] = df["OPD_DATE"].str.split(':').str[0]
        df["TIMESTAMP"] = (pd.to_datetime(df["OPD_DATE"]) + pd.to_timedelta(df["ACT_TIME"], unit='s'))
        df = df.drop(columns=['ACT_TIME', 'OPD_DATE'])
        df = df.sort_values(by=["TIMESTAMP", "EVENT_NO_TRIP"])
        assert 'TIMESTAMP' in df.columns, "TIMESTAMP column not created"
    except AssertionError as e:
        write_error(e)
    return df

def trip_exist(df):
    # 4 Existence - Every record must have a EVENT_NO_TRIP
    # Drop remaining rows where EVENT_NO_TRIP is still missing
    try:
        df.dropna(subset=["EVENT_NO_TRIP"], inplace=True)
        assert not df['EVENT_NO_TRIP'].isna().any(), "Null values in EVENT_NO_TRIP"
    except AssertionError as e:
        write_error(e)
    return df

def vehicle_id(df):
    # 5 Referential Integerity - VEHICLE_ID must be within Team1's assignment
    try:
        bus = pd.read_csv("vehicleGroupsIds.csv")
        df = df[df["VEHICLE_ID"].isin(bus["Whisker"])]
        assert df["VEHICLE_ID"].isin(bus["Whisker"]).all(), "Extraneous vehicle ids."
    except AssertionError as e:
        write_error(e)
    return df

    # Transform Meters and Timestamp into Speed column
    # 6 Intra-Record Validation - Speed is determined based on delta 
    # distance over delta time for all data within the 
    # same EVENT_NO_TRIP

    # 7 Existence - Speed must exist
    # Transform empty speed cell with next valid value. 
    # Speed cannot be over 70 mph
    # Speed cannot be NaN

def trip_speed(group):
    group = group.sort_values("TIMESTAMP")
    group['dMETERS'] = group['METERS'].diff()
    group['dTIME'] = group['TIMESTAMP'].diff().dt.total_seconds()
    group['SPEED'] = group['dMETERS'] / group['dTIME']
    group['SPEED'] = group['SPEED'].bfill()
    group = group.drop(columns=["dMETERS", "dTIME"])
    group = group.dropna(subset=['SPEED'])
    group = group[group['SPEED'] <= 70]
    return group

def speed_wrapper(df):
    try:
        df = df.groupby(by="EVENT_NO_TRIP", group_keys=False).apply(trip_speed).reset_index(drop=True)
        assert 'SPEED' in df.columns, "Missing SPEED column."
    except AssertionError as e:
        write_error(e)
    return df

def longitude(df):
    # 8 Existence - Longitude exists
    try:
        df = df.dropna(subset=["GPS_LONGITUDE"])
        assert not df['GPS_LONGITUDE'].isna().any(), "null GPS_LONGITUDE still exists."
    except AssertionError as e:
        write_error(e)
    return df

def latitude(df):
    # 9 Existence - Latitude exists
    try:
        df = df.dropna(subset=["GPS_LATITUDE"])
        assert not df['GPS_LATITUDE'].isna().any(), "null GPS_LATITUDE still exists."
    except AssertionError as e:
        write_error(e)
    return df

def avg_speed(df):
    # 10 Statistical - Average speed is less than 60 miles per hour
    try:
        assert df['SPEED'].mean() <= 60, "Average speed was greater than 60 mph"
    except AssertionError as e:
        write_error(e)

def column_organization(df):
    # Reorganize columns for copy_from
    try:
        expected_cols = ['TIMESTAMP', 'GPS_LATITUDE', 'GPS_LONGITUDE', 'SPEED', 'EVENT_NO_TRIP', 'VEHICLE_ID']
        df = df[expected_cols]
        assert expected_cols.issubset(df.columns), f"Columns present: {set(df.columns)}"
    except AssertionError as e:
        write_error(e)
    return(df)


def valid_and_trans(messages):
    #check for empty df
    empty_df(messages)
    df = messages.copy()

    df = drop_cols(df)      
    df = neg_meters(df)
    df = neg_time(df)
    df = timestamp_col(df)
    df = trip_exist(df)
    df = vehicle_id(df)
    df = speed_wrapper(df)
    df = longitude(df)
    df = latitude(df)
    avg_speed(df)
    df = column_organization(df)
    return df
