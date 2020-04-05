import json
import requests
from requests import auth

def getDataForAccount(accountID):
    with open("/Users/yhw/Desktop/CS/2ndYear/SystemEngineering/webapp-testing/aux_files/finalData.json", 'r') as data:
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
    result = json.dumps(resultDic)
    url = "http://51.104.239.212:8060/v1/documents?uri=/documents/" + accountID + ".json"
    headers = {'Content-Type': 'application/json'}
    r = requests.put(url, data=json.dumps(result), headers=headers, auth=auth.HTTPDigestAuth("admin", "admin"))
    return

# getDataForAccount("22289")
# getDataForAccount("76523")
# getDataForAccount("90613")
# getDataForAccount("92548")
getDataForAccount("97513")