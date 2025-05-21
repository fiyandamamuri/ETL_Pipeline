import pandas as pd
import os

def clean_data(input_csv_path, output_csv_path):
    # Baca data dari hasil extract
    df = pd.read_csv(input_csv_path)

    # Hapus data yang memiliki nilai null
    df.dropna(inplace=True)

    # Hapus data duplikat
    df.drop_duplicates(inplace=True)

    # Hapus data dengan Title "Unknown Product"
    df = df[df["Title"] != "Unknown Product"]

    # Hapus data dengan Price "Unknown Price"
    df = df[~df["Price"].astype(str).str.contains("Unknown", na=False)]

    # Bersihkan dan konversi kolom Price dari dolar ke Rupiah (USD -> IDR, kurs 16.000)
    df["Price"] = df["Price"].replace('[\$,]', '', regex=True).astype(float) * 16000

    # Hapus baris yang memiliki Rating invalid
    df = df[~df["Rating"].astype(str).str.contains("Invalid", na=False)]

    # Bersihkan dan konversi Rating jadi float
    df["Rating"] = df["Rating"].astype(str).str.extract(r"([\d.]+)").astype(float)

    # Bersihkan kolom Colors: ambil hanya angka
    df["Colors"] = df["Colors"].astype(str).str.extract(r"(\d+)").astype(int)

    # Bersihkan kolom Size: hapus "Size: "
    df["Size"] = df["Size"].astype(str).str.replace("Size: ", "", regex=False)

    # Bersihkan kolom Gender: hapus "Gender: "
    df["Gender"] = df["Gender"].astype(str).str.replace("Gender: ", "", regex=False)

    # Simpan hasil transformasi ke file CSV di output path
    df.to_csv(output_csv_path, index=False)
    print(f"Transformasi selesai. Data bersih disimpan di '{output_csv_path}'")
    print(df.info())
    print(df.head())

if __name__ == "__main__":
    # Gunakan path relatif dari main folder
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    input_path = os.path.join(base_dir, "scraped_fashion_products.csv")
    output_path = os.path.join(base_dir, "cleaned_fashion_products.csv")

    clean_data(input_path, output_path)
