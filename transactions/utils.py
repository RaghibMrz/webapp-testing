import requests
from requests import auth
from django import template
import requests, json, urllib
from users.models import Account 
import datetime
from dateutil.relativedelta import relativedelta
import csv, os, sys

register = template.Library()

def getRows(accountID):
    #print("getRows")
    #print(type(accountID))
    me = auth.HTTPDigestAuth("admin", "admin")
    row = []
    transactionAttributes = ["BookingDateTime", "TransactionInformation", "Amount", "Currency", "MCC"]
  ####### code that works with vm
  # for i in range(len(accountID)):
  #   id = str(accountID[i])
  #   res = requests.get("http://51.104.239.212:8060/v1/documents?uri=/documents/"+id+".json", auth = me)
  #   if (res.status_code == 404):
  #     continue
    # a = json.loads(res.text)

####### code written by yuheng, works same way as online code with local files

    # for account in accountID:  #accountID is the queryset of all accountIDs under this user
    #     with open(os.path.join(sys.path[0], "aux_files/"+account+".json"), 'r') as data:
    #         jsondata = json.load(data)
    #         a = json.loads(jsondata)
    #     print(a)
    #     for transaction in a['Transaction']:
    #         collecting = {
    #             'BookingDateTime': '',
    #             'TransactionInformation': '',
    #             'Amount': '',
    #             'Currency': '',
    #             'MCC': ''
    #         }
    #         for attribute in transactionAttributes:
    #             if attribute == "MCC":
    #                 collecting[attribute] = transaction["MerchantDetails"]["MerchantCategoryCode"]
    #                 continue
    #             if ((attribute == "Amount") or (attribute == "Currency")):
    #                 collecting[attribute] = transaction['Amount'][str(attribute)]
    #                 if collecting['Amount'][0] == "+" or collecting['Amount'][0] == "-":
    #                     continue
    #                 if transaction["CreditDebitIndicator"] == "Debit":
    #                     collecting['Amount'] = "-" + collecting['Amount']
    #                 elif transaction["CreditDebitIndicator"] == "Credit":
    #                     collecting['Amount'] = "+" + collecting['Amount']
    #             else:
    #                 collecting[attribute] = transaction[str(attribute)]
    #             if (collecting not in row):
    #                 row.append(collecting)
    # print(row)
    # return row

    ##### Raghib code, easier debugging
    with open(os.path.join(sys.path[0], "aux_files/data.json"), 'r') as data:
        a = json.load(data)
    for transaction in a['Data']['Transaction']:
      collecting = {
        'BookingDateTime': '',
        'TransactionInformation': '',
        'Amount': '',
        'Currency': '',
        'MCC': ''
      }
      for attribute in transactionAttributes:
        if attribute == "MCC":
            collecting[attribute] = transaction["MerchantDetails"]["MerchantCategoryCode"]
            continue
        if ((attribute == "Amount") or (attribute == "Currency")):
            collecting[attribute] = transaction['Amount'][str(attribute)]
            if collecting['Amount'][0] == "+" or collecting['Amount'][0] == "-":
                continue
            if transaction["CreditDebitIndicator"] == "Debit":
                collecting['Amount'] = "-" + collecting['Amount']
            elif transaction["CreditDebitIndicator"] == "Credit":
                collecting['Amount'] = "+" + collecting['Amount']
        else:
          collecting[attribute] = transaction[str(attribute)]
        if (collecting not in row):
            row.append(collecting)
    return row

def addToAccountList(request, addedAccount):
	if (addedAccount not in request.user.profile.getAccount()):
		Account.objects.create(accountid=str(addedAccount), user = request.user)
	##request.user.profile.clearAccountList()
	##accList = request.user.profile.getAccount()
	##request.user.profile.storeAccount(addedAccount)
	print(request.user.profile.getAccount())
	print(request.user.profile.getAccount()[0])

