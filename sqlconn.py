import mysql.connector
mycon=mysql.connector.connect(host='localhost',database='portfolio2',user='root',password='password123')
query='''select * from holdings_view where username="{}" and symbol="{}"'''.format('rewan','LEC')
cur = mycon.cursor()
cur.execute(query)
entered_quantity=cur.fetchall()
print(entered_quantity)
