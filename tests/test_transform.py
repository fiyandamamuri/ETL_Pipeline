import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
import sys
from pathlib import Path

# Fix import path
sys.path.append(str(Path(__file__).parent.parent))
from utils.transform import clean_data

@pytest.fixture
def sample_raw_data():
    return pd.DataFrame({
        "Title": ["Product A", "Unknown Product", "Product B", "Product D", "Product C"],
        "Price": ["$10.99", "Unknown Price", "$20.50", "$15.00", "$25.99"],
        "Rating": ["4.5 stars", "Invalid", "3.8 stars", "4.0 stars", "5.0 stars"],
        "Colors": ["2 colors", "1 color", "3 colors", "2 colors", "1 color"],
        "Size": ["Size: M", "Size: L", "Size: XL", "Size: S", "Size: M"],
        "Gender": ["Gender: Male", "Gender: Female", "Gender: Unisex", "Gender: Male", "Gender: Female"],
        "Timestamp": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
    })

@pytest.fixture
def expected_clean_data():
    return pd.DataFrame({
        "Title": ["Product A", "Product B", "Product D", "Product C"],
        "Price": [175840.0, 328000.0, 240000.0, 415840.0],
        "Rating": [4.5, 3.8, 4.0, 5.0],
        "Colors": [2, 3, 2, 1],
        "Size": ["M", "XL", "S", "M"],
        "Gender": ["Male", "Unisex", "Male", "Female"],
        "Timestamp": ["2023-01-01", "2023-01-03", "2023-01-04", "2023-01-05"]
    })

def test_clean_data_transformations(tmpdir, sample_raw_data, expected_clean_data):
    input_path = str(tmpdir.join("raw.csv"))
    output_path = str(tmpdir.join("clean.csv"))
    sample_raw_data.to_csv(input_path, index=False)
    clean_data(input_path, output_path)
    cleaned_df = pd.read_csv(output_path)
    expected_clean_data.reset_index(drop=True, inplace=True)
    cleaned_df.reset_index(drop=True, inplace=True)
    pd.testing.assert_frame_equal(cleaned_df, expected_clean_data)

def test_clean_data_handles_empty_file(tmpdir):
    input_path = str(tmpdir.join("empty.csv"))
    output_path = str(tmpdir.join("clean_empty.csv"))
    pd.DataFrame().to_csv(input_path, index=False)
    with pytest.raises((ValueError, pd.errors.EmptyDataError)):
        clean_data(input_path, output_path)

def test_clean_data_handles_missing_columns(tmpdir):
    input_path = str(tmpdir.join("missing_cols.csv"))
    output_path = str(tmpdir.join("clean_missing.csv"))
    pd.DataFrame({"Title": ["Test"]}).to_csv(input_path, index=False)
    with pytest.raises(KeyError):
        clean_data(input_path, output_path)

def test_clean_data_saves_to_correct_path(tmpdir, sample_raw_data):
    input_path = str(tmpdir.join("raw.csv"))
    output_path = str(tmpdir.join("clean.csv"))
    sample_raw_data.to_csv(input_path, index=False)

    # ✅ Patch hanya saat fungsi dijalankan, bukan saat bikin file
    with patch("pandas.DataFrame.to_csv") as mock_to_csv:
        clean_data(input_path, output_path)
        mock_to_csv.assert_called_once_with(output_path, index=False)

def test_price_conversion(tmpdir):
    input_path = str(tmpdir.join("raw_price.csv"))
    output_path = str(tmpdir.join("clean_price.csv"))
    price_data = pd.DataFrame({
        "Title": ["Product A"],
        "Price": ["$10.00"],
        "Rating": ["5.0 stars"],
        "Colors": ["1 color"],
        "Size": ["Size: M"],
        "Gender": ["Gender: Male"],
        "Timestamp": ["2023-01-01"]
    })
    price_data.to_csv(input_path, index=False)
    clean_data(input_path, output_path)
    cleaned_df = pd.read_csv(output_path)
    assert cleaned_df["Price"].iloc[0] == 160000.0

def test_color_extraction(tmpdir):
    input_path = str(tmpdir.join("raw_colors.csv"))
    output_path = str(tmpdir.join("clean_colors.csv"))
    color_data = pd.DataFrame({
        "Title": ["Product A", "Product B"],
        "Price": ["$10.00", "$20.00"],
        "Rating": ["5.0 stars", "4.0 stars"],
        "Colors": ["3 colors", "5 different colors"],
        "Size": ["Size: M", "Size: L"],
        "Gender": ["Gender: Male", "Gender: Female"],
        "Timestamp": ["2023-01-01", "2023-01-02"]
    })
    color_data.to_csv(input_path, index=False)
    clean_data(input_path, output_path)
    cleaned_df = pd.read_csv(output_path)
    assert cleaned_df["Colors"].tolist() == [3, 5]
