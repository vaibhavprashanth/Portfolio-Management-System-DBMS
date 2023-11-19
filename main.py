from flask import Flask, render_template, request, session
from flask_mysqldb import MySQL
from datetime import timedelta
import hashlib
import yaml
from json import dumps
import time
import datetime
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
mysql = MySQL(app)
#db = yaml.load(open('db.yaml'))
app.secret_key = '123'
app.permanent_session_lifetime = timedelta(minutes=10) # Session lasts for 10 minutes

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password123'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_DB'] = 'portfolio3'
# Default is tuples
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.permanent = True
        user_details = request.form
        try:
            # If not logged in case
            username = user_details['username']
            password = user_details['password']

            # Password hashing to 224 characters
            password_hashed = hashlib.sha224(password.encode()).hexdigest()
        except:
            if request.form['logout'] == '':
                # If logged in case (for signout form return)
                session.pop('user')
            return render_template('/index.html', session=session)
        cur = mysql.connection.cursor()
        cur.execute('''select username, user_password from user_profile''')
        mysql.connection.commit()
        all_users = cur.fetchall()
        for user in all_users:
            # Check if the entered username and password is correct
            if user[0] == username and user[1] == password_hashed:
                session['user'] = username
                return portfolio()
        return render_template('alert2.html')
    else:
        return render_template('index.html', session=session)

@app.route('/signup.html',methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        phone = int(request.form.get('phone'))
        email = request.form.get('email')
        password_hashed = hashlib.sha224(password.encode()).hexdigest()
        #mycon=mysql.connector.connect(host='localhost',user='root',database='portfolio3',password='password123')
        cur = mysql.connection.cursor()
        query='''insert into user_profile values('{}','{}',{},'{}')'''.format(username,email,phone,password_hashed)
        cur.execute(query)
        mysql.connection.commit()
     

    return render_template('signup.html')
    
    #return 'hi'

@app.route('/portfolio.html')
def portfolio():

    # Check if we have logged in users
    if "user" not in session:
        return render_template('alert1.html')

    # Query for holdings
    x=['BIH','ELEX','HEX','HIH',    'KBL','LEC', 'LSL'  ,'NBL',  'NEPP',  'NIL']
    y=['AAPL','GOOGL','MSFT','AMZN','TSLA','META','ARM','NVDA','ORCL','JPM']
    cur = mysql.connection.cursor()
    for i in range(len(x)):
        today = datetime.datetime.now()
        start_time = datetime.datetime(today.year, today.month, today.day, 0, 0)
        end_time = datetime.datetime(today.year, today.month, today.day, 23, 59)
        period1 = int(time.mktime(start_time.timetuple()))
        period2 = int(time.mktime(end_time.timetuple()))
        interval = '1d'  # 1d, 1m
        query_string = f'https://query1.finance.yahoo.com/v7/finance/download/{y[i]}?period1={period1}&period2={period2}&interval={interval}&events=history&includeAdjustedClose=true'

        df = pd.read_csv(query_string)
        query_update='''update company_price set LTP="{}" where symbol="{}"'''.format(float(df['Open'][0]),y[i])
        cur.execute(query_update)
        mysql.connection.commit()
    user = [session['user']]
    print(user)
    cur.callproc('portfolio', user)
    holdings = cur.fetchall()

    # Query for watchlist
    query_watchlist = '''select symbol, LTP, PC, round((LTP-PC), 2) AS CH, round(((LTP-PC)/PC)*100, 2) AS CH_percent from watchlist
natural join company_price
where username = %s
order by (symbol)
'''
    cur.execute(query_watchlist, user)
    watchlist = cur.fetchall()


    # Query for stock suggestion
    query_suggestions = '''select symbol, EPS, ROE, book_value, rsi, adx, pe_ratio, macd from company_price
natural join fundamental_averaged
natural join technical_signals
natural join company_profile 
where 
EPS>25 and roe>13 and 
book_value > 100 and
rsi>50 and adx >23 and
pe_ratio < 35 and
macd = 'bull'
order by symbol;
'''
    cur.execute(query_suggestions)
    suggestions = cur.fetchall()

    # Query on EPS
    query_eps = '''select symbol, ltp, eps from fundamental_averaged
where eps > 30
order by eps;'''
    cur.execute(query_eps)
    eps = cur.fetchall()

    # Query on PE Ratio
    query_pe = '''select symbol, ltp, pe_ratio from fundamental_averaged
where pe_ratio <30;'''
    cur.execute(query_pe)
    pe = cur.fetchall()

    # Query on technical signals
    query_technical = '''select * from technical_signals
where ADX > 23 and rsi>50 and rsi<70 and MACD = 'bull';'''
    cur.execute(query_technical)
    technical = cur.fetchall()

    # Query for pie chart
    query_sectors = '''select C.sector, sum(A.quantity*B.LTP) as current_value 
from holdings_view A
inner join company_price B
on A.symbol = B.symbol
inner join company_profile C
on A.symbol = C.symbol
where username = %s
group by C.sector;
'''
    cur.execute(query_sectors, user)
    sectors_total = cur.fetchall()
    # Convert list to json type having percentage and label keys
    piechart_dict = toPercentage(sectors_total)
    piechart_dict[0]['type'] = 'pie'
    piechart_dict[0]['hole'] = 0.4
    ticker_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'ARM', 'NVDA', 'ORCL', 'JPM']

    # Download historical stock data for the given symbols
    stock_data = yf.download(ticker_symbols, start="2023-01-01", end="2023-12-31")

    # Extract the 'Close' prices for plotting
    stock_close = stock_data['Close']

    # Plotting the stock prices
    #plt.figure(figsize=(10, 6))
  
    #plt.plot(stock_close.index, stock_close['AAPL'], label='Apple (AAPL)', color='blue')
    # plt.plot(stock_close.index, stock_close['TSLA'], label='Tesla (TSLA)', color='orange')
    # plt.plot(stock_close.index, stock_close['GOOGL'], label='Google (GOOGL)', color='black')
    # plt.plot(stock_close.index, stock_close['MSFT'], label='Microsoft (MSFT)', color='orange')
    # plt.plot(stock_close.index, stock_close['AMZN'], label='Amazon (AMZN)', color='orange')
    # plt.plot(stock_close.index, stock_close['META'], label='META (META)', color='orange')
    # plt.plot(stock_close.index, stock_close['ORCL'], label='ORCL (Oracle)', color='orange')
    # plt.plot(stock_close.index, stock_close['NVDA'], label='NVDA (Nvidia)', color='orange')
    # plt.plot(stock_close.index, stock_close['JPM'], label='JPM (JP Morgan)', color='orange')
    # plt.plot(stock_close.index, stock_close['ARM'], label='ARM (ARM)', color='orange')
    # plt.title('Stock Price of Apple and Tesla in 2023')
    # plt.xlabel('Date')
    # plt.ylabel('Stock Price ($)')
    # plt.legend()
    # plt.grid(True)
    # plt.tight_layout()
    

    # Save the plot as a bytes object
    # buffer = BytesIO()
    # plt.savefig(buffer, format='png')
    # buffer.seek(0)
    # plt.close()

    # # Convert the plot to base64 encoding
    # plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render_template('portfolio.html', holdings=holdings, user=user[0], suggestions=suggestions, eps=eps, pe=pe, technical=technical, watchlist=watchlist, piechart=piechart_dict)


