import requests
from requests import auth
from django import template
import requests, json, urllib

register = template.Library()

def getRows(userID):
	me = auth.HTTPDigestAuth("admin", "admin")
	row = []
	transactionAttributes = ["BookingDateTime", "TransactionInformation", "Amount", "Currency"]
	id = str(userID)
	res = requests.get("http://51.132.8.252:8060/v1/documents?uri=/documents/"+id+".json", auth = me)
	if (res.status_code == 404):
		return False
	a = json.loads(res.text)
	for transaction in a['Data']['Transaction']:
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
	##if (addedAccount not in request.user.profile.getAccount):
	Account.objects.create(accountid=  str(addedAccount), user = request.user)
	##accList = request.user.profile.getAccount()
	##request.user.profile.storeAccount(addedAccount)
	##request.user.profile.clearAccountList()
	print(request.user.profile.getAccount)

def getDataForAccount(accountID):
	

class UserID():
	def __init__(self, userID):
		self.transactions = getRows(UserID)

	@register.filter
	def getTransactions(self):
		return self.transactions
