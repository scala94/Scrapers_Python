import json

with open("HM\HM\eee.json", "r") as myfile:
    data = json.load(myfile)

cat = []
for i in data:
    cat.append(i)

print("first scraped category (", data[0]["category1"]," -- ", data[0]["category2"], " has ",len(data[0])," fields: ", a)
for i in range(len(data)):
        if len(data[i]) != len(data[0]):
            print("category number ", i, " (", data[i]["category1"], " -- ", data[i]["category2"], " ) has ", len(data[0]), "fields")
        print("all other  are the same as first")

print("""

-----------------------------
--- SEARCH for MATCHS -------
-----------------------------

""")

for i in range(len(data)):
    for ii in range(len(data)):
            if data[i][cat[0]] == data[ii][cat[0]]:
                print("no")

