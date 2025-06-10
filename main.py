import os
import sys

import requests

from utils import rt_print

project = sys.argv[1]
if project == "hutao":
    project_key = "snap-hutao"
    github_release_api = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao/releases/latest"
    release_asset_index = 1
    patch_url = "https://api.snapgenshin.com/patch/hutao"
    should_overwrite = True
elif project == "deployment":
    project_key = "snap-hutao-deployment"
    github_release_api = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao.Deployment/releases/latest"
    release_asset_index = 0
    patch_url = "https://api.snapgenshin.com/patch/hutao-deployment"
    should_overwrite = False
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
