import requests

from dataclasses import dataclass

from pymongo import MongoClient

from stock_crawler.settings import MONGODB_URI, MONGODB_COLLECTION, MONGODB_DB


MONGODB_CLIENT = MongoClient(MONGODB_URI)
MONGODB_STOCK_CRAWLER = MONGODB_CLIENT[MONGODB_DB][MONGODB_COLLECTION]

@dataclass
class LogType:
    INFO: int=1
    WARNING: int=2
    ERROR: int=3


def requests_retry(url, total_times=1, timeout=10):
    times = 0
    while (times := times + 1) <= total_times:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return True, response
            elif response.status_code != 200 and times > total_times:
                return False, response
        except requests.RequestException as e:
            return None, e.__repr__()
