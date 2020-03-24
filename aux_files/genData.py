import json

def getDataForAccount(accountID):
    with open("finalData.json", 'r') as data:
        a = json.load(data)
    resultDic = {}
    for key in a['Data']:
        current = []
        for item in a['Data'][key]:
            if item["AccountId"] == accountID:
                if key == "Account":
                    month = item["OpeningDate"][3:5]
                    day = item["OpeningDate"][0:2]
                    resultDic["BillingDate"] = month + '-' + day
                current.append(item)
            resultDic[key] = current
    with open(accountID + "new.json", 'w') as outfile:
        json.dump(resultDic, outfile)

getDataForAccount("10567")
getDataForAccount("22289")
getDataForAccount("76523")
getDataForAccount("90613")
getDataForAccount("92548")