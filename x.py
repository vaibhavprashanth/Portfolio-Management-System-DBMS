import matplotlib.pyplot as plt
import pandas as pd

# Sample data (replace this with your actual data)
data = {
    'Date': ['2023-11-01', '2023-11-02', '2023-11-03'],
    'AAPL': [150, 153, 148],
    'TSLA': [900, 920, 890]
}
stock_close = pd.DataFrame(data)
stock_close['Date'] = pd.to_datetime(stock_close['Date'])
stock_close.set_index('Date', inplace=True)

# Plotting multiple columns without a for loop
plt.plot(stock_close.index, stock_close.drop(columns='Date'))
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend(stock_close.drop(columns='Date').columns)  # Use column names as legend labels
plt.show()
