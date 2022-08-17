from typing import Dict
import pandas as pd


def dollars(value: float, dollar_sign: bool = True) -> str:
    if dollar_sign:
        return "${:,.2f}".format(value)
    else:
        return "{:,.2f}".format(value)


def df_append(df: pd.DataFrame, row: Dict) -> pd.DataFrame:
    """Because pandas deprecated their append function :("""
    return pd.concat([df, pd.DataFrame.from_records([row])], ignore_index=True)
