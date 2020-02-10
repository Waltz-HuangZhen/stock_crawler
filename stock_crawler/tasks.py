import requests
import json

from stock_crawler.celery import app
from stock_crawler.settings import (
    NORMAL_TASK_TIMELIMIT, NORMAL_TASK_SOFTTIMELIMIT
)
from stock_crawler.models import Log, FundCode
from stock_crawler.utils.utils import LogType


@app.task(queue='sc_crawler', soft_time_limit=NORMAL_TASK_SOFTTIMELIMIT, time_limit=NORMAL_TASK_TIMELIMIT)
@Log.log_this()
def create_or_update_fund_code():
    status = {
        'status': LogType.INFO,
        'message': 'Success(total: {}, created: {}, updated: {})'
    }
    created_count = 0
    try:
        funds_str = requests.get('http://fund.eastmoney.com/js/fundcode_search.js', timeout=60).text
        funds_list = json.loads(funds_str[8:-1])
        count = len(funds_list)
        for fund in funds_list:
            _, created = FundCode.objects.update_or_create(
                code=fund[0],
                defaults={
                    'code': fund[0],
                    'short_name': fund[1],
                    'name': fund[2],
                    'fund_type': fund[3],
                    'pinyin_name': fund[4]
                }
            )
            created_count += int(created)
    except Exception as e:
        status['message'] = e.__repr__()
        status['status'] = LogType.ERROR
        return status, False
    status['message'] = status['message'].format(count, created_count, count-created_count)
    return status, True
