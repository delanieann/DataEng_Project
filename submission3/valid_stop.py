import pandas as pd


def write_error(e):
    with open("validation_err.txt", "a") as file:
        file.write(str(e) + "\n")

def empty_df(df):
    try:
        assert not df.empty, "DF is empty"
        assert not df.shape[1] == 0, "DF has no rows"
    except AssertionError as e:
        write_error(e)
        return False
    return True

def invalid_trip_id(df):
    try:
        df["trip_id"] = pd.to_numeric(df["trip_id"], errors="coerce")
        df = df[df["trip_id"] != -1]
        df = df.dropna(subset=["trip_id"])
        assert "trip_id" in df.columns, "Missing 'trip_id' column"
    except AssertionError as e:
        write_error(e)
    return df

def rename_cols(df):
    try:
        df.rename(columns={
        "vehicle_number": "vehicle_id",
        "route_number": "route_id"
    }, inplace=True)
        df = df[['trip_id', 'route_id', 'vehicle_id', 'service_key', 'direction']]
        assert "vehicle_id" in df.columns, "Missing 'vehicle_id' column"
        assert "route_id" in df.columns, "Missing 'route_id' column"
    except AssertionError as e:
        write_error(e)
    return df

def service_key(df):
    try:
        service_map = {"W": "Weekday", "S": "Saturday", "U": "Sunday"}
        df["service_key"] = df["service_key"].map(service_map)
        df = df.dropna(subset=["service_key"])
        valid_keys = {"Weekday", "Saturday", "Sunday"}
        invalid_keys = set(df["service_key"].unique()) - valid_keys
        assert not invalid_keys, f"Unexpected service_key values: {invalid_keys}"
    except AssertionError as e:
        write_error(e)
    return df

def direction(df):
    try:
        direction_map = {0: "Out", 1: "Back"}
        df["direction"] = df["direction"].map(direction_map)
        df = df.dropna(subset=["direction"])
        valid_dirs = {"Out", "Back"}
        invalid_dirs = set(df["direction"].unique()) - valid_dirs
        assert not invalid_dirs, f"Unexpected direction values: {invalid_dirs}"

    except AssertionError as e:
        write_error(e)
    return df


def valid_stop(incoming):
    df = incoming.copy()
    if empty_df(df):
        df = invalid_trip_id(df)
        df = rename_cols(df)
        df = service_key(df)
        df = direction(df)
    return df


def main():

    try:
        df = pd.read_csv("05232025.csv")
        df = valid_stop(df)

        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="localhost"
        )
        cur = conn.cursor()

        insert_query = """
            INSERT INTO Trip (trip_id, route_id, vehicle_id, service_key, direction)
            VALUES (%s, %s, %s, %s::service_type, %s::tripdir_type)
            ON CONFLICT (trip_id) DO UPDATE SET
                route_id = EXCLUDED.route_id,
                vehicle_id = EXCLUDED.vehicle_id,
                service_key = EXCLUDED.service_key,
                direction = EXCLUDED.direction;
        """

        for _, row in df.iterrows():
            try:
                cur.execute(insert_query, (
                    int(row['trip_id']),
                    int(row['route_id']) if pd.notnull(row['route_id']) else None,
                    int(row['vehicle_id']) if pd.notnull(row['vehicle_id']) else None,
                    row['service_key'],  # ENUM: Weekday, Saturday, Sunday
                    row['direction']     # ENUM: Out, Back
                ))
            except Exception as row_err:
                write_error(f"Error updating trip_id {row['trip_id']}: {row_err}")
                conn.rollback()

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        write_error(e)


if __name__ == "__main__":
    main()
