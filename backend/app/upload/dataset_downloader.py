import os
import zipfile
import urllib.request
import logging
from pathlib import Path

logger = logging.getLogger("asksql-downloader")

EXPECTED_FILES = {
    "category_name_translation.csv": "product_category_name_translation.csv",
    "customers.csv": "olist_customers_dataset.csv",
    "order_items.csv": "olist_order_items_dataset.csv",
    "order_payments.csv": "olist_order_payments_dataset.csv",
    "order_reviews.csv": "olist_order_reviews_dataset.csv",
    "orders.csv": "olist_orders_dataset.csv",
    "products.csv": "olist_products_dataset.csv",
    "sellers.csv": "olist_sellers_dataset.csv"
}

def ensure_sample_datasets():
    sample_dir = Path(__file__).resolve().parent.parent / "data" / "sample_datasets"
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if all files exist
    all_exist = True
    for f in EXPECTED_FILES.keys():
        if not (sample_dir / f).exists():
            all_exist = False
            break
            
    if all_exist:
        return
        
    logger.info("Some or all sample datasets are missing. Downloading from public S3...")
    zip_path = sample_dir / "olist.zip"
    url = "https://wagon-public-datasets.s3.amazonaws.com/olist/olist.zip"
    
    try:
        # Download zip
        urllib.request.urlretrieve(url, zip_path)
        logger.info("Download completed. Extracting files...")
        
        # Unzip files
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(sample_dir)
            
        # Rename/move files
        for target, source in EXPECTED_FILES.items():
            source_path = sample_dir / source
            if not source_path.exists():
                # Maybe nested under olist/
                source_path = sample_dir / "olist" / source
            if source_path.exists():
                os.replace(source_path, sample_dir / target)
                
        # Cleanup zip file and any extracted directories if present
        if zip_path.exists():
            os.remove(zip_path)
        olist_dir = sample_dir / "olist"
        if olist_dir.exists():
            import shutil
            shutil.rmtree(olist_dir)
            
        logger.info("Sample datasets prepared successfully.")
    except Exception as e:
        logger.error(f"Failed to download/extract sample datasets: {e}")
        # Try to clean up
        if zip_path.exists():
            try:
                os.remove(zip_path)
            except Exception:
                pass
        raise e
