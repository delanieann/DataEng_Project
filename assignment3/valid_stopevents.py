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


@pa.check_input(raw_schema, lazy=True)
@pa.check_output(final_schema, lazy=True)
def replace_direction(df: pd.DataFrame) -> pd.DataFrame:
    direction_map = {
        0: "Out",
        1: "Back",
    }
    return df.replace({"direction": direction_map})

@pa.check_input(raw_schema, lazy=True)
@pa.check_output(final_schema, lazy=True)
def replace_service_key(df: pd.DataFrame) -> pd.DataFrame:
    service_key_map = {
        "W": "Weekday",
        "S": "Saturday",
        "U": "Sunday",
    }
    return df.replace({"service_key": service_key_map})


@pa.check_input(raw_schema, lazy=True)
@pa.check_output(final_schema, lazy=True)
def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(
        columns={
            "trip_id": "trip_id",
            "vehicle_number": "vehicle_id",
            "route_number": "route_id",
            "service_key": "service_key",
            "direction": "direction",
        }
        inplace=True,
    )