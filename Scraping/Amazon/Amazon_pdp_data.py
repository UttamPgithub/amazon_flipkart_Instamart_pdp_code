import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timedelta
from scrapy import Selector


def fetch_amazon_product(url):
    """
    Fetch Amazon product page with proper headers and cookies
    """
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "device-memory": "8",
        "downlink": "5.85",
        "dpr": "1.25",
        "ect": "4g",
        "Host": "www.amazon.in",
        "Referer": url,
        "rtt": "250",
        "sec-ch-device-memory": "8",
        "sec-ch-dpr": "1.25",
        "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
        "sec-ch-ua-full-version-list": '"Chromium";v="152.0.7977.77", "Not?A_Brand";v="24.0.0.0", "Google Chrome";v="152.0.7977.77"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-ch-viewport-width": "1536",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Service-Worker-Navigation-Preload": "true",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "viewport-width": "1536"
    }

    cookies = {
        "session-id": "522-7172470-7091624",
        "session-id-time": "2082787201l",
        "sst-acbin": "Sst1|PQIIlGLOFLcqqW1fe9CbRUHLB_IyP5Zu8iGJitk7el8UimEYBnEsHEkGdLlaHpRglRywf9LmHwhuPdQr_FspAqA7nG5_NnA92HgdEMGRrTSWqIgzfVQhCPbcGZogA5XNz9NgdNnGs0BEkuT1RH-ioazigA-bmCTifSCl4RyKpcwL8B_--gEX1zL0u9v0h7i01ZTYaY4fK1zIJy46CH7WNkZxBMQ5pbKFhgtJH8Jpn26OszvgmeXtbjjNAAAB3d5UdeGa",
        "i18n-prefs": "INR",
        "lc-acbin": "en_IN",
        "ubid-acbin": "525-5283892-6579813",
        "session-token": "OeTzP7GXxAw7MwJFvJGBWsCCFNGKtbwYjj38SKH4UcP1mwtvZa52zqcoK+G7GpRHKQFHBOPM2aPsJhr/jFIkevpdv7ChPTJ6zyM6tiCHarwTP2yoyZOfp/cGzxBd/YdkK24m5VAGaYvVtJJc7iECSYUC0XRmqpTk9SOwei4/7/yrhG5/lCr6K7bEgy0mh7kTGbk6o3Dtl7gQCp61mTllJmpscjPzhVkT",
        "csm-hit": "tb:FT91YC46V5EFJ8AKQ27Y+s-FT91YC46V5EFJ8AKQ27Y|1788706300934&t:1788706300934&adb:adblk_no",
        "cmc": "3abAxxFdNBtEc9Gb6ZUYEZFt7tSJ0yNMx/5S11UdBztjyz96CThMm9b86w17kDxq0X7hP5VEnfXZBChslr+0MBpIn926ZhaT1Hl/d9ARnf7tmDpgWaHFy8GSFi5U+Txfq1ibvQ4lsosXyvNiF5KFwhs3Rn6cYnGNADY8bjJdmLR1VeANDCYmqJqeaEhAtzW5NE3rKjrJnZVh4J4di8CgADp90pXlipj5ctISvBy+mzObTRgBZuaaJcmO0Zl2KE4JFH0lRk4lx9/YmG33ojowkSMWTfla3Sr9/PV+5j6n486iXTCn5jRqshJU",
        "rxc": "AIPw7zY+upWmqf2C5Cg"
    }

    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return None


