import time
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}


def fetching_content(url):
    """Mengambil konten HTML dari URL yang diberikan."""
    session = requests.Session()
    try:
        response = session.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan ketika mengakses {url}: {e}")
        return None


def safe_get_text(element, default="N/A"):
    return element.get_text(strip=True) if element else default

def extract_product_data(card):
    """Mengambil data produk fashion dari satu card HTML dengan pengecekan yang aman."""
    try:
        title = safe_get_text(card.find("h3", class_="product-title"), "Unknown Product")
        price = safe_get_text(card.find("span", class_="price"), "Unknown Price")

        details = card.select("div.product-details p")
        rating = safe_get_text(details[0]) if len(details) > 0 else "N/A"
        colors = safe_get_text(details[1]) if len(details) > 1 else "N/A"
        size = safe_get_text(details[2]) if len(details) > 2 else "N/A"
        gender = safe_get_text(details[3]) if len(details) > 3 else "N/A"

        return {
            "Title": title,
            "Price": price,
            "Rating": rating,
            "Colors": colors,
            "Size": size,
            "Gender": gender,
            "Timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Gagal parsing satu produk: {e}")
        return None


def scrape_fashion_products(base_url="https://fashion-studio.dicoding.dev/", delay=2):
    """Scraping semua data produk fashion dari website."""
    data = []
    next_page = base_url

    while next_page:
        print(f"Scraping halaman: {next_page}")
        content = fetching_content(next_page)
        if not content:
            break

        soup = BeautifulSoup(content, "html.parser")
        product_cards = soup.find_all("div", class_="collection-card")
        for card in product_cards:
            product = extract_product_data(card)
            if product:
                data.append(product)

        next_link = soup.select_one("li.page-item.next a")
        if next_link and next_link.get("href"):
            next_page = base_url.rstrip("/") + next_link.get("href")
            time.sleep(delay)
        else:
            break

    return data


def main():
    """Fungsi utama menjalankan scraping dan menyimpan ke file."""
    all_products = scrape_fashion_products()
    df = pd.DataFrame(all_products)

    # Tentukan folder utama (1 level di atas folder ini)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Buat path file CSV di main folder
    output_path = os.path.join(base_dir, "scraped_fashion_products.csv")

    df.to_csv(output_path, index=False)
    print(f"Scraping selesai. Data disimpan di '{output_path}'")
    print(df.head())


if __name__ == "__main__":
    main()
