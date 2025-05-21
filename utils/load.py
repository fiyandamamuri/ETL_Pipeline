import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def load_from_csv(file_path: str) -> pd.DataFrame:
    """
    Load data from a CSV file.
    """
    print(f"📥 Loading data from CSV: {file_path}")
    return pd.read_csv(file_path)


def load_to_gsheet(df: pd.DataFrame, spreadsheet_id: str, range_name: str = "Sheet1!A1", credentials_file: str = "./google-sheets-api.json") -> bool:
    """
    Upload a DataFrame to Google Sheets using Sheets API v4.
    """
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # Ubah Timestamp ke string agar bisa diserialisasi
        df = df.copy()
        df = df.applymap(lambda x: x.isoformat() if isinstance(x, pd.Timestamp) else x)

        # Konversi DataFrame ke list of lists
        values = [df.columns.tolist()] + df.values.tolist()
        body = {'values': values}

        # Tulis data ke Google Sheets
        sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

        print("✅ Data berhasil disimpan ke Google Sheets.")
        return True

    except Exception as e:
        print(f"❌ Gagal menyimpan ke Google Sheets: {e}")
        return False


def load_to_postgres(data_bersih: pd.DataFrame, db_url: str):
    """
    Load a cleaned DataFrame into a PostgreSQL table (products).
    If the table doesn't exist, it will be created.
    """
    try:
        engine = create_engine(db_url)

        with engine.connect() as con:
            print("✅ Koneksi ke database berhasil!")

            # Buat tabel jika belum ada
            create_table_query = text("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    "Title" TEXT NOT NULL,
                    "Price" NUMERIC(10, 2) NOT NULL,
                    "Rating" NUMERIC(3, 2) NOT NULL,
                    "Colors" INTEGER NOT NULL,
                    "Size" TEXT NOT NULL,
                    "Gender" TEXT NOT NULL,
                    "Timestamp" TIMESTAMP NOT NULL
                );
            """)
            con.execute(create_table_query)
            print("✅ Tabel 'products' berhasil dicek atau dibuat.")

        # Validasi kolom
        expected_columns = ['Title', 'Price', 'Rating', 'Colors', 'Size', 'Gender', 'Timestamp']
        missing = [col for col in expected_columns if col not in data_bersih.columns]
        if missing:
            raise ValueError(f"❌ Kolom berikut tidak ditemukan di data: {missing}")

        print(f"🧮 Jumlah baris yang akan diunggah: {len(data_bersih)}")
        print("🔍 Tipe data kolom:")
        print(data_bersih.dtypes)

        # Upload ke PostgreSQL
        print("🚚 Mulai proses upload ke PostgreSQL...")
        data_bersih.to_sql(
            name='products',
            con=engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=1000,
            schema='public'  # eksplisit untuk menghindari masalah schema
        )
        print("✅ Data berhasil disimpan ke tabel 'products'.")

    except SQLAlchemyError as e:
        print(f"❌ Kesalahan SQLAlchemy: {e}")
        raise
    except Exception as e:
        print(f"❌ Terjadi kesalahan umum: {e}")
        raise


if __name__ == "__main__":
    try:
        df = load_from_csv("./cleaned_fashion_products.csv")
        print(df.head())

        # Load ke PostgreSQL
        DB_URL = "postgresql://fiyan:winarnipaimin@localhost:5432/datasets_fashion"
        load_to_postgres(df, DB_URL)

        # Upload ke Google Sheets
        SPREADSHEET_ID = "1FQi2FBtradlhahlk8DOcj4t6dwTn3KaKfQ5KDlqX7oY"
        load_to_gsheet(df, SPREADSHEET_ID)
    except Exception as e:
        print(f"❌ Program gagal dijalankan: {e}")
