import csv
import datetime
import time
import os
import sys
from django.shortcuts import render
import json
import requests
from dateutil.relativedelta import relativedelta
from django import template
from requests import auth

from users.models import Account

register = template.Library()


# gets the correct account ID from the database through the correct post request
# default setting displays "All" account transactions aggregated into one,
# selecting an account from the drop down menu filters to just the selected account
def getAccount(request):
    if len(request.user.profile.getAccount()) > 0 and request.user.profile.getGotAccount() == "0":
        request.user.profile.setAccountID("All")
    if request.method == 'POST' and 'submit' in request.POST:
        if request.POST['submit'] in getAllAccounts(request.user.profile):
            request.user.profile.setAccountID(request.POST.get('submit'))
    return request.user.profile.getAccountID()


# checks if entered accountID produces a valid list of transactions, if not user is redirected with a page that displays
# a user friendly message telling them to check the ID they entered.
def validateID(request, accountID, page):
    if not getRows(accountID) and accountID != "All":
        context = {
            'rows': [{
                'TransactionInformation': 'Incorrect UserID linked',
                'Amount': 'Update accountID',
                'Currency': 'and try again',
                'BookingDateTime': 'No Data Found',
                'accountIDs': getStrAccountIDs(request.user.profile),
                'selectedAccount': accountID
            }]}
        return render(request, 'transactions/' + page + '.html', context)


# creates all the lists required to store categorical data, 10 lists for 10 categories
# a couple other lists for supplementary data such as sums, these are then files into
# the required context dictionary for later use
def makeContext(request, accountID):
    bpList, tpList, groceryList, fcList, financesList = [], [], [], [], []
    foodList, genList, entertainmentList, lsList, uncatList = [], [], [], [], []
    context = {
        'one': bpList, 'two': tpList, 'three': groceryList, 'four': fcList, 'five': financesList, 'six': foodList,
        'seven': genList, 'eight': entertainmentList, 'nine': lsList, 'zero': uncatList,
        'accountIDs': getStrAccountIDs(request.user.profile), 'selectedAccount': accountID
    }
    return context


# returns rows of userID selected, or aggregate rows if all selected
def getSelectedAccountRows(request, accountID):
    if accountID == "All":
        rows = getAllRows(getStrAccountIDs(request.user.profile))
    else:
        rows = getRows(accountID)
    return rows


# helper function to get data from database/local file into python dictionaries
def getData(accountID):
    # get from database
    # res = requests.get("http://51.104.239.212:8060/v1/documents?uri=/documents/" + accountID + ".json",
    #                    auth=auth.HTTPDigestAuth("admin", "admin"))
    # if res.status_code == 404:
    #     return False
    # return json.loads(res.text)

    # get locally
    try:
        with open(os.path.join(sys.path[0], "aux_files/" + accountID + ".json"), 'r') as data:
            jsonData = json.load(data)
        return jsonData
    except FileNotFoundError:
        return False


# function which takes a list of transaction, works out the total and if the sum is money spent or income.
def getTotal(transactionList):
    total = 0
    for transaction in transactionList:
        total += float(transaction['Amount'])
    if str(total)[0] == "-":
        spendIndicator = "Spent"
        total = total * -1.0
    else:
        spendIndicator = "Income"
    return round(float(total), 2), spendIndicator


# function sorts all rows (of transactions) from latest transaction to oldest
def sortedRows(rows):
    sortedRows = sorted(rows, key=lambda i: i['BookingDateTime'])
    sortedRows.reverse()
    return sortedRows


# handles POST request which gets correct data for pagination including actual data to display,
# the key and the setting for number of items per page
def getPaginationElements(request, transPerPage, page, rows, pageElem):
    if request.user.profile.getTransPerPage() != "AllTransactions":
        transPerPage = int(transPerPage)
        if pageElem == "<":
            pageElem = "Page " + str(int(page.split(" ")[1]) - 1)
        elif pageElem == ">":
            pageElem = "Page " + str(int(page.split(" ")[1]) + 1)
        if pageElem == "Page 1":
            elems = [pageElem, '>', "Page " + str(((len(rows)) // transPerPage) + 1)]
        elif pageElem == ("Page " + str(((len(rows)) // transPerPage) + 1)):
            elems = ['Page 1', '<', pageElem]
        else:
            elems = ['Page 1', '<', pageElem, '>', "Page " + str(((len(rows)) // 10) + 1)]
    else:
        elems = ['Page 1']
    return pageElem, elems


# close to identical context required in two methods, this function calculates and returns it
def getFinalContext(request, rows, transPerPageList, elems, dateIndicator, transPerPage, pageElem, predction):
    context = {'rows': getPaginatedRows(rows, transPerPage, pageElem), 'total': getTotal(rows)[0],
               'spendIndicator': getTotal(rows)[1],
               'dateIndicator': dateIndicator,
               'accountIDs': getStrAccountIDs(request.user.profile),
               'selectedAccount': request.user.profile.getAccountID(), 'elements': elems,
               'monthlyIncome': getIncome(rows), 'monthlySpend': getSpend(rows), 'leftOver': calcExcess(rows),
               'transPerPageList': transPerPageList, 'page': pageElem, 'prediction': prediction}

    return context


# takes user bank accountID and returns a list of transactions.
def getRows(accountID):
    row = []
    transactionAttributes = ["TransactionInformation", "Amount", "Currency", "BookingDateTime", "MCC"]
    a = getData(accountID)
    if not a:
        return False

    for transaction in a['Transaction']:
        collecting = {
            'TransactionInformation': '',
            'Amount': '',
            'Currency': '',
            'BookingDateTime': '',
            'MCC': ''
        }
        for attribute in transactionAttributes:
            # make function to convert date into more pleasant format
            if attribute == "BookingDateTime":
                collecting[attribute] = datetime.datetime.strptime(transaction[str(attribute)],
                                                                   "%Y-%m-%dT%H:%M:%S+00:00")
                continue
            if attribute == "MCC":
                collecting[attribute] = transaction["MerchantDetails"]["MerchantCategoryCode"]
                continue
            # appends "+/-" to indicate income/expenditure
            if (attribute == "Amount") or (attribute == "Currency"):
                collecting[attribute] = transaction['Amount'][str(attribute)]
                if collecting['Amount'][0] == "+" or collecting['Amount'][0] == "-":
                    continue
                if transaction["CreditDebitIndicator"] == "Debit":
                    collecting['Amount'] = "-" + collecting['Amount']
                elif transaction["CreditDebitIndicator"] == "Credit":
                    collecting['Amount'] = "+" + collecting['Amount']
            else:
                collecting[attribute] = transaction[str(attribute)]
            if collecting not in row:
                row.append(collecting)
    return sortedRows(row)


# combines list of transactions from all accounts into one, by unpacking each list of dictionaries into one
def getAllRows(IDs):
    row = getRows(IDs[0])
    for accountID in IDs:
        if accountID == IDs[0]:
            continue
        for collectingDict in getRows(accountID):
            row.append(collectingDict)
    return sortedRows(row)


# takes an element of a list, and makes it the first element
def makeFirstElement(element, elemList):
    if elemList[0] == element:
        return elemList
    else:
        elemList.remove(element)
        elemList.reverse()
        elemList.append(element)
        elemList.reverse()
        return elemList


# takes a list of transactions, the page number and the number of transactions to display
def getPaginatedRows(rows, transPerPage, page):
    if transPerPage == "AllTransactions":
        return rows
    transPerPage = int(transPerPage)
    p = int(page.split(" ")[1])
    start = transPerPage * (p - 1)
    end = (transPerPage * p) - 1
    if end > len(rows):
        end = len(rows)
    return rows[start:end]


# our accountID list is stored in the sqlite3 database as a "QuerySet", this function converts it to a string
def getStrAccountIDs(profile):
    accountList = []
    for accounts in profile.getAccount():
        accountList.append(str(accounts))
    return accountList


# our accountID list is stored in the sqlite3 database as a "QuerySet", this function converts it to a string
def getAllAccounts(profile):
    accountList = []
    for accounts in profile.getAccount():
        accountList.append(str(accounts))
    accountList.append("All")
    return accountList


def getDataForAccount(accountID):
    a = getData(accountID)
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
    with open(os.path.join(sys.path[0], "aux_files/" + accountID + "new.json"), 'w') as outfile:
        json.dump(resultDic, outfile)
    # result = json.dumps(resultDic)
    # print(type(result))
    # url = "http://51.104.239.212:8060/v1/documents?uri=/documents/" + accountID + ".json"
    # headers = {'Content-Type': 'application/json'}
    # r = requests.put(url, data=json.dumps(result), headers=headers, auth=auth.HTTPDigestAuth("admin", "admin"))
    # print(r.status_code)


# works out totals spend for each category
def getCategoricalTotal(context):
    spendIndicatorList, totalList = [], []
    for catList in context:
        if catList == "accountIDs":
            break
        total, spendIndicator = getTotal(context[catList])
        spendIndicatorList.append(spendIndicator)
        totalList.append(total)
        if len(context[catList]) < 1:
            context[catList].append({
                'TransactionInformation': 'None',
                'Amount': '-',
                'Currency': '-',
                'BookingDateTime': '-'
            })
    return totalList, spendIndicatorList, context


# gets number of transactions for visualisation
def getTransactionNum(context):
    numOfTransactions = []
    for catList in context:
        if catList != "accountIDs" and catList != "selectedAccount" and catList != "dateIndicator":
            if catList == "totals":
                break
            if context[catList][0]['TransactionInformation'] == "None" and len(context[catList]) == 1:
                numOfTransactions.append(0)
            else:
                numOfTransactions.append(len(context[catList]))
        else:
            continue

    return numOfTransactions


# this function returns all given rows of transactions between the two dates given
def getFilteredRows(rows, startDate, endDate):
    start = datetime.datetime.strptime(startDate, "%d/%m/%Y %H:%M ")
    end = datetime.datetime.strptime(endDate, " %d/%m/%Y %H:%M")
    filteredRows = []
    for row in rows:
        if row['BookingDateTime'] > end:
            continue
        if row['BookingDateTime'] < start:
            break
        filteredRows.append(row)
    return filteredRows


def getAverageSpending(testDate, accountID):
    a = getData(accountID)
    billingdate = datetime.datetime(testDate.year, testDate.month, int(a['BillingDate'].split('-')[1]))
    if billingdate <= testDate:
        startdate = billingdate - relativedelta(months=1)
        enddate = billingdate
    else:
        startdate = billingdate - relativedelta(months=2)
        enddate = billingdate - relativedelta(months=1)
    totalamount = 0
    for transaction in a['Transaction']:
        bookingdate = datetime.datetime.strptime(transaction['BookingDateTime'], "%Y-%m-%dT%H:%M:%S+00:00")
        if enddate > bookingdate > startdate and transaction['ProprietaryBankTransactionCode'][
            'Code'] != "DirectDebit" and transaction['CreditDebitIndicator'] == 'Debit':
            totalamount += float(transaction['Amount']['Amount'])
    return totalamount / (enddate - startdate).days


def getPredictionForCurrent(a, testDate, accountID):
    billingdate = datetime.datetime(testDate.year, testDate.month, int(a['BillingDate'].split('-')[1]))
    print(billingdate)
    averagespending = getAverageSpending(testDate, accountID)
    if testDate.day > billingdate.day:
        targetdate = billingdate + relativedelta(months=1)
    else:
        targetdate = billingdate
    currentbalance = float(a['Balance'][0]['Amount']['Amount'])
    prediction = {
        "date": [],
        "value": []
    }
    currentdate = testDate.date()
    timeInterval = targetdate - testDate
    directDebitToPay = {}
    for directdebit in a['DirectDebit']:
        if directdebit['DirectDebitStatusCode'] == "Active":
            previouspayment = datetime.datetime.strptime(directdebit['PreviousPaymentDateTime'],
                                                         "%Y-%m-%dT%H:%M:%S+00:00")
            nextpayment = previouspayment + relativedelta(months=1)
            print(nextpayment, targetdate, testDate)
            if nextpayment <= targetdate and nextpayment > testDate:
                if nextpayment.date() in directDebitToPay:
                    directDebitToPay[nextpayment.date()] += float(directdebit['PreviousPaymentAmount']['Amount'])
                else:
                    directDebitToPay[nextpayment.date()] = float(directdebit['PreviousPaymentAmount']['Amount'])
    print(directDebitToPay)
    print(timeInterval.days)
    daysPredicted = 0
    while daysPredicted < timeInterval.days:
        currentdate += relativedelta(days=1)
        currentbalance -= averagespending
        if currentdate in directDebitToPay:
            currentbalance-= directDebitToPay[currentdate]
        # prediction[time.mktime(currentdate.timetuple()) * 1000] = currentbalance
        prediction["date"].append(time.mktime(currentdate.timetuple()) * 1000)
        prediction["value"].append(currentbalance)
        daysPredicted +=1
    return prediction


def getPredictionForCreditCard(a, testDate, accountID):
    billingdate = datetime.datetime(testDate.year, testDate.month, int(a['BillingDate'].split('-')[1]))
    averagespending = getAverageSpending(testDate, accountID)
    interest = 0
    balance = 0  # float(a['Balance']['Amount']['Amount'])
    if testDate.day > billingdate.day:
        targetdate = billingdate + relativedelta(months=1)
    else:
        targetdate = billingdate

    # chargedDate is the date before which all the purchases will be charged the interest
    chargedDate = targetdate - relativedelta(
        days=int(a['Product'][0]['CCC']['CoreProduct']['MaxPurchaseInterestFreeLengthDays']))

    # check if the credit card is still in promotion
    for marketingState in a['Product'][0]['CCC']['CCCMarketingState']:
        if marketingState['Identification'] == "P1":
            startDate = datetime.datetime.strptime(a[Account][0]['OpeningDate'],
                                                   "%d-%m-%Y")
            if startDate + relativedelta(months=int(marketingState['StateTenureLength'])) > testDate:
                return ({"Interest": "Still in promotion, the interest is 0."})
        elif marketingState['Identification'] == "R1":
            minRepaymentRate = float(marketingState['Repayment']['MinBalanceRepaymentRate'])
            nonRepaymentCharge = float(
                marketingState['Repayment']['NonRepaymentFeeCharges'][0]['NonRepaymentFeeChargeDetail'][0]['FeeAmount'])
            for charge in marketingState['OtherFeesCharges']:
                if charge['FeeType'] == "Purchase":
                    purchaseRate = float(charge['FeeRate'])
    for transaction in a['Transaction']:
        if transaction['TransactionId'] == a['Balance']['LastPaidTransaction']:
            lastPaymentTime = datetime.datetime.strptime(transaction['ValueDateTime'],
                                                         "%Y-%m-%dT%H:%M:%S+00:00")
    for transaction in a['Transaction']:
        paymentTime = datetime.datetime.strptime(transaction['ValueDateTime'],
                                                 "%Y-%m-%dT%H:%M:%S+00:00")
        if paymentTime > lastPaymentTime:
            if paymentTime.date() < chargedDate:
                balance += float(transaction['Amount']['Amount'])
                interest += (chargedDate - paymentTime.date()).days * purchaseRate / 365
    return {"Interest": interest}


def prediction(testDate, accountID):
    a = getData(accountID)
    if a['Account'][0]['AccountSubType'] == 'CurrentAccount':
        prediction = getPredictionForCurrent(a, testDate, accountID)
    elif a['Account']['AccountSubType'] == 'CreditCard':
        prediction = getPredictionForCreditCard(a, testDate, accountID)
    return prediction


def getIncome(rows):
    if rows != False:
        monthDict = {}
        for row in rows:
            amount = float(row['Amount'])
            date = row['BookingDateTime']
            if str(date.month) not in monthDict:
                monthDict[str(date.month)] = 0
            if amount > 0:
                monthDict[str(date.month)] += amount
        # round(sum(monthDict.values()) / len(monthDict.values()), 2)
        if len(monthDict.values()) > 0:
            return min(monthDict.values())
        else:
            return 0


def getSpend(rows):
    monthDict = {}
    for row in rows:
        amount = float(row['Amount'])
        date = row['BookingDateTime']
        if str(date.month) not in monthDict:
            monthDict[str(date.month)] = 0
        if amount < 0:
            monthDict[str(date.month)] += amount
    if len(monthDict.values()) > 0:
        return -round(max(monthDict.values()), 2)
    else:
        return 0


def calcExcess(rows):
    leftOver = []
    left = getIncome(rows) - getSpend(rows)
    if left >= 0:
        leftOver.append("On track to save: ")
    else:
        left = -left
        leftOver.append("Spends predicted to exceed income by:")
    leftOver.append(round(left, 2))
    return leftOver


# check if post request has been sent to update a certain cap
def updateCaps(request):
    possibleCapSetOn = ["getValueCC", "getValueBP", "getValueTP", "getValueGC", "getValueFC", "getValueFSC",
                        "getValueFoodC", "getValueGC", "getValueEC", "getValueLSC", "getValueOC"]

    if request.method == "POST" and any(cap in request.POST for cap in possibleCapSetOn):
        chosenCapName = str(list(dict(request.POST).keys())[1])
        capValue = request.POST[chosenCapName]
        request.user.profile.setCap(chosenCapName, capValue)


# the context dictionary needs to be updated with all sorts of different information retrieved from different
# methods, this function collates those variables and adds them to the context.
def updateContext(context, rows, request, accountID):
    totalList, spendIndicatorList, context = getCategoricalTotal(context)
    context['count'] = getTransactionNum(context)
    context['totals'] = totalList
    context['spendIndicatorList'] = spendIndicatorList
    context['prediction'] = prediction(datetime.datetime(2020,2,10), accountID)
    if rows != False:
        context['monthlyIncome'] = getIncome(rows)
        context['monthlySpend'] = getSpend(rows)
        context['leftOver'] = calcExcess(rows)
    context['caps'] = getAllCaps(request)
    return context


# gets all the numerical values of the caps set on each category
def getAllCaps(request):
    possibleCapSetOn = ["getValueCC", "getValueBP", "getValueTP", "getValueGC", "getValueFC", "getValueFSC",
                        "getValueFoodC", "getValueGC", "getValueEC", "getValueLSC", "getValueOC"]
    capValues = []
    for caps in possibleCapSetOn:
        capValues.append((request.user.profile.getCap(caps)[0]))
    return capValues


# performs lookup from Merchant Category Code file- maps it to a defined category
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
        "10": "ten",
        "11": "eleven",
        "12": "twelve",
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
        
# class UserID():
#     def __init__(self, userID):
#         self.transactions = getRows(userID)
#
#     @register.filter
#     def getTransactions(self):
#         return self.transactions