def toPercentage(sectors_total):
    json_format = {}
    total = 0

    for row in sectors_total:
        total += row[1]

    json_format['values'] = [round((row[1]/total)*100, 2)
                             for row in sectors_total]
    json_format['labels'] = [row[0] for row in sectors_total]
    return [json_format]
    
def list_to_json(listToConvert):
    json_format = {}
    temp_dict = {}
    val_per = []
    for value in listToConvert:
        temp_dict[value] = listToConvert.count(value)

    values = [val for val in temp_dict.values()]
    for i in range(len(values)):
        per = ((values[i]/sum(values))*100)
        val_per.append(round(per, 2))
    keys = [k for k in temp_dict.keys()]
    json_format['values'] = val_per
    json_format['labels'] = keys
    return [json_format]


@app.route('/add_transaction.html', methods=['GET', 'POST'])
def add_transaction():

    # Query for all companies (for drop down menu)
    cur = mysql.connection.cursor()
    query_companies = '''select symbol from company_profile'''
    cur.execute(query_companies)
    companies = cur.fetchall()

    if request.method == 'POST':
        transaction_details = request.form
        symbol = transaction_details['symbol']
        date = transaction_details['transaction_date']
        transaction_type = transaction_details['transaction_type']
        quantity = float(transaction_details['quantity'])
        cur = mysql.connection.cursor()
        print(transaction_details['rate'])
        #rate = float(transaction_details['rate'])
        if transaction_details['rate']=='':
            today = datetime.datetime.now()
            start_time = datetime.datetime(today.year, today.month, today.day, 0, 0)
            end_time = datetime.datetime(today.year, today.month, today.day, 23, 59)
            period1 = int(time.mktime(start_time.timetuple()))
            period2 = int(time.mktime(end_time.timetuple()))
            interval = '1d'  # 1d, 1m
            query_string = f'https://query1.finance.yahoo.com/v7/finance/download/{symbol}?period1={period1}&period2={period2}&interval={interval}&events=history&includeAdjustedClose=true'
            df = pd.read_csv(query_string)
            rate=float(df['Open'][0])
        else:
            rate = float(transaction_details['rate'])
        if transaction_type == 'Sell':
            quantity = -quantity
            query='''select quantity from holdings_view where username="{}" and symbol="{}"'''.format(session['user'],symbol)
            cur.execute(query)
            entered_quantity=cur.fetchone()
            print(entered_quantity,quantity)
            if not entered_quantity or int(entered_quantity[0])-abs(quantity)<0:
        
                return render_template('alert3.html')

        #cur = mysql.connection.cursor()
        query = '''insert into transaction_history(username, symbol, transaction_date, quantity, rate) values
(%s, %s, %s, %s, %s)'''
        values = [session['user'], symbol, date, quantity, rate]
        cur.execute(query, values)
        mysql.connection.commit()
    
    return render_template('add_transaction.html', companies=companies)


