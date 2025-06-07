import pandas as pd
import os
from typing import Union, IO, Any


def robust_read_csv(file: Union[str, IO[Any]]):
    """Read a CSV file trying multiple encodings."""
    encodings = ["utf-8", "latin1", "cp1252"]
    last_err = None
    for enc in encodings:
        try:
            return pd.read_csv(file, encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
            # reset file pointer if possible
            if hasattr(file, "seek"):
                file.seek(0)
    if last_err:
        raise last_err
    # generic fallback if some other error occurred
    return pd.read_csv(file)


def load_trade_data(file: Union[str, IO[Any]]):
    """Load trade data from a file path or file-like object."""
    # If file is a string path
    if isinstance(file, str):
        lower = file.lower()
        if lower.endswith('.csv'):
            return robust_read_csv(file)
        elif lower.endswith('.xlsx') or lower.endswith('.xls'):
            return pd.read_excel(file)
        else:
            raise ValueError("Unsupported file format: " + file)
    # If file has a name attribute (e.g., Streamlit UploadedFile)
    elif hasattr(file, 'name'):
        filename = file.name
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.csv':
            return robust_read_csv(file)
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(file)
        else:
            raise ValueError("Unsupported uploaded file format: " + filename)
    else:
        raise ValueError("Invalid file type for loading trades.")
