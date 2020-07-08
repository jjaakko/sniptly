import pandas as pd


def create_pandas_df():
    # -->
    # name: Create Pandas dataframe
    # prefix: pd_create_df
    # description: Creates Pandas dataframe
    df = pd.DataFrame({"x": [0, 1, 2, 3, 4], "y": [10, 11, 10, 9, 12]})
    # <--
    return df