# this funciton get the json containing all data and get all the related info about the current account id and upload it as a separate json file
def getDataForAccount(accountID):
    me = auth.HTTPDigestAuth("admin", "admin")
    print("Run")
    res = requests.get("http://51.104.239.212:8060/v1/documents?uri=/documents/data.json", auth = me)
    if (res.status_code == 404):
        return False
    a = json.loads(res.text)
    resultDic = {}
    for key in a['Data']:
        current= []
        for item in a['Data'][key]:
            if item["AccountId"] == accountID:
                if key == "Account":
                    month = item["OpeningDate"][3:5]
                    day = item["OpeningDate"][0:2]
                    resultDic["BillingDate"] = month+'-'+day
                current.append(item)
            resultDic[key] = current
    result = json.dumps(resultDic)
    print(type(result))
    url = "http://51.104.239.212:8060/v1/documents?uri=/documents/"+accountID+".json"
    headers = {'Content-Type': 'application/json'}
    r = requests.put(url, data=json.dumps(result), headers=headers, auth = me)
    print(r.status_code)

# this calculate the average spending of a account excluding all direct debit for the last month
# we then assume that the user will spend similar amount in the future one month
def getAverageSpending(testDate, accountID):
    me = auth.HTTPDigestAuth("admin", "admin")
    res = requests.get("http://51.104.239.212:8060/v1/documents?uri=/documents/"+accountID+".json", auth = me)
    if (res.status_code == 404):
        return False
    a = json.loads(res.text)
    billingdate = datetime.datetime(testDate.year, testDate.month, int(a['BillingDate'].split('-')[1]))
    print(billingdate)
    if billingdate<=testDate:
        startdate = billingdate- relativedelta(months=1)
        enddate = billingdate
    else:
        startdate = billingdate - relativedelta(months=2)
        enddate = billingdate - relativedelta(months=1)
    totalamount = 0 
    for transaction in a['Transaction']:
        bookingdate = datetime.datetime.strptime(transaction['BookingDateTime'], "%Y-%m-%dT%H:%M:%S+00:00")
        if bookingdate<enddate and bookingdate>startdate and transaction['ProprietaryBankTransactionCode']['Code']!="DirectDebit":
            totalamount+=float(transaction['Amount']['Amount'])
    print(startdate)
    print(enddate)
    print("{0:.2f}".format(totalamount/(enddate- startdate).days))

# this funciton returns a dictionary  that takes all dates from  the test date to the next biiling day and the values are the predicted remaining amount in the account 
def getPrediction(testDate, accountID):
    me = auth.HTTPDigestAuth("admin", "admin")
    res = requests.get("http://51.104.239.212:8060/v1/documents?uri=/documents/"+accountID+".json", auth = me)
    if (res.status_code == 404):
        return False
    a = json.loads(res.text)
    # billing day is the day that the bank charge for overdraft and pay interest
    # it is the same day of the month as the opening day of the account
    billingdate = datetime.datetime(testDate.year, testDate.month, int(a['BillingDate'].split('-')[1]))
    averagespending = getAverageSpending(testDate,accountID)
    #test if the billingday of this calender month has already passed, if yes, we will calculate the prediction from now to next month's billing day
    if testDate.day()>billingdate.day():
        targetdate = billingdate + relativedelta(months=1)
    else:
        targetdate = billingdate
    currentbalance = float(a['Balance']['Amount']['Amount'])
    prediction={}
    currentdate = testDate.date
    while currentdate<targetdate.date:
        currentdate +=relativedelta(days= 1)
        currentbalance-=averagespending
        prediction[currentdate] = currentbalance
    for directdebit in a['DirectDebit']:
        if directdebit['DirectDebitStatusCode'] == "Active":
            previouspayment = datetime.datetime.strptime(directdebit['PreviousPaymentDateTime'], "%Y-%m-%dT%H:%M:%S+00:00")
            nextpayment = previouspayment + relativedelta(months=1)
            if nextpayment.date in prediction:
                prediction[nextpayment.date] -=float(directdebit['PreviousPaymentAmount']['Amount'])
    print(prediction)
    return prediction

def getCategory(mcc):
    reader = csv.reader(open(os.path.join(sys.path[0], "aux_files/MCC_CatId.csv"), 'r'))
    getLetters = {
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
        "0": "zero"
    }
    d = {}
    count = 0
    for row in reader:
        if count == 0:
            count += 1
            continue
        key, value = row
        d[key] = value
    if mcc in d.keys():
        return getLetters[d[mcc]]
    else:
        return "zero"

class UserID():
	def __init__(self, userID):
		self.transactions = getRows(UserID)

	@register.filter
	def getTransactions(self):
		return self.transactions
