import json
 
f = open('data2.json')
 
# returns JSON object as 
# a dictionary
data = json.load(f)
for i in data:
    x=data['password']
print(x)
