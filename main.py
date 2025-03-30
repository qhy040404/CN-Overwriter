import os
import sys
import threading

import boto3
import requests
from botocore.config import Config

from utils import download_file, rt_print


class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()


project = sys.argv[1]
if project == "hutao":
    project_key = "snap-hutao"
    github_release_api = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao/releases/latest"
    release_asset_index = 1
    patch_url = "https://api.snapgenshin.com/patch/hutao"
    download_file_name = "Snap.Hutao.msix"
    need_download = False
    should_overwrite = True
    cdn_mode = "preheat"
elif project == "deployment":
    project_key = "snap-hutao-deployment"
    github_release_api = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao.Deployment/releases/latest"
    release_asset_index = 0
    patch_url = "https://api.snapgenshin.com/patch/hutao-deployment"
    download_file_name = "Snap.Hutao.Deployment.exe"
    need_download = True
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
if need_download:
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
    s3_client.upload_file(download_file_name, bucket_name, asset["name"],
                          Callback=ProgressPercentage(download_file_name))
    rt_print()
    rt_print("Upload complete")
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
if need_download:
    rt_print("Preheating MinIO")
    minio_s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
        endpoint_url=os.getenv("MINIO_ENDPOINT"),
        config=config
    )
    minio_bucket_name = "hutao"
    minio_s3_client.upload_file(download_file_name, minio_bucket_name, asset["name"],
                                Callback=ProgressPercentage(download_file_name))
    rt_print()
    rt_print("Preheating complete")
rt_print(requests.get(f"https://api.qhy04.com/hutaocdn/{cdn_mode}?filename={asset["name"]}", headers={
    "Authorization": os.getenv("CDN_TOKEN")
}).text)

if os.path.exists("Snap.Hutao.msix"):
    os.remove("Snap.Hutao.msix")
if os.path.exists("Snap.Hutao.Deployment.exe"):
    os.remove("Snap.Hutao.Deployment.exe")
