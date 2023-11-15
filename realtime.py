import time
import datetime
import pandas as pd

ticker = 'GOOGL'
today = datetime.datetime(2023, 11, 12)

start_time = datetime.datetime(today.year, today.month, today.day, 0, 0)
end_time = datetime.datetime(today.year, today.month, today.day, 23, 59)

period1 = int(time.mktime(start_time.timetuple()))
period2 = int(time.mktime(end_time.timetuple()))
interval = '1d'  # 1d, 1m

query_string = f'https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1={period1}&period2={period2}&interval={interval}&events=history&includeAdjustedClose=true'

df = pd.read_csv(query_string)
print(type(df['Open'][0]))