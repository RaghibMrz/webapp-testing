from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from users.forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm
import requests
from requests import auth
from django.contrib import messages
from django.core.mail import send_mail
from .forms import ContactForm
#auxilliary file I made to hold some of the logic
from .utils import *

@login_required
def home(request):
    request.session.set_expiry(600)
    accountid = request.user.profile.getAccount()
    #print("home")
    #print(accountid)
    #print(type(accountid))
    if getRows(accountid) == False:
        # context = {
        #     'rows': [{
        #     'BookingDateTime': 'No Data Found',
        #     'TransactionInformation': 'Incorrect UserID linked',
        #     'Amount': 'Update accountID',
        #     'Currency': 'and try again',
        # }]}
        return render(request, 'transactions/home.html')
    bpList, tpList, groceryList, fcList, financesList = [], [], [], [], []
    foodList, genList, entertainmentList, lsList, uncatList = [], [], [], [], []
    totalList = []
    spendIndicator = []
    numOfTransactions = []
    context = {
        "one": bpList,
        "two": tpList,
        "three": groceryList,
        "four": fcList,
        "five": financesList,
        "six": foodList,
        "seven": genList,
        "eight": entertainmentList,
        "nine": lsList,
        "zero": uncatList,
        "totals": totalList,
        "count": numOfTransactions,
        "spendIndicator": spendIndicator
    }

    #get data from database, store into "context" dictionary
    for transaction in getRows(accountid):
    	context[getCategory(transaction['MCC'])].append(transaction)

    #gets number of transactions for treemap
    for catList in context:
    	if (catList == "totals"):
    		break
    	numOfTransactions.append(len(context[catList]))

    #works out totals spend for each category
    for catList in context:
    	if catList == "totals":
    		break
    	total = 0
    	for transaction in context[catList]:
    		total += float(transaction['Amount'])

    	if (str(total)[0] == "-"):
    		spendIndicator.append("Spent")
    		total = total*-1.0
    	else:
    		spendIndicator.append("Income")
    	totalList.append(round(float(total),2))
    return render(request, 'transactions/home.html', context)

@login_required
def profile(request):
	request.session.set_expiry(600)
	if request.method == 'POST':
		uForm = UserUpdateForm(request.POST, request.FILES, instance=request.user)
		pForm = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
		if uForm.is_valid() and pForm.is_valid():
			newAccountID = pForm.cleaned_data.get('accountID')
			addToAccountList(request, newAccountID)
			getDataForAccount(newAccountID)
			# accList = request.user.profile.getAccount()
			# request.user.profile.storeAccount(pForm.cleaned_data.get('accountID'))
			# request.user.profile.clearAccountList()
			# print(request.user.profile.accountIDList)
			uForm.save()
			pForm.save()
			messages.success(request, f'Account successfully updated')
			return redirect('profile')
	#return statement in line above is to prevent user from falling to line below
	#phenomenon called 'get-redirect pattern'- when u reload browser afrer submitting data
	#post request will be duplicated.
	else:
		uForm = UserUpdateForm(instance=request.user)
		pForm = ProfileUpdateForm(instance=request.user.profile)
	context = {
		'uForm': uForm,
		'pForm': pForm,
	}
	return render(request, 'transactions/profile.html', context)

@login_required
def transactions(request):
	request.session.set_expiry(600)
	#print("Transactions")
	#print(request.user.profile.getAccount())
	if (getRows(request.user.profile.getAccount()) == False):
		context = {
			'rows': [{
			'BookingDateTime': 'No Data Found',
			'TransactionInformation': 'Incorrect UserID linked',
			'Amount': 'Update accountID and try again'
			}]
		}
		return render(request, 'transactions/transactions.html', context)
	context = {
		'rows': getRows(request.user.profile.getAccount())
	}
	return render(request, 'transactions/transactions.html', context)

@login_required
def report(request):
	request.session.set_expiry(600)
	return render(request, 'transactions/report.html')

@login_required
def help(request):
	request.session.set_expiry(600)
	if request.method == "POST":
		form = ContactForm(request.POST)
		if form.is_valid:
			form.save()
			messages.success(request, f'Message sent!')
			send_mail(form.cleaned_data.get('subject'), form.cleaned_data.get('message')+"\n\n Reply to: "+form.cleaned_data.get('email'), 'pwresetst45@gmail.com', ['pwresetst45@gmail.com'])
			return redirect('home')
	else:
		form = ContactForm()
	context = {
		'form' : form
	}
	return render(request, 'transactions/help.html', context)
