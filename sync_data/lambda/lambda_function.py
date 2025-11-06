import os
import hashlib
import requests
import json
from bs4 import BeautifulSoup
import boto3



BLS_URL = "https://download.bls.gov/pub/time.series/pr/"
BLS_BASE_URL = "https://download.bls.gov"
API_URL = "https://honolulu-api.datausa.io/tesseract/data.jsonrecords?cube=acs_yg_total_population_1&drilldowns=Year%2CNation&locale=en&measures=Population"
RAW_BUCKET = os.environ.get("RAW_BUCKET", "raw-data")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ENDPOINT_URL = os.environ.get("ENDPOINT_URL")  # LocalStack endpoint, if any

LOCAL_DIR = "/tmp/bls_data"
os.makedirs(LOCAL_DIR, exist_ok=True)

s3 = boto3.client("s3", endpoint_url=ENDPOINT_URL, region_name=AWS_REGION)
HEADERS = {
    "User-Agent": "nishantkanungo593@gmail.com"
}



def file_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def s3_file_md5(bucket, key):
    try:
        resp = s3.head_object(Bucket=bucket, Key=key)
        return resp["ETag"].strip('"')
    except s3.exceptions.ClientError:
        return None

def lambda_handler(event, context):

    # Part 1: Sync BLS CSV files

    resp = requests.get(BLS_URL, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    bls_files_hrefs = [
        node.get("href") for node in soup.find_all("a")
        if node.get("href") and (node.get("href").endswith(".Current") or node.get("href").endswith(".series"))
    ]

    s3_objects = s3.list_objects_v2(Bucket=RAW_BUCKET)
    s3_keys = {obj["Key"] for obj in s3_objects.get("Contents", [])}

    for filename in bls_files_hrefs:
        file_name = filename.split("/")[-1]
        local_path = os.path.join(LOCAL_DIR, file_name)
        url = f"{BLS_BASE_URL}{filename}"

        file_resp = requests.get(url, headers=HEADERS)
        file_resp.raise_for_status()

        with open(local_path, "wb") as f:
            f.write(file_resp.content)

        local_hash = file_md5(local_path)
        s3_hash = s3_file_md5(RAW_BUCKET, file_name)

        if s3_hash == None or local_hash != s3_hash:
            s3.upload_file(local_path, RAW_BUCKET, file_name)

    # Delete removed files
    bls_file_names = [bls_file.split("/")[-1] for bls_file in bls_files_hrefs]
    for s3_key in s3_keys:
        if s3_key not in bls_file_names:
            s3.delete_object(Bucket=RAW_BUCKET, Key=s3_key)

    print(f"BLS CSV sync completed: {len(bls_files_hrefs)} files updated.")



    # Part 2: Fetch API JSON
    api_resp = requests.get(API_URL)
    api_resp.raise_for_status()
    api_data = api_resp.json()

    api_file_name = "population_data.json"
    local_api_file = os.path.join(LOCAL_DIR, api_file_name)

    with open(local_api_file, "w") as f:
        json.dump(api_data, f)

    s3.upload_file(local_api_file, RAW_BUCKET, api_file_name)

    print("Population API JSON synced successfully.")


    return {
        "statusCode": 200,
        "body": "BLS CSV and Population API JSON synced to S3"
    }
