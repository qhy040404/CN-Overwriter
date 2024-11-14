import os
import sys

import boto3
import requests
from botocore.config import Config

from utils import download_file, rt_print


def core(file_path, bucket_file_name):
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
    s3_client.upload_file(file_path, bucket_name, bucket_file_name)


rt_print("CN Overwriter")
rt_print()

if len(sys.argv) == 1:
    rt_print("No arguments found!")
    rt_print("Fetching latest version")
    latest_release_data = requests.get("https://api.github.com/repos/DGP-Studio/Snap.Hutao/releases/latest").json()
    asset = latest_release_data["assets"][1]
    asset_url = asset["browser_download_url"]
    asset_url = "https://ghproxy.qhy04.cc/" + asset_url
    patch_url = "https://api.snapgenshin.com/patch/hutao"
    rt_print("Waiting Patch API to update")
    while True:
        patch_data = requests.get(patch_url).json()
        if patch_data["data"]["version"][:-2] == latest_release_data["tag_name"]:
            break
    rt_print("Overwriting download url to ghproxy")
    rt_print(requests.post("https://api.snapgenshin.com/patch/mirror",
                           headers={
                               "API-Token": os.getenv("OVERWRITE_TOKEN")
                           },
                           json={
                               "key": "snap-hutao",
                               "url": asset_url,
                               "mirror_name": "GitHub Proxy",
                               "mirror_type": "direct"
                           }).text)
    rt_print("Downloading latest version")
    download_file(asset_url, "Snap.Hutao.msix")
    core("Snap.Hutao.msix", asset["name"])
else:
    rt_print("Invalid arguments!")

if os.path.exists("Snap.Hutao.msix"):
    os.remove("Snap.Hutao.msix")
