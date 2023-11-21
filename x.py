import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

# Sample data (replace this with your actual data)
stock_data = yf.download(['AAPL','GOOGL'], start="2023-11-19", end="2023-11-19")
data = {
    'Date': ['2023-11-01', '2023-11-02', '2023-11-03'],
    'AAPL': [150, 153, 148],
    'TSLA': [900, 920, 890],
    'GOOGL': [2700, 2650, 2680]  # Adding another column for demonstration
}
stock_data=pd.DataFrame(stock_data['Close'])
print(stock_data.head)


# # Plotting multiple columns without using a for loop
stock_data.plot(figsize=(8, 6))  # Plotting all columns against the index
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend(title='Stocks')  # Adding a legend with column names as labels
plt.show()
