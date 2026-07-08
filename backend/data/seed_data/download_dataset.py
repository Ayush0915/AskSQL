import os
import urllib.request

FILES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv"
]

# We will try a few potential repository hosts for these raw CSV files
BASE_URLS = [
    "https://raw.githubusercontent.com/Ganesh7699/Brazilian-E-Commerce-OList/master/",
    "https://raw.githubusercontent.com/Ganesh7699/Brazilian-E-Commerce-OList/main/",
    "https://raw.githubusercontent.com/andresionek91/brazilian-ecommerce-analysis/master/data/",
    "https://raw.githubusercontent.com/mcs-jocelyn/olist-brazilian-ecommerce/master/data/",
    "https://raw.githubusercontent.com/tusharwalia/Olist-Brazilian-E-commerce-Dataset/master/"
]

output_dir = os.path.dirname(os.path.abspath(__file__))

print(f"Downloading files to: {output_dir}")

for file_name in FILES:
    dest_path = os.path.join(output_dir, file_name)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"{file_name} already exists and is not empty. Skipping.")
        continue
    
    success = False
    for base_url in BASE_URLS:
        url = base_url + file_name
        print(f"Trying to download {file_name} from {url}...")
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Successfully downloaded {file_name}!")
            success = True
            break
        except Exception as e:
            print(f"Failed to download from {url}: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
    
    if not success:
        print(f"ERROR: Could not download {file_name} from any source.")
