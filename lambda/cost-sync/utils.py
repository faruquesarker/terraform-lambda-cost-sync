import datetime

def get_today_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_month_end_date():
    now = datetime.datetime.now()
    month_end_date = datetime.date(now.year, 1 if now.month==12 else now.month+1, 1) - datetime.timedelta(days=1)
    return month_end_date.strftime("%Y-%m-%d")

def get_last_month_start_date():
    now = datetime.datetime.now()
    month_start_date = datetime.date(now.year-1 if now.month==1 else now.year , 12 if now.month==1 else now.month-1, 1)
    return month_start_date.strftime("%Y-%m-%d")
