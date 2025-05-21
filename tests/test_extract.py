import pytest
import requests
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup
from datetime import datetime
import sys
from pathlib import Path

# Fix import path
sys.path.append(str(Path(__file__).parent.parent))
from utils.extract import (
    fetching_content,
    safe_get_text,
    extract_product_data,
    scrape_fashion_products,
    HEADERS
)

# Sample test data
SAMPLE_HTML = """
<div class="collection-card">
    <h3 class="product-title">Test Product</h3>
    <span class="price">$99.99</span>
    <div class="product-details">
        <p>4.5 stars</p>
        <p>Red, Blue</p>
        <p>M, L</p>
        <p>Unisex</p>
    </div>
</div>
"""

# 1. Test fetching_content()
@patch("utils.extract.requests.Session")
def test_fetching_content_success(mock_session):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"<html>test</html>"
    mock_response.raise_for_status.return_value = None
    mock_session.return_value.get.return_value = mock_response

    result = fetching_content("http://valid.url")
    assert result == b"<html>test</html>"

@patch("utils.extract.requests.Session")
def test_fetching_content_failure(mock_session):
    mock_session.return_value.get.side_effect = requests.exceptions.RequestException("Failed")
    result = fetching_content("http://invalid.url")
    assert result is None

# 2. Test safe_get_text()
def test_safe_get_text_with_element():
    soup = BeautifulSoup("<p>Test Text</p>", "html.parser")
    element = soup.p
    assert safe_get_text(element) == "Test Text"

def test_safe_get_text_without_element():
    assert safe_get_text(None) == "N/A"
    assert safe_get_text(None, default="Empty") == "Empty"

# 3. Test extract_product_data()
def test_extract_product_data_complete():
    soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
    card = soup.find("div", class_="collection-card")
    result = extract_product_data(card)
    
    assert result == {
        "Title": "Test Product",
        "Price": "$99.99",
        "Rating": "4.5 stars",
        "Colors": "Red, Blue",
        "Size": "M, L",
        "Gender": "Unisex",
        "Timestamp": result["Timestamp"]
    }

def test_extract_product_data_incomplete():
    incomplete_html = "<div class='collection-card'><h3 class='product-title'>Test</h3></div>"
    soup = BeautifulSoup(incomplete_html, "html.parser")
    card = soup.find("div", class_="collection-card")
    result = extract_product_data(card)
    
    assert result == {
        "Title": "Test",
        "Price": "Unknown Price",
        "Rating": "N/A",
        "Colors": "N/A",
        "Size": "N/A",
        "Gender": "N/A",
        "Timestamp": result["Timestamp"]
    }

# 4. Test scrape_fashion_products()
@patch("utils.extract.fetching_content")
def test_scrape_fashion_products_single_page(mock_fetch):
    mock_html = """
    <html>
        <div class="collection-card">Test Product</div>
        <li class="page-item next"></li>
    </html>
    """
    mock_fetch.return_value = mock_html.encode()
    
    result = scrape_fashion_products()
    assert len(result) > 0
    assert isinstance(result[0]["Timestamp"], str)

@patch("utils.extract.fetching_content")
@patch("utils.extract.time.sleep")
def test_scrape_fashion_products_multiple_pages(mock_sleep, mock_fetch):
    page1 = """
    <html>
        <div class="collection-card">Product 1</div>
        <li class="page-item next"><a href="/page2"></a></li>
    </html>
    """
    page2 = """
    <html>
        <div class="collection-card">Product 2</div>
    </html>
    """
    mock_fetch.side_effect = [page1.encode(), page2.encode()]
    
    result = scrape_fashion_products()
    assert len(result) == 2
    assert mock_fetch.call_count == 2
