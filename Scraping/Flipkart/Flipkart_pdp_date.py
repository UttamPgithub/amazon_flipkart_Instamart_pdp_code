import sys
import os
import time
import random
import json
import logging
from datetime import datetime
import pytz
import pymysql
from tabulate import tabulate
from curl_cffi import requests
from scrapy.selector import Selector
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS_LOCATION = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "flipkart_secure": "true",
    "Host": "2.rome.api.flipkart.com",
    "Origin": "https://www.flipkart.com",
    "Referer": "https://www.flipkart.com/",
    "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "X-User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36 FKUA/website/41/website/Desktop"
}

HEADERS_PRODUCT = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Host": "www.flipkart.com",
    "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
}

INITIAL_COOKIES = {
    "T": "TI178065175943100092258554936004205572872652512204650172104091095753",
    "K-ACTION": "null",
    "vh": "730",
    "vw": "1536",
    "dpr": "1.25",
    "vd": "VIB41C83B8F1BE4E78BFEB1997DA9314FD-1780651765752-1.1780651765.1780651765.157702074",
    "S": "d1t12Slc6PxE/MjkiPz8tPz9MDTMs/RDxPq7e6muE5RFWzjcUQYKFMiBVAHniGDkqPhG2Umkl5pLOJuqWyJD2U1ObSg==",
    "SN": "VIB41C83B8F1BE4E78BFEB1997DA9314FD.TOK5766407DC276487697A0EF08AFFA2B81.1780651790147.LO"
}
session = requests.Session(impersonate='chrome')

web_pid ="CHTHE5F76GHVFSEH"
url_location = "https://2.rome.api.flipkart.com/api/4/location/update"
payload_location = {
  "geoLocation": {
    "latitude": 19.0803885,
    "longitude": 72.8468571
  },
  "addressInfo": {
    "addressLine1": "Santacruz East, Station Road, Anand Nagar, Vakola, Anand Vihar Society",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400055"
  },
  "redirectionUrl": "/abc/p/itmce4d794d6ccdf?pid=CHTHE5F76GHVFSEH&marketplace=HYPERLOCAL",
  "marketplace": "HYPERLOCAL"
}


session.post(url_location, headers=HEADERS_LOCATION, json=payload_location, timeout=10)
url_product = f"https://www.flipkart.com/abc/p/itmce4d794d6ccdf?pid=CHTHE5F76GHVFSEH&marketplace=HYPERLOCAL"

response = session.get(url_product, headers=HEADERS_PRODUCT, timeout=20)
if response.status_code == 200:
    html_repos = Selector(text=response.text)
    try:
        script_data = html_repos.xpath('//script[contains(text(),"window.__INITIAL_STATE__ =")]/text()').get()
        if script_data:
            json_html = script_data.split('window.__INITIAL_STATE__ = ')[1].split('}}};')[0] + '}}}'
    except:
        json_html = ''
item = dict()
try:
    response_text = json_html
    json_data = json.loads(response_text)

    page_data = json_data.get("multiWidgetState", {}).get("pageDataResponse", {})
    page_context = page_data.get("pageContext", {})

    psi = page_context.get("fdpEventTracking", {}).get("events", {}).get("psi", {})

    # -------------------------
    # PRODUCT BASIC INFO
    # -------------------------

    product_id = page_context.get("productId", web_pid)
    try:
        schema_data = page_data.get("seoData", {}).get("schema", [{}])[0]
    except:
        schema_data = {}

    product_title = schema_data.get("name", "")

    product_description = schema_data.get("description", "")

    brand = psi.get("bd") or schema_data.get("brand", {}).get("name", "")

    grammage = ""
    swa = psi.get("swa", [])
    if swa:
        grammage = swa[0].get("attributeValue", "")

    # -------------------------
    # IMAGE
    # -------------------------

    image_list = schema_data.get("image", [])

    image_url = ""
    image_url_all = ""

    if image_list:
        image_url = image_list[0]

        for img in image_list:
            if image_url_all:
                image_url_all = image_url_all + "|" + img
            else:
                image_url_all = img

    image_count = psi.get("pas", {}).get("imagesCount", 0)
    video_count = psi.get("pas", {}).get("videosCount", 0)

    # -------------------------
    # PRICE
    # -------------------------

    price_data = psi.get("ppd", {})

    sp = price_data.get("fsp", 0)
    mrp = price_data.get("mrp", 0)

    if mrp:
        discount = round(((mrp - sp) / mrp) * 100, 2)
    else:
        discount = 0

    # -------------------------
    # RATINGS
    # -------------------------

    rating_data = psi.get("pr", {})

    rating = rating_data.get("rating", 0)
    rating_count = rating_data.get("ratingsCount", 0)
    review_count = rating_data.get("reviewsCount", 0)

    rating_1 = rating_2 = rating_3 = rating_4 = rating_5 = 0

    breakup = rating_data.get("individualRatingsCount", [])
    for r in breakup:
        val = r.get("ratingValue")
        cnt = r.get("ratingCount", 0)

        if val == 1:
            rating_1 = cnt
        elif val == 2:
            rating_2 = cnt
        elif val == 3:
            rating_3 = cnt
        elif val == 4:
            rating_4 = cnt
        elif val == 5:
            rating_5 = cnt

    # -------------------------
    # AVAILABILITY
    # -------------------------

    availability = psi.get("pls", {}).get("availabilityStatus")

    if availability == "IN_STOCK":
        osa = 1
        osa_remark = "INSTOCK"
    else:
        osa = 0
        osa_remark = "OOS"

    # -------------------------
    # SELLER
    # -------------------------

    seller_name = psi.get("pls", {}).get("sellerName") or psi.get("pls", {}).get("sellerId", "")

    item["marketplace"] = "Flipkart Minutes"
    item["extracted_web_pid"] = web_pid
    item["pdp_title_value"] = product_title
    item["pdp_desc_value"] = product_description
    item["extracted_brand_name"] = brand
    item["pdp_rating_value"] = rating
    item["pdp_rating_count"] = rating_count
    item["pdp_review_count"] = review_count
    item["one_star"] = rating_1
    item["two_star"] = rating_2
    item["three_star"] = rating_3
    item["four_star"] = rating_4
    item["five_star"] = rating_5
    item["pdp_number_of_bulletin"] = 0
    item["delivery_date"] = ""
    item["price_rp"] = mrp
    item["price_sp"] = sp
    item["pdp_discount_value"] = discount
    item["pdp_image_count"] = image_count
    item["pdp_image_url"] = image_url
    item["pdp_image_url_all"] = image_url_all
    item["osa"] = osa
    item["osa_remark"] = osa_remark
    item["pdp_page_url"] = url_product
    item["created_by"] = "System"
    item["status"] = "1"
    item["reseller_name_crawl"] = seller_name

    table_data = [[key, value] for key, value in item.items()]
    print(tabulate(table_data, headers=['Field', 'Value'], tablefmt='grid'))
except Exception as e:
    print("Parsing Error:", e)
