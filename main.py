import os
import sys
import time

import boto3
import requests
from botocore.config import Config

from utils import download_file, rt_print

project = sys.argv[1]
if project == "hutao":
    project_key = "snap-hutao"
    github_release_api = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao/releases/latest"
    release_asset_index = 1
    patch_url = "https://api.snapgenshin.com/patch/hutao"
    download_file_name = "Snap.Hutao.msix"
    should_overwrite = True
    cdn_mode = "preheat"
elif project == "deployment":
    project_key = "snap-hutao-deployment"
    github_release_api = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao.Deployment/releases/latest"
    release_asset_index = 0
    patch_url = "https://api.snapgenshin.com/patch/hutao-deployment"
    download_file_name = "Snap.Hutao.Deployment.exe"
    should_overwrite = False
    cdn_mode = "refresh"
else:
    rt_print("Invalid project")
    sys.exit(1)

rt_print("CN Overwriter")
rt_print()
rt_print("Project Key: " + project_key)
rt_print("Fetching latest version")
latest_release_data = requests.get(github_release_api).json()
asset = latest_release_data["assets"][release_asset_index]
asset_url = asset["browser_download_url"]
asset_url = "https://ghproxy.qhy04.cc/" + asset_url
rt_print("Waiting Patch API to update")
while True:
    patch_data = requests.get(patch_url).json()
    if patch_data["data"]["version"][:-2] == latest_release_data["tag_name"]:
        break
if should_overwrite:
    rt_print("Add GitHub Proxy to Patch API")
    rt_print(requests.post("https://api.snapgenshin.com/patch/mirror",
                           headers={
                               "API-Token": os.getenv("OVERWRITE_TOKEN")
                           },
                           json={
                               "key": project_key,
                               "url": asset_url,
                               "mirror_name": "GitHub Proxy",
                               "mirror_type": "direct"
                           }).text)
rt_print("Downloading latest version")
download_file(asset_url, download_file_name)

rt_print("Starting upload...")
config = Config(signature_version='s3v4')
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
    endpoint_url=os.getenv("S3_ENDPOINT"),
    config=config
)
bucket_name = "hutao-distribute"
s3_client.upload_file(download_file_name, bucket_name, asset["name"])
if should_overwrite:
    rt_print("Add R2 to Patch API")
    rt_print(requests.post("https://api.snapgenshin.com/patch/mirror",
                           headers={
                               "API-Token": os.getenv("OVERWRITE_TOKEN")
                           },
                           json={
                               "key": project_key,
                               "url": f"https://hutao-dist.qhy04.cc/{asset["name"]}",
                               "mirror_name": "Cloudflare R2",
                               "mirror_type": "direct"
                           }).text)

rt_print("Preheating CDN Caches...")
rt_print("Preheating MinIO")
minio_s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    endpoint_url=os.getenv("MINIO_ENDPOINT"),
    config=config
)
minio_bucket_name = "hutao"
if project == "deployment":
    response = minio_s3_client.list_objects_v2(Bucket=bucket_name)
    for obj in response.get('Contents', []):
        rt_print(obj['Key'])
        if obj['Key'] == download_file_name:
            minio_s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
    time.sleep(1)
minio_s3_client.upload_file(download_file_name, minio_bucket_name, asset["name"])
rt_print(requests.get(f"https://api.qhy04.com/hutaocdn/{cdn_mode}?filename={asset["name"]}", headers={
    "Authorization": os.getenv("CDN_TOKEN")
}).text)

if os.path.exists("Snap.Hutao.msix"):
    os.remove("Snap.Hutao.msix")
if os.path.exists("Snap.Hutao.Deployment.exe"):
    os.remove("Snap.Hutao.Deployment.exe")
