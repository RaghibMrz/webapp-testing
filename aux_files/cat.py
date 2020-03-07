import urllib.request
import requests
from requests import auth
import json

def getValues(r_list):
    valueList = []
    for i in range(0, len(r_list)):
        row = []
        row.append(str(i))
        row.append(r_list[i])
        row.append("")
        valueList.append(row)
    return valueList

def main():
    # refList = []
    # for row in getRows(10567):
    #     refList.append(row["TransactionInformation"])
    # values = getValues(refList)

    data =  { "Inputs": {
                "input1": {
                    "ColumnNames": ["ID", "Description", "Column 2"],
                    "Values": [ 
                                ["1", "Amazon shopping", ""],
                                ["2", "cash from John", ""],
                                ["3", "Mikel Coffee", ""],
                                ["4", "Pizza hut", ""],
                                ["5", "council rent", ""],
                                ["6", "paypal", ""]
                            ]
                },        
            },
            "GlobalParameters": {}
    }

    body = str.encode(json.dumps(data))
    url = 'https://ussouthcentral.services.azureml.net/workspaces/39de74e263724481af1ff429fb093ea4/services/818e86b59ad64ea79133a75f13071aa1/execute?api-version=2.0&details=true'
    api_key = 'K8FsrW164co+p2caaZGOQC/uWQt3oEtDlktGkIa4CMz1H/ZdiLVYlHss+EQsDDYJK4grVsSkB9p6u9iT4jvW7Q=='
    headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ api_key)}
    req = urllib.request.Request(url, body, headers) 

    print(getCategories(getCategoryIDs(req)))

def getCategoryIDs(req):
    try:
        response = urllib.request.urlopen(req)
        result = response.read()
        dictionary = json.loads(result.decode('utf-8'))
        lists = dictionary["Results"]["output1"]["value"]["Values"]
        categoryList = []
        for refList in lists:
            # scores = []
            # l_id = refList[0]
            # for i in range(1, 13):
            #     scores.append(refList[i])
            # print(l_id)
            # print(scores)

            if (refList[13] != None):
                categoryList.append(refList[13])
            else:
                categoryList.append(0)
        return categoryList

    except urllib.request.HTTPError as error:
        print("The request failed with status code: " + str(error.code))
        print(error.info())
        print(json.loads(error.read()))
        return -1

def getCategories(catIDs):
    catDict = {
        "1": "Bills & Payments",
        "2": "Transport",
        "3": "Groceries",
        "4": "Electronics",
        "5": "Fashion & Cosmetics",
        "6": "Finances",
        "7": "Food",
        "8": "Games & Sports",
        "9": "General",
        "10": "Charity",
        "11": "Entertainment",
        "12": "Leisure",
        "0": "Uncategorised"
    }
    categoryList = []
    for elem in catIDs:
        categoryList.append(catDict[str(elem)])
    return categoryList


# def getRows(userID):
#     me = auth.HTTPDigestAuth("admin", "admin")
#     row = []
#     transactionAttributes = ["BookingDateTime", "TransactionInformation", "Amount", "Currency"]
#     id = str(userID)
#     res = requests.get("http://51.11.48.127:8060/v1/documents?uri=/documents/"+id+".json", auth = me)
#     if (res.status_code == 404):
#         return False
#     a = json.loads(res.text)
#     for transaction in a['Data']['Transaction']:
#         collecting = {
#             'BookingDateTime': '',
#             'TransactionInformation': '',
#             'Amount': '',
#             'Currency': ''
#         }
#         for attribute in transactionAttributes:
#             if ((attribute == "Amount") or (attribute == "Currency")) :
#                 collecting[attribute] = transaction['Amount'][str(attribute)]
#             else:
#                 collecting[attribute] = transaction[str(attribute)]
#         row.append(collecting)
#     return row

main()