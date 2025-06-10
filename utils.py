from contextlib import closing

import requests


# 实时打印
def rt_print(message=""):
    print(message, flush=True)