def extract_sku_data(html_content):
    """
    Extract SKU data from Amazon product page HTML using BeautifulSoup
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    html_sele = Selector(text=html_content)

    # print("🔍 Extracting SKU data")
    sku_name, rating_value, rating_count, osa = None, 0, 0, 0

    # addition
    is_fresh = 0
    sellers_str = ""
    delivery_date = ""

    price_sp = price_rp = 0
    feature_bullets, bulletins_count = None, 0
    star_5 = star_4 = star_3 = star_2 = star_1 = None
    reseller_name = ""
    sellers = []

    # Extract SKU Name
    try:
        sku_name_element = soup.find('h1', class_=lambda x: x and 'a-size-large' in x and 'a-spacing-none' in x)
        if sku_name_element:
            sku_name = sku_name_element.text.strip()
    except:
        # super saver
        try:
            sku_name = soup.find('span', {'id': 'productTitle'}).text.strip()
        except:
            pass

    # Extract Price
    try:
        price_sp = html_sele.xpath('//span[@id="tp_price_block_total_price_ww"]/span/text()').get('')

    except Exception as e:
        pass

    try:
        # Default: if MRP not found, fallback to selling price
        price_rp = html_sele.xpath('//span[contains(text(),"M.R.P.")]//following-sibling::span/span[@class="a-offscreen"]/text()').extract_first()
    except Exception as e:
        price_rp = 0


    if not price_rp:
        price_rp = price_sp

    price_rp = int(float(re.sub(r'[^\d.]', '', str(price_rp)))) if price_rp else 0
    price_sp = int(float(re.sub(r'[^\d.]', '', str(price_sp)))) if price_sp else 0

    # Extract Delivery Date
    delivery_date = None
    try:
        # Case 1: Primary delivery message
        delivery_element = soup.find('div', {'id': 'mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE'})
        if delivery_element and delivery_element.text.strip():
            delivery_text = delivery_element.text.strip()
            pattern = r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b,?\s+\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\b'
            match = re.search(pattern, delivery_text)
            delivery_date = match.group() if match else delivery_text
        else:
            # Case 2: bold span in alm-delivery-message
            delivery_element = soup.find('div', {'id': 'alm-delivery-message'})
            if delivery_element:
                bold_span = delivery_element.find('span', class_=lambda x: x and 'a-text-bold' in x)
                if bold_span and bold_span.text.strip():
                    delivery_date = bold_span.text.strip()
                elif delivery_element.text.strip():
                    delivery_date = delivery_element.text.strip()
            else:
                # Case 3: fallback entire delivery block
                delivery_element = soup.find('div', {'id': 'mir-layout-DELIVERY_BLOCK'})
                if delivery_element and delivery_element.text.strip():
                    delivery_date = delivery_element.text.strip()

    except Exception as e:
        pass

    # Extract Images
    def get_images(soup):
        image_list = []
        image_url = ""

        try:
            alt_images = soup.find('div', {'id': 'altImages'})
            if alt_images:
                thumbnails = alt_images.find_all('div', class_=lambda x: x and 'a-button-thumbnail' in x)
                for thumbnail in thumbnails:
                    img = thumbnail.find('img')
                    if img:
                        src = img.get('src')
                        if src and "common" not in src:
                            image_list.append(src)
                image_url = image_list[0] if image_list else ""
        except Exception as e:
            image_list = []
            image_url = ""

        return image_list, image_url

    image_list, image_url = get_images(soup)

    # Check "Add to Cart" / OSA
    try:
        right_col = soup.find('div', {'id': 'rightCol'})
        if right_col and "Add to cart" in right_col.text:
            osa = 1
    except:
        pass

    # Extract Ratings
    try:
        ratings = soup.find('div', {'id': 'averageCustomerReviews_feature_div'})
        if ratings:
            ratings_text = [i for i in ratings.text.splitlines() if i.strip()]
            for line in ratings_text:
                line = line.strip()
                if line.replace('.', '', 1).isdigit():
                    rating_value = float(line)
                elif "(" in line and ")" in line:
                    rating_count = int(''.join(filter(str.isdigit, line)))
    except:
        pass
    if not rating_value:
        ratings = soup.find('a', {'class': 'a-popover-trigger a-declarative mvt-cm-cr-review-stars-mini-popover'})
        rating_value = ''.join(ratings.text.splitlines()).strip().split(' ')[0]

        # Extract Feature Bullets
    try:
        bullets = soup.select('#feature-bullets ul li span')
        bulletins_count = len(bullets)
        feature_bullets = " | ".join([b.text.strip() for b in bullets if b.text.strip()])
    except:
        pass

    # Extract Star Ratings
    try:
        rating_histogram = soup.find('div', {'class': 'a-section a-spacing-none a-text-right aok-nowrap'})
        if rating_histogram:
            text = [i for i in ''.join(rating_histogram.text.lower().splitlines()).split('%') if i.strip()]
            star_5 = text[0]
            star_4 = text[1]
            star_3 = text[2]
            star_2 = text[3]
            star_1 = text[4]
    except:
        pass

    # Check if Amazon Fresh
    try:
        fresh = soup.find('div',
                          class_=lambda x: x and 'a-section' in x and 'a-spacing-micro' in x and 'a-padding-none' in x)
        if fresh:
            fresh_img = fresh.find('img', {'alt': 'Amazon Fresh'})
            if fresh_img:
                is_fresh = 1
    except Exception as e:
        pass

    # Extract Reseller Name
    try:
        # TRY 1
        try:
            reseller_name_element = soup.find('a', {'id': 'sellerProfileTriggerId'})
            if reseller_name_element:
                reseller_name = reseller_name_element.text.strip()
            else:
                reseller_name = ""
        except:
            reseller_name = ""

        # TRY 2
        if not reseller_name:
            try:
                sold_by_span = soup.find('span', string=re.compile(r'Sold by', re.I))
                if sold_by_span:
                    parent_td = sold_by_span.find_parent('td')
                    if parent_td:
                        next_td = parent_td.find_next_sibling('td')
                        if next_td:
                            link = next_td.find('a')
                            if link:
                                reseller_name = link.text.strip()
            except:
                reseller_name = ""

        # TRY 3 (OLD LOGIC)
        if not reseller_name:
            try:
                sold_by_span = soup.find('span', string=re.compile(r'Sold by', re.I))
                if sold_by_span:
                    next_a = sold_by_span.find_next('a')
                    if next_a:
                        reseller_name = next_a.text.strip()
            except:
                reseller_name = ""

        # Reject garbage values
        if (not reseller_name or
                any(x.lower() in reseller_name.lower() for x in
                    ["deliver to", "details", "see more", "free delivery"]) or
                re.search(r'\d{6}', reseller_name)):
            reseller_name = ""

    except:
        reseller_name = ""

    # Merchant Info Feature fallback
    if not reseller_name:
        try:
            merchant_div = soup.find('div', {'id': 'merchantInfoFeature_feature_div'})
            if merchant_div:
                element = merchant_div.find('div', recursive=False)
                if element:
                    element = element.find('div', recursive=False)
                    if element and element.text.strip():
                        reseller_name = element.text.strip()
        except Exception as e:
            pass

    # Amazon Fresh merchant info
    if not reseller_name:
        try:
            fresh_merchant = soup.find('div', {'id': 'fresh-merchant-info'})
            if fresh_merchant:
                link = fresh_merchant.find('a', href=re.compile(r'/sp\?'))
                if link:
                    reseller_name = link.text.strip()
        except:
            pass

    if not reseller_name:
        try:
            fresh_merchant = soup.find('div', {'id': 'fresh-merchant-info'})
            if fresh_merchant:
                span = fresh_merchant.find('span', class_=lambda x: x and 'a-size-small' in x and 'a-color-base' in x)
                if span and span.text.strip():
                    reseller_name = span.text.strip()
        except:
            pass

    if not reseller_name:
        try:
            shipper_span = soup.find('span', string=re.compile(r'Shipper / Seller', re.I))
            if shipper_span:
                next_a = shipper_span.find_next('a')
                if next_a:
                    reseller_name = next_a.text.strip()
        except:
            pass

    # Extract Best Seller Rank
    try:
        try:
            best_seller_elem = soup.find('span', string=re.compile(r'Best Sellers Rank', re.I))
            if best_seller_elem:
                best_seller = best_seller_elem.find_next('span')
                if best_seller:
                    best_seller = best_seller.text
            else:
                best_seller_elem = soup.find('li', string=re.compile(r'Best Sellers Rank', re.I))
                if best_seller_elem:
                    best_seller = best_seller_elem.text
                else:
                    best_seller = None
        except:
            best_seller = None

        if best_seller:
            try:
                best_seller_match = ' | '.join(best_seller.split(' Rank:')[1].split('\n'))
            except:
                best_seller_match = ' | '.join(best_seller.split('\n'))
            best_seller_rank = best_seller_match
        else:
            best_seller_rank = None

    except:
        best_seller_rank = None

    # Extract Category
    try:
        try:
            if best_seller:
                try:
                    category_parts = best_seller.split(' Rank:')[0].split('\n')
                    category_name = category_parts[-1].split('in')[1].strip()
                except:
                    category_name = best_seller.split('\n')[-1].split('in')[1].strip()
        except:
            try:
                breadcrumb_items = soup.find_all('ul', class_=lambda
                    x: x and 'a-unordered-list' in x and 'a-horizontal' in x and 'a-size-small' in x)
                if breadcrumb_items:
                    last_item = breadcrumb_items[-1].find_all('li')[-1]
                    category_name = last_item.text.strip()
                else:
                    category_name = ""
            except:
                category_name = ""
    except:
        category_name = ""

    # Extract Description
    try:
        description_element = soup.find('div', {'id': 'productDescription'})
        if description_element:
            desc_p = description_element.find('p')
            if desc_p:
                desc_span = desc_p.find('span')
                if desc_span:
                    description = desc_span.text.strip()
    except:
        description = None

    today = datetime.now()

    def parse_amazon_delivery(text):
        if not text:
            return None

        text = text.lower()

        # 1. Today / Tomorrow
        if "today" in text:
            return today.strftime("%Y-%m-%d")
        if "tomorrow" in text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")

        # 2. Range (18 - 22 April)
        match = re.search(r'(\d{1,2})\s*-\s*(\d{1,2})\s*(\w+)', text)
        if match:
            day = match.group(1)
            month = match.group(3)
            try:
                date_obj = datetime.strptime(f"{day} {month} {today.year}", "%d %B %Y")
                return date_obj.strftime("%Y-%m-%d")
            except:
                pass

        # 3. Full date (Saturday, 18 April / Friday, April 18)
        match = re.search(r'(\d{1,2})\s*(\w+)', text)
        if match:
            try:
                day = match.group(1)
                month = match.group(2)
                date_obj = datetime.strptime(f"{day} {month} {today.year}", "%d %B %Y")
                if date_obj < today:
                    date_obj = date_obj.replace(year=today.year + 1)
                return date_obj.strftime("%Y-%m-%d")
            except:
                pass

        # 4. "in 3 to 5 days"
        match = re.search(r'(\d+)\s*to\s*(\d+)\s*day', text)
        if match:
            days = int(match.group(1))
            return (today + timedelta(days=days)).strftime("%Y-%m-%d")

        return None

    # Parse delivery date
    try:
        if delivery_date:
            delivery_element = soup.find('div', {'id': 'deliveryBlockMessage'})
            if delivery_element:
                span = delivery_element.find('span', {'data-csa-c-delivery-time': True})
                if span:
                    delivery_date = span.get('data-csa-c-delivery-time')
            if delivery_date:
                delivery_date = parse_amazon_delivery(delivery_date)
    except:
        delivery_date = today.strftime("%Y-%m-%d")

    # Extract Video Count
    try:
        video_element = soup.find('span', {'id': 'videoCount'})
        if video_element:
            video_number_text = video_element.text.strip()
            video_number_match = re.search(r'\d+', video_number_text)
            if video_number_match:
                video_number = int(video_number_match.group())
            elif 'video' in video_number_text.lower():
                video_number = 1
            else:
                video_number = 0
        else:
            video_number = 0
    except:
        video_number = 0

    # Extract All Sellers (from aod panel)
    try:
        # Find all sellers in the aod-offer-soldBy divs
        seller_divs = soup.find_all('div', {'id': 'aod-offer-soldBy'})
        for seller_div in seller_divs:
            try:
                link = seller_div.find('a', class_=lambda x: x and 'a-size-small' in x and 'a-link-normal' in x)
                if link:
                    name = link.text.strip()
                    if name and "Deliver to" not in name and "Details" not in name and not re.search(r'\d{6}', name):
                        sellers.append(name)
            except:
                pass

        if reseller_name == "" and sellers:
            reseller_name = sellers[0]

        sellers_str = json.dumps(sellers)

    except Exception as e:
        if reseller_name:
            sellers = [reseller_name]
            sellers_str = json.dumps(sellers)
        else:
            sellers = []

    # print("✅ Extraction complete")
    return (sku_name, price_rp, price_sp, osa, rating_value, rating_count,
            feature_bullets, bulletins_count, star_1, star_2, star_3, star_4, star_5,
            reseller_name, is_fresh, sellers_str, delivery_date, image_url,
            image_list, description, video_number, best_seller_rank, category_name)


# Main execution
if __name__ == "__main__":
    # URL to scrape
    url = "https://www.amazon.in/dp/B07F8H9NYY?th=1"

    # Fetch the page
    print("Fetching product page...")
    html_content = fetch_amazon_product(url)

    if html_content:
        print("Page fetched successfully. Extracting data...")
        result = extract_sku_data(html_content)

        # Print results
        (sku_name, price_rp, price_sp, osa, rating_value, rating_count,
         feature_bullets, bulletins_count, star_1, star_2, star_3, star_4, star_5,
         reseller_name, is_fresh, sellers_str, delivery_date, image_url,
         image_list, description, video_number, best_seller_rank, category_name) = result

        print("\n=== EXTRACTED DATA ===")
        print(f"SKU Name: {sku_name}")
        print(f"Price (RP): ₹{price_rp}")
        print(f"Price (SP): ₹{price_sp}")
        print(f"OSA: {osa}")
        print(f"Rating: {rating_value} ({rating_count} reviews)")
        print(f"Feature Bullets: {feature_bullets[:100]}..." if feature_bullets else "Feature Bullets: None")
        print(f"Bulletins Count: {bulletins_count}")
        print(f"Stars: 5★={star_5}, 4★={star_4}, 3★={star_3}, 2★={star_2}, 1★={star_1}")
        print(f"Reseller: {reseller_name}")
        print(f"Is Fresh: {is_fresh}")
        print(f"Sellers: Amazon")
        print(f"Delivery Date: {delivery_date}")
        print(f"Image URL: {image_url}")
        print(f"Total Images: {len(image_list)}")
        print(f"Description: {description}..." if description else "Description: None")
        print(f"Video Count: {video_number}")
        print(f"Best Seller Rank: {best_seller_rank}")
        print(f"Category: {category_name}")
    else:
        print("Failed to fetch the product page.")