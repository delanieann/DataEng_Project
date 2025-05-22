import pandera as pa

import pandas as pd



raw_schema = pa.DataFrameSchema(
    {
        "trip_id": pa.Column(int, pa.Check.ge(0)),
        "vehicle_number": pa.Column(int, pa.Check.ge(0)),
        "route_number": pa.Column(int, pa.Check.ge(0)),
        "service_key": pa.Column(str, pa.Check.str_length(1, 2)),
        "direction": pa.Column(int, pa.Check.isin([0, 1])),
    },
    strict=True,
    coerce=True,
)


final_schema = pa.DataFrameSchema(
    {
        "trip_id": pa.Column(int, pa.Check.ge(0)),
        "vehicle_id": pa.Column(int, pa.Check.ge(0)),
        "route_id": pa.Column(int, pa.Check.ge(0)),
        "service_key": pa.Column(str, pa.Check.isin(["Weekday", "Saturday", "Sunday"])),
        "direction": pa.Column(str, pa.Check.isin(["Out", "Back"])),
    },
    strict=True,
    coerce=True,
    drop_invalid_rows=True,
)


def replace_direction(df: pd.DataFrame) -> pd.DataFrame:
    direction_map = {
        0: "Out",
        1: "Back",
    }
    return df.replace({"direction": direction_map})

def replace_service_key(df: pd.DataFrame) -> pd.DataFrame:
    service_key_map = {
        "W": "Weekday",
        "S": "Saturday",
        "U": "Sunday",
    }
    return df.replace({"service_key": service_key_map})


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(
        columns={
            "trip_id": "trip_id",
            "vehicle_number": "vehicle_id",
            "route_number": "route_id",
            "service_key": "service_key",
            "direction": "direction",
        }
    )

@pa.check_input(raw_schema)
@pa.check_output(final_schema)
def run_transforms(df: pd.DataFrame) -> pd.DataFrame:
    try:
        df = replace_direction(df)
        df = replace_service_key(df)
        df = rename_columns(df)
    except Exception as e:
        # handle the exception write_error? or use logging module
        print(f"An error occurred: {e}")
        raise
    return df
