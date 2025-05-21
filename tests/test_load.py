import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.load import load_from_csv, load_to_gsheet, load_to_postgres

@pytest.fixture
def sample_clean_data():
    """Fixture untuk DataFrame bersih contoh"""
    return pd.DataFrame({
        "Title": ["Product A"],
        "Price": [160000.0],
        "Rating": [4.5],
        "Colors": [2],
        "Size": ["M"],
        "Gender": ["Male"],
        "Timestamp": [pd.Timestamp("2023-01-01")]
    })

def test_load_from_csv(tmpdir):
    """Test fungsi load_from_csv membaca file dengan benar"""
    file_path = tmpdir.join("test.csv")
    df_expected = pd.DataFrame({
        "Name": ["Alice", "Bob"],
        "Age": [30, 25]
    })
    df_expected.to_csv(file_path, index=False)

    df_result = load_from_csv(str(file_path))
    pd.testing.assert_frame_equal(df_result, df_expected)

@patch("utils.load.Credentials")
@patch("utils.load.build")
def test_load_to_gsheet_success(mock_build, mock_credentials, sample_clean_data):
    """Test load_to_gsheet berhasil menyimpan data"""
    mock_service = MagicMock()
    mock_sheet = MagicMock()
    mock_values = MagicMock()
    
    mock_build.return_value = mock_service
    mock_service.spreadsheets.return_value = mock_sheet
    mock_sheet.values.return_value = mock_values
    mock_values.update.return_value.execute.return_value = {}

    result = load_to_gsheet(sample_clean_data, "dummy_spreadsheet_id", credentials_file="dummy.json")

    assert result is True
    mock_values.update.assert_called_once()

@patch("utils.load.Credentials")
@patch("utils.load.build")
def test_load_to_gsheet_failure(mock_build, mock_credentials, sample_clean_data):
    """Test load_to_gsheet gagal jika terjadi exception"""
    mock_build.side_effect = Exception("Auth error")
    
    result = load_to_gsheet(sample_clean_data, "dummy_spreadsheet_id", credentials_file="dummy.json")
    assert result is False

@patch("utils.load.create_engine")
def test_load_to_postgres_success(mock_create_engine, sample_clean_data):
    """Test load_to_postgres berhasil menyimpan ke PostgreSQL"""
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    load_to_postgres(sample_clean_data, "postgresql://dummy_user:dummy_pass@localhost:5432/dummy_db")

    mock_conn.execute.assert_called()
    mock_engine.connect.assert_called_once()
    mock_create_engine.assert_called_once()

@patch("utils.load.create_engine")
def test_load_to_postgres_missing_column(mock_create_engine, sample_clean_data):
    """Test load_to_postgres gagal karena kolom hilang"""
    df_invalid = sample_clean_data.drop(columns=["Title"])  # Hapus satu kolom

    with pytest.raises(ValueError, match="Kolom berikut tidak ditemukan"):
        load_to_postgres(df_invalid, "postgresql://dummy_user:dummy_pass@localhost:5432/dummy_db")

@patch("utils.load.create_engine")
def test_load_to_postgres_sqlalchemy_error(mock_create_engine, sample_clean_data):
    """Test load_to_postgres gagal karena SQLAlchemy error"""
    mock_create_engine.side_effect = SQLAlchemyError("Connection failed")

    with pytest.raises(SQLAlchemyError):
        load_to_postgres(sample_clean_data, "postgresql://dummy_user:dummy_pass@localhost:5432/dummy_db")
