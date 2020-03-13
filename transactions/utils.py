import csv
import datetime
import os
import sys

import json
import requests
from dateutil.relativedelta import relativedelta
from django import template
from requests import auth

from users.models import Account

register = template.Library()


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


def sortedRows(rows):
    sortedRows = sorted(rows, key=lambda i: i['BookingDateTime'])
    sortedRows.reverse()
    return sortedRows


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
                collecting[attribute] = datetime.datetime.strptime(transaction[str(attribute)], "%Y-%m-%dT%H:%M:%S+00:00")
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


def getStrAccountIDs(profile):
    accountList = []
    for accounts in profile.getAccount():
        accountList.append(str(accounts))
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
    result = json.dumps(resultDic)
    print(type(result))
    url = "http://51.104.239.212:8060/v1/documents?uri=/documents/" + accountID + ".json"
    headers = {'Content-Type': 'application/json'}
    r = requests.put(url, data=json.dumps(result), headers=headers, auth=auth.HTTPDigestAuth("admin", "admin"))
    print(r.status_code)


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
        if catList == "totals":
            break
        numOfTransactions.append(len(context[catList]))
    return numOfTransactions


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
    print(billingdate)
    if billingdate <= testDate:
        startdate = billingdate - relativedelta(months=1)
        enddate = billingdate
    else:
        startdate = billingdate - relativedelta(months=2)
        enddate = billingdate - relativedelta(months=1)
    totalamount = 0
    for transaction in a['Transaction']:
        bookingdate = datetime.datetime.strptime(transaction['BookingDateTime'], "%Y-%m-%dT%H:%M:%S+00:00")
        if enddate > bookingdate > startdate and transaction['ProprietaryBankTransactionCode']['Code'] != "DirectDebit":
            totalamount += float(transaction['Amount']['Amount'])
    print(startdate)
    print(enddate)
    print("{0:.2f}".format(totalamount / (enddate - startdate).days))
    return totalamount / (enddate - startdate).days


def prediction(testDate, accountID):
    a = getData(accountID)
    billingdate = datetime.datetime(testDate.year, testDate.month, int(a['BillingDate'].split('-')[1]))
    averagespending = getAverageSpending(testDate, accountID)
    if testDate.day() > billingdate.day():
        targetdate = billingdate + relativedelta(months=1)
    else:
        targetdate = billingdate
    currentbalance = float(a['Balance']['Amount']['Amount'])
    prediction = {}
    currentdate = testDate.date
    while currentdate < targetdate.date:
        currentdate += relativedelta(days=1)
        currentbalance -= averagespending
        prediction[currentdate] = currentbalance
    for directdebit in a['DirectDebit']:
        if directdebit['DirectDebitStatusCode'] == "Active":
            previouspayment = datetime.datetime.strptime(directdebit['PreviousPaymentDateTime'],
                                                         "%Y-%m-%dT%H:%M:%S+00:00")
            nextpayment = previouspayment + relativedelta(months=1)
            if nextpayment.date in prediction:
                prediction[nextpayment.date] -= float(directdebit['PreviousPaymentAmount']['Amount'])
    return prediction


def getIncome(rows):
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


def updateContext(context, rows):
    totalList, spendIndicatorList, context = getCategoricalTotal(context)
    context['count'] = getTransactionNum(context)
    context['totals'] = totalList
    context['spendIndicatorList'] = spendIndicatorList
    context['monthlyIncome'] = getIncome(rows)
    context['monthlySpend'] = getSpend(rows)
    context['leftOver'] = calcExcess(rows)
    return context


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
