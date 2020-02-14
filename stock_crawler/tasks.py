import random
import requests
import json
import time
import re

from lxml import etree

from celery import group

from stock_crawler.celery import app
from stock_crawler.settings import (
    NORMAL_TASK_TIMELIMIT, NORMAL_TASK_SOFTTIMELIMIT, CRAWLER_TASK_TIMELIMIT, CRAWLER_TASK_SOFTTIMELIMIT
)
from stock_crawler.models import Log, FundCode, FundCodeDayWorth
from stock_crawler.utils.utils import LogType, requests_retry


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


@app.task(queue='sc_crawler', soft_time_limit=CRAWLER_TASK_SOFTTIMELIMIT, time_limit=CRAWLER_TASK_TIMELIMIT)
@Log.log_this(save_param=True)
def crawl_all_funds(start_date=None, end_date=None):
    status = {
        'status': LogType.INFO,
        'message': 'Successfully started to crawl {} stocks.'
    }
    count = 0
    try:
        codes = FundCode.objects.values_list('code', flat=True).all().iterator(chunk_size=500)
        for code in codes:
            crawl_fund.s(code, start_date, end_date).apply_async()
            count += 1
    except Exception as e:
        status['message'] = e.__repr__()
        status['status'] = LogType.ERROR
        return status, False
    status['message'] = status['message'].format(count)
    return status, True


@app.task(queue='sc_fund_crawler', soft_time_limit=CRAWLER_TASK_SOFTTIMELIMIT, time_limit=CRAWLER_TASK_TIMELIMIT)
@Log.log_this(save_param=True)
def crawl_fund(code, start_date=None, end_date=None):
    status = {
        'status': LogType.INFO,
        'message': 'Successfully crawled {} pages(total {}, fail {}).'
    }
    base_url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx' \
               '?type=lsjz&code={code}&page={page}&per=50'
    total_times = 10
    task_group = []
    page = 1
    result = None
    try:
        if start_date:
            base_url += '&sdate={}'.format(start_date)
        if end_date:
            base_url += '&edate={}'.format(end_date)

        response_status, response = requests_retry(base_url.format(**locals()), total_times=total_times)
        if response_status is not True:
            status['message'] = 'Failed to crawl {}. Error: {}'.format(
                code, response if response_status is None else response.text
            )
            status['status'] = LogType.ERROR
            return status, False

        data_dict = json.loads(re.sub('([a-zA-Z]*?):', '"\g<1>":', response.text[12:-1]))
        task_group.append(crawl_fund_page.s(code, data_dict=data_dict))
        for i in range(page + 1, data_dict['pages'] + 1):
            page = i
            task_group.append(crawl_fund_page.s(code, url=base_url.format(**locals())))

        task_group = group(task_group)
        result = task_group.apply_async()
        while result.waiting():
            time.sleep(2)
    except Exception as e:
        message = e.__repr__()
        status['status'] = LogType.ERROR
        return status, False
    finally:
        if result is not None:
            if status['status'] == LogType.ERROR:
                result.revoke()
            successful_num = failed_num = 0
            for r in result.results:
                successful_num += int(r.result is True)
                failed_num += int(r.result is False)
            not_crawled_num = page - successful_num - failed_num
            status['message'] = status['message'].format(successful_num, page, failed_num)
        else:
            status['message'] = 'Failed to crawl {}. Error: Tasks\' result is None.'.format(code)
    return status, True


@app.task(queue='sc_fund_page_crawler', soft_time_limit=NORMAL_TASK_SOFTTIMELIMIT, time_limit=NORMAL_TASK_TIMELIMIT)
@Log.log_this(save_param=True)
def crawl_fund_page(code, data_dict=None, url=None):
    status = {
        'status': LogType.INFO,
        'message': ''
    }
    total_times = 10
    try:
        if url is not None:
            time.sleep(random.randint(0, 15) / 10)
            response_status, response = requests_retry(url, total_times=total_times)
            if response_status is not True:
                status['message'] = 'Failed to crawl {}. URL: {} \nError: {}'.format(
                    code, url, response if response_status is None else response.text
                )
                status['status'] = LogType.ERROR
                return status, False
            data_dict = json.loads(re.sub('([a-zA-Z]*?):', '"\g<1>":', response.text[12:-1]))
        if data_dict is not None:
            html_data = etree.HTML(data_dict['content'])
            for html_col in html_data.xpath('//table/tbody/tr'):
                data = [str(d.xpath('string(.)')) for d in html_col]
                if len(data) > 6:
                    FundCodeDayWorth.objects.create(
                        fund_code_id=code,
                        date=data[0].replace('*', ''),
                        nav=float(data[1] or 0),
                        accnav=float(data[2] or 0),
                        growth_rate=float(data[3][:-1] or 0),
                        purchased=data[4],
                        redemption=data[5],
                        dividend=data[6]
                    )
                elif len(data) == 6:
                    FundCodeDayWorth.objects.create(
                        fund_code_id=code,
                        date=data[0].replace('*', ''),
                        ten_thousands_annual=float(data[1] or 0),
                        seven_day_annual_yield=float(data[2][:-1] or 0),
                        purchased=data[3],
                        redemption=data[4],
                        dividend=data[5]
                    )
    except Exception as e:
        status['message'] = 'Failed to crawl {}. \nError: '.format(code) + e.__repr__()
        status['status'] = LogType.ERROR
        return status, False
    return None, True
