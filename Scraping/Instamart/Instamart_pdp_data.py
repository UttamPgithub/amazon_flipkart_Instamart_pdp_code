# ============================================================================
# Instamart Product Scraper
# ============================================================================
# Description: This module scrapes product details from Instamart.in using
# the product ID (web_pid) and pincode to fetch real-time product data
# including pricing, availability, images, and seller information.
# ============================================================================

from datetime import datetime
from scrapy import Selector
import random
import requests
import json
import time
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Default headers for API requests
DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Host": "instamart.in",
    "If-None-Match": 'W/"97c-OaaUksXriyu6xZl6hRlAWQMG1Ow"',
    "matcher": "febb98efedbabgbg78cdc7f",
    "Referer": "https://instamart.in/",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "x-build-version": "2.367.0",
    "x-device-id": "154b8371-c833-4d9c-a64f-64d15079bdc8"
}

# Headers for HTML page requests (PDP)
PDP_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Host": "instamart.in",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_session_with_retries():
    """
    Create a requests session with automatic retry logic.

    Returns:
        requests.Session: Configured session with retry capabilities

    Retry Strategy:
        - Total retries: 3
        - Backoff factor: 2 (exponential delay)
        - Retry on status codes: 429, 500, 502, 503, 504
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def build_image_url(image_id):
    """
    Build the full Cloudinary image URL from an image ID.

    Args:
        image_id (str): Cloudinary image identifier

    Returns:
        str: Complete image URL
    """
    return f"https://res.cloudinary.com/swiggy/image/upload/fl_lossy/fl_progressive/{image_id}.jpg"


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def set_pincode_location(pincode):
    """
    Set the delivery location using a pincode and retrieve store information.

    This function performs two API calls:
        1. Get place_id from pincode using maps/suggestions endpoint
        2. Get location details (lat/lng) using address-widgets endpoint
        3. Post location data to select-location endpoint to get store_id

    Args:
        pincode (str): Indian pincode (e.g., "110033")

    Returns:
        tuple: (requests.Session, str) - Configured session and store ID
    """

    # Step 1: Get place_id from pincode
    suggestions_url = f"https://instamart.in/api/instamart/maps/suggestions?input={pincode}"
    session = create_session_with_retries()

    response = session.get(suggestions_url, headers=DEFAULT_HEADERS)
    suggestions_data = response.json()

    # Extract place_id from response
    place_id = suggestions_data.get("data", [])[0].get("place_id", "")

    # Step 2: Get location details using place_id
    address_url = f"https://instamart.in/api/instamart/maps/address-widgets/v2?place_id={place_id}"
    address_response = session.get(address_url, headers=DEFAULT_HEADERS)
    address_data = address_response.json()

    # Extract latitude, longitude, and address
    location = address_data.get("data", {}).get("address", {}).get("location", {})
    latitude = location.get("latitude", "")
    longitude = location.get("longitude", "")
    subtitle = address_data.get("data", {}).get("address", {}).get("subtitle", "")

    # Step 3: Set location and get store_id
    location_url = "https://instamart.in/api/instamart/home/select-location/v2"

    payload = {
        "data": {
            "lat": latitude,
            "lng": longitude,
            "address": subtitle,
            "addressId": "",
            "annotation": subtitle,
            "clientId": "INSTAMART-APP"
        }
    }

    location_response = session.post(location_url, headers=DEFAULT_HEADERS, json=payload)
    location_data = location_response.json()

    # Extract store_id from response
    try:
        store_id = location_data.get("data", {}).get("configs", {}).get("IM_PAGE_CONFIGS", {}).get("configInfo", [])[
            0].get("card", {}).get("podDetails", {}).get("podId", "")
    except (IndexError, KeyError, AttributeError):
        store_id = ""

    return session, store_id


def extract_product_data(html_content, web_pid):
    """
    Extract product information from the HTML response.

    Args:
        html_content (requests.Response): Response object from product page request
        web_pid (str): Product ID being scraped

    Returns:
        dict: Extracted product data with all relevant fields
        bool: Flag indicating if extraction was successful
    """
    item = {}
    flag = 0

    try:
        # Parse HTML and extract initial state data
        selector = Selector(html_content)
        script_data = selector.xpath('//script[contains(text(),"window.___INITIAL_STATE___ =")]/text()').get()

        if not script_data:
            return item, flag

        # Extract JSON data from script tag
        json_str = script_data.split('window.___INITIAL_STATE___ = ')[1].split(';  var App =')[0]
        output = json.loads(json_str)

        # Check if product data exists
        if output.get('homeV2', {}).get('statusCode') == 0:
            flag = 1

            # Get product details from response
            product_data = output.get('productV2', {}).get('itemData', {})
            product_id = product_data.get('productId', web_pid)

            # Extract pricing
            variation = product_data.get('variations', [{}])[0]
            price_data = variation.get('price', {})

            # Try to get prices from HTML (fallback) or JSON
            price_rp = selector.xpath('//div[@data-testid="itemMRPPrice"]/div[2]/text()').get('')
            price_sp = selector.xpath('//div[@data-testid="itemMRPPrice"]/div[1]/text()').get('')

            if not price_rp:
                price_rp = int(price_data.get('mrp', {}).get('units', 0))
                price_sp = int(price_data.get('offerPrice', {}).get('units', 0))

            # Extract images
            image_ids = variation.get('imageIds', [])
            pdp_image_count = len(image_ids)

            hero_image = ""
            all_images = []
            if pdp_image_count > 0:
                hero_image = build_image_url(image_ids[0])
                all_images = [build_image_url(img_id) for img_id in image_ids]

            # Extract availability
            if product_data.get('inStock', False):
                osa_remark = "IN STOCK"
                osa = 1
            else:
                osa_remark = "OSS"
                osa = 0

            # Extract discount
            discount_desc = price_data.get('offerApplied', {}).get('listingDescription', '')
            discount = 0
            if discount_desc:
                try:
                    percetage_sign = discount_desc.index("%")
                    discount = int(discount_desc[:percetage_sign].strip())
                except (ValueError, TypeError):
                    discount = 0

            # Extract seller name
            seller_name = ""
            cards = output.get('productV2', {}).get('cards', [])
            for card in cards:
                try:
                    card_title = card.get('card', {}).get('card', {}).get('title', '')
                    if 'Seller Details' in card_title:
                        seller_description = card.get('card', {}).get('card', {}).get('description', '')
                        match = re.search(r"Seller Name:\s*(.+)", seller_description)
                        if match:
                            seller_name = match.group(1).strip().split('<br>')[0]
                        break
                except (KeyError, AttributeError):
                    continue

            # Extract description
            description = ""
            for card in cards:
                try:
                    card_title = card.get('card', {}).get('card', {}).get('title', '')
                    if 'Description'.lower() in card_title.lower():
                        desc_text = card.get('card', {}).get('card', {}).get('description', '')
                        description = desc_text.strip().split('</p>')[0].replace('<p>', '')
                        break
                except (KeyError, AttributeError):
                    continue

            # Build product item dictionary
            item = {
                "marketplace": "Instamart",
                "extracted_web_pid": web_pid,
                "pdp_title_value": product_data.get('displayName', ''),
                "extracted_brand_name": product_data.get('brand', ''),
                "price_rp": float(price_rp) if price_rp else 0.0,
                "price_sp": float(price_sp) if price_sp else 0.0,
                "savings": 0,
                "pdp_discount_value": float(discount),
                "pdp_desc_value": description,
                "pdp_image_count": pdp_image_count,
                "pdp_image_url": hero_image,
                "pdp_image_url_all": ",".join(all_images),
                "reseller_name_crawl": seller_name,
                "osa": osa,
                "osa_remark": osa_remark,
                'deal_flag': 0,
                "pdp_page_url": f"https://instamart.in/p/{web_pid}",
                "created_by": "System",
                "created_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": 1
            }

            print(f"MRP: {item['price_rp']}")
            print(f"Sale Price: {item['price_sp']}")
            print(f"OSA Remark: {item['osa_remark']}")

    except Exception as e:
        print(f"Error extracting product data: {str(e)}")
        return item, 0

    return item, flag


def scrape_instamart_product(web_pid, pincode, max_retries=5):
    """
    Main function to scrape a product from Instamart.

    Args:
        web_pid (str): Product ID to scrape
        pincode (str): Delivery pincode
        max_retries (int): Number of retry attempts

    Returns:
        dict: Scraped product data or empty dict if failed
    """
    print(f"\n{'=' * 80}")
    print(f"Scraping Product: {web_pid} | Pincode: {pincode}")
    print(f"{'=' * 80}\n")

    # Set location and get session
    session, store_id = set_pincode_location(pincode)

    # Build product URL
    product_url = f"https://instamart.in/p/{web_pid}"

    # Attempt to scrape with retries
    for attempt in range(max_retries):
        try:
            # Random delay between requests
            time.sleep(0.25)

            # Set user agent
            headers = PDP_HEADERS.copy()
            headers["User-Agent"] = random.choice(USER_AGENTS)

            # Make the request
            response = session.get(product_url, headers=headers)
            time.sleep(0.25)

            print(f"Attempt {attempt + 1}/{max_retries} - Status: {response.status_code}")

            # Extract product data
            product_data, success = extract_product_data(response, web_pid)

            if success:
                print("✓ Product data extracted successfully")
                return product_data
            else:
                print(f"✗ Failed to extract data on attempt {attempt + 1}")

        except Exception as e:
            print(f"✗ Error on attempt {attempt + 1}: {str(e)}")
            continue

    print(f"✗ Failed to scrape product after {max_retries} attempts")
    return {}


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Main entry point for testing the scraper.
    """
    # Test parameters
    test_pincode = "110033"
    test_product_id = "AOLIZO3IXR"

    # Scrape the product
    result = scrape_instamart_product(test_product_id, test_pincode)

    # Print results
    print("\n" + "=" * 80)
    print("SCRAPING RESULTS")
    print("=" * 80)

    if result:
        print("\nSuccessfully scraped product data:")
        print(f"Product ID: {result.get('extracted_web_pid')}")
        print(f"Product Name: {result.get('pdp_title_value')}")
        print(f"Brand: {result.get('extracted_brand_name')}")
        print(f"MRP: ₹{result.get('price_rp')}")
        print(f"Selling Price: ₹{result.get('price_sp')}")
        print(f"Discount: {result.get('pdp_discount_value')}%")
        print(f"Availability: {result.get('osa_remark')}")
        print(f"Seller: {result.get('reseller_name_crawl')}")
        print(f"Images: {result.get('pdp_image_count')}")
        print(f"Product URL: {result.get('pdp_page_url')}")
    else:
        print("\nFailed to scrape product data")