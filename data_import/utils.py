import pandas as pd
import os
from typing import Union, IO, Any


def load_trade_data(file: Union[str, IO[Any]]):
    """Load trade data from a file path or file-like object."""
    # If file is a string path
    if isinstance(file, str):
        lower = file.lower()
        if lower.endswith('.csv'):
            return pd.read_csv(file)
        elif lower.endswith('.xlsx') or lower.endswith('.xls'):
            return pd.read_excel(file)
        else:
            raise ValueError("Unsupported file format: " + file)
    # If file has a name attribute (e.g., Streamlit UploadedFile)
    elif hasattr(file, 'name'):
        filename = file.name
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.csv':
            return pd.read_csv(file)
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(file)
        else:
            raise ValueError("Unsupported uploaded file format: " + filename)
    else:
        raise ValueError("Invalid file type for loading trades.")
