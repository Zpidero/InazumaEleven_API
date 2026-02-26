from pandas import DataFrame, Series
from typing import Union, Dict, List

def as_json(obj : Union[DataFrame, Series, List], title : str = "") -> Dict:
    if isinstance(obj, DataFrame):
        return obj.to_dict(orient="index")
    elif isinstance(obj, Series):
        return obj.to_dict()
    elif isinstance(obj, List):
        return {title : obj}
    else:
        raise ValueError("Value is not a Dataframe or Series")