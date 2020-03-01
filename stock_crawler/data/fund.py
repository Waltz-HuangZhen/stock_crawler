FUND_CODE_CN_MAPPING = {
    '净值日期': 'date',
    '单位净值': 'nav',
    '累计净值': 'accnav',
    '日增长率': 'growth_rate',
    '申购状态': 'purchased',
    '赎回状态': 'redemption',
    '分红送配': 'dividend',
    '每万份收益': 'ten_thousands_annual',
    '7日年化收益率（%）': 'seven_day_annual_yield',
    '最近运作期年化收益率': 'last_operating_period_annual_yield',
    '每百份收益': 'hundred_annual',
    '每百万份收益': 'million_annual'
}


def mongodb_fund_code_data_formatter(fund_code):
    formatted_fund_code = {}
    for k, v in fund_code.items():
        if isinstance(v, str):
            if k == 'date':
                formatted_fund_code[k] = v[:10]
            if k in ['nav', 'accnav']:
                formatted_fund_code[k] = float(v)
            if k in ['growth_rate', 'ten_thousands_annual', 'seven_day_annual_yield',
                     'last_operating_period_annual_yield', 'hundred_annual', 'million_annual']:
                tmp = v.replace('%', '')
                formatted_fund_code[k] = float(tmp) if tmp else None
    fund_code.update(formatted_fund_code)
