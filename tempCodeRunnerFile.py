stock_close.plot(figsize=(8, 6))  # Plotting all columns against the index
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend(title='Stocks')  # Adding a legend with column names as labels
plt.show()