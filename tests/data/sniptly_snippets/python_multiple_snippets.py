import pandas as pd


def create_pandas_df():
    # -->
    # name: Create Pandas dataframe
    # prefix: pd_create_df
    # description: Creates Pandas dataframe
    df = pd.DataFrame({"x": [0, 1, 2, 3, 4], "y": [10, 11, 10, 9, 12]})
    # <--
    return df


def concat_dataframes():
    df1 = pd.DataFrame({"id": [12, 18, 21], "price": [10, 20, 40]})
    df2 = pd.DataFrame({"id": [10, 14], "price": [5, 16]})
    # -->
    # name: Concatenate two dataframes
    # prefix: pd_concat_df
    # description: Concatenates two dataframes along the y-axis
    # see: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.concat.html
    concatenated = pd.concat([df1, df2], axis=0)
    # <--
    return concatenated


# -->
# name: Mypy TypedDict
# prefix: mypy_typeddict
# description: Define dictionary type with specific keys
from typing import Optional, List, TypedDict, Union


class MyTypedDict(TypedDict):
    string: str
    list_of_strings: List[str]
    string_or_boolean: Union[str, bool]
    # Optional only means that None is a valid value.
    optional_key: Optional[int]
    # Check totality for arguments that can be omitted.
    # https://mypy.readthedocs.io/en/latest/more_types.html#totality


my_typed_dict: MyTypedDict = {
    "string": "Hello",
    "list_of_strings": ["one", "two", "three"],
    "string_or_boolean": True,
    "optional_key": None,
}
# <--