@app.route('/add_watchlist.html', methods=['GET', 'POST'])
def add_watchlist():

    # Query for companies (for drop down menu) excluding those which are already in watchlist
    cur = mysql.connection.cursor()
    query_companies = '''SELECT symbol from company_profile
where symbol not in
(select symbol from watchlist
where username = %s);
'''
    user = [session['user']]
    cur.execute(query_companies, user)
    companies = cur.fetchall()

    if request.method == 'POST':
        watchlist_details = request.form
        symbol = watchlist_details['symbol']
        cur = mysql.connection.cursor()
        query = '''insert into watchlist(username, symbol) values
(%s, %s)'''
        values = [session['user'], symbol]
        cur.execute(query, values)
        mysql.connection.commit()

    return render_template('add_watchlist.html', companies=companies)

@app.route('/stockprice.html')
def current_price(company='all'):
    cur = mysql.connection.cursor()
    if company == 'all':
        query = '''SELECT symbol, LTP, PC, round((LTP-PC), 2) as CH, round(((LTP-PC)/PC)*100, 2) AS CH_percent FROM company_price
order by symbol;
'''
        cur.execute(query)
    else:
        company = [company]
        query = '''SELECT symbol, LTP, PC, round((LTP-PC), 2) as CH, round(((LTP-PC)/PC)*100, 2) AS CH_percent FROM company_price
        where symbol = %s;
'''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('stockprice.html', values=rv)


@app.route('/fundamental.html', methods=['GET'])
def fundamental_report(company='all'):
    cur = mysql.connection.cursor()
    if company == 'all':
        query = '''select * from  fundamental_averaged;'''
        cur.execute(query)
    else:
        company = [company]
        query = '''select F.symbol, report_as_of, LTP, eps, roe, book_value, round(LTP/eps, 2) as pe_ratio
from fundamental_report F
inner join company_price C
on F.symbol = C.symbol
where F.symbol = %s'''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('fundamental.html', values=rv)


@app.route('/technical.html')
def technical_analysis(company='all'):
    cur = mysql.connection.cursor()
    if company == 'all':
        query = '''select A.symbol, sector, LTP, volume, RSI, ADX, MACD from technical_signals A 
left join company_profile B
on A.symbol = B.symbol
order by (A.symbol)'''
        cur.execute(query)
    else:
        company = [company]
        query = '''SELECT * FROM technical_signals where company = %s'''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('technical.html', values=rv)


@app.route('/companyprofile.html')
def company_profile(company='all'):
    cur = mysql.connection.cursor()
    if company == 'all':
        query = '''select * from company_profile
order by(symbol);
'''
        cur.execute(query)
    else:
        company = [company]
        query = '''select * from company_profile where company = %s'''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('companyprofile.html', values=rv)


@app.route('/dividend.html')
def dividend_history(company='all'):
    cur = mysql.connection.cursor()
    if company == 'all':
        query = '''select * from dividend_history
order by(symbol);
'''
        cur.execute(query)
    else:
        company = [company]
        query = '''select * from dividend_history where company = %s'''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('dividend.html', values=rv)


@app.route('/watchlist.html')
def watchlist():
    if 'user' not in session:
        return render_template('alert1.html')
    cur = mysql.connection.cursor()
    query_watchlist = '''select symbol, LTP, PC, round((LTP-PC), 2) AS CH, round(((LTP-PC)/PC)*100, 2) AS CH_percent from watchlist
natural join company_price
where username = %s
order by (symbol);
'''
    cur.execute(query_watchlist, [session['user']])
    watchlist = cur.fetchall()

    return render_template('watchlist.html', user=session['user'], watchlist=watchlist)


@app.route('/holdings.html')
def holdings():
    if "user" not in session:
        return render_template('alert1.html')
    cur = mysql.connection.cursor()
    query_holdings = '''select A.symbol, A.quantity, B.LTP, round(A.quantity*B.LTP, 2) as current_value from holdings_view A
inner join company_price B
on A.symbol = B.symbol
where username = %s
'''
    cur.execute(query_holdings, [session['user']])
    holdings = cur.fetchall()

    return render_template('holdings.html', user=session['user'], holdings=holdings)

@app.route('/news.html')
def news(company='all'):
    cur = mysql.connection.cursor()
    if company == 'all':
        query = '''select date_of_news, title, related_company, C.sector, group_concat(sources) as sources 
from news N
inner join company_profile C
on N.related_company = C.symbol
group by(title);
'''
        cur.execute(query)
    else:
        company = [company]
        query = '''select date_of_news, title, related_company, related_sector, sources from news where related_company = %s'''
        cur.execute(query, company)
    rv = cur.fetchall()
    return render_template('news.html', values=rv)


if __name__ == '__main__':
    app.run(debug=True)
