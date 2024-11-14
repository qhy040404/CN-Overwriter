from contextlib import closing

import requests


# 实时打印
def rt_print(message=""):
    print(message, flush=True)


# 下载文件
def download_file(url, path):
    with closing(requests.get(url, stream=True)) as response:
        chunk_size = 10240  # 单次请求最大值
        content_size = int(response.headers['content-length'])  # 内容体总大小
        data_count = 0
        progresses = []
        with open(path, "wb") as file:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)
                data_count = data_count + len(data)
                progress = int(data_count / content_size * 100)
                if progress not in progresses:
                    progresses.append(progress)
                    rt_print(f"Progress: {progress} %")
