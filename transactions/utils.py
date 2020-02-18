import requests
from requests import auth
from django import template
import requests, json, urllib
from users.models import Account 

register = template.Library()

def getRows(userID):
	me = auth.HTTPDigestAuth("admin", "admin")
	row = []
	transactionAttributes = ["BookingDateTime", "TransactionInformation", "Amount", "Currency"]
	id = str(userID)
	res = requests.get("http://51.11.48.127:8060/v1/documents?uri=/documents/"+id+".json", auth = me)
	if (res.status_code == 404):
		return False
	a = json.loads(res.text)
	for transaction in a['Transaction']:
		collecting = {
			'BookingDateTime': '',
			'TransactionInformation': '',
			'Amount': '',
			'Currency': ''	
		}
		for attribute in transactionAttributes:
			if ((attribute == "Amount") or (attribute == "Currency")) :
				collecting[attribute] = transaction['Amount'][str(attribute)]
			else:
				collecting[attribute] = transaction[str(attribute)]
		row.append(collecting)
	return row

def addToAccountList(request, addedAccount):
	if (addedAccount not in request.user.profile.getAccount()):
		Account.objects.create(accountid=  str(addedAccount), user = request.user)
	##accList = request.user.profile.getAccount()
	##request.user.profile.storeAccount(addedAccount)
	##request.user.profile.clearAccountList()
	print(request.user.profile.getAccount())
	print(request.user.profile.getAccount()[0])

def getDataForAccount(accountID):
    me = auth.HTTPDigestAuth("admin", "admin")
    print("Run")
    res = requests.get("http://51.11.48.127:8060/v1/documents?uri=/documents/data.json", auth = me)
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
    url = "http://51.11.48.127:8060/v1/documents?uri=/documents/"+accountID+".json"
    headers = {'Content-Type': 'application/json'}
    r = requests.put(url, data=json.dumps(result), headers=headers, auth = me)
    print(r.status_code)


def getAverageSpending(testDate, accountID):
    me = auth.HTTPDigestAuth("admin", "admin")
    res = requests.get("http://51.11.48.127:8060/v1/documents?uri=/documents/"+accountID+".json", auth = me)
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


class UserID():
	def __init__(self, userID):
		self.transactions = getRows(UserID)

	@register.filter
	def getTransactions(self):
		return self.transactions
