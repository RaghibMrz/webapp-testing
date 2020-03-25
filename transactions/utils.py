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

# from users.models import Account

register = template.Library()


# gets the correct account ID from the database through the correct post request
# default setting displays "All" account transactions aggregated into one,
# selecting an account from the drop down menu filters to just the selected account
def getAccount(request):
    if len(request.user.profile.getAccountIDList()) > 0 and request.user.profile.getGotAccount() == "0":
        accountList = getAccountIDsFromModel(request.user.profile)
        if len(accountList) > 0:
            request.user.profile.setAccountID(accountList[0])
        else:
            request.user.profile.setAccountID("None")
    if request.method == 'POST' and 'submit' in request.POST:
        if request.POST['submit'] in getAccountsForDropDown(request.user.profile):
            request.user.profile.setAccountID(request.POST.get('submit'))
    return request.user.profile.getAccountID()


# checks if entered accountID produces a valid list of transactions, if not user is redirected with a page that displays
# a user friendly message telling them to check the ID they entered.
def validateID(request, accountID):
    if not getRows(request, accountID):
        context = {
            'accountID': accountID,
            'noRows': True,
            'accountIDs': getAccountIDsFromModel(request.user.profile)
        }
        return request, 'transactions/home.html', context
    return True


# returns rows of userID selected, or aggregate rows if all selected
def getRows(request, accountID):
    if accountID == "All":
        return False
        # rows = getAllRows(getAccountIDsFromModel(request.user.profile))
    elif accountID == "AllCurr":
        return getAllRowsCurr(getAccountIDsFromModel(request.user.profile))
    elif accountID == "AllCC":
        return getAllRowsCC(getAccountIDsFromModel(request.user.profile))
    return getSingleAccountRows(accountID)


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

#function that returns all necessary info on summary page
def getSummaryContext(request):
    accountIDs = getAccountIDsFromModel(request.user.profile)
    accountData = []
    totalCurrentBalance = 0
    totalCreditBalance = 0
    totalBills = 0
    for accountID in accountIDs:
        data = getData(accountID)
        newEntry = {}
        newEntry['accountID'] = accountID
        newEntry['isCreditAccount'] = isCreditAccount(accountID)
        predict = prediction( datetime.datetime(2020, 2, 10), accountID)
        newEntry['nextBillingDay'] = predict['nextBillingDay'].date()
        if newEntry['isCreditAccount']:
            newEntry['balance'] = predict['balance']
            totalCreditBalance+= predict['balance']
            newEntry['minimumPayment'] = predict['minRepaymentAmount']
            newEntry['balanceWtihInterest'] = predict['BalanceWithInterest']
        else:
            newEntry['balance'] = float(data['Balance'][0]['Amount']['Amount'])
            totalCurrentBalance += float(data['Balance'][0]['Amount']['Amount'])
            directDebit = getDirectDebit(data, datetime.datetime(2020, 2, 10), accountID)
            sumofDD = 0
            for value in directDebit.values():
                sumofDD +=value
            newEntry['directDebit'] = sumofDD
            totalBills+=sumofDD
        accountData.append(newEntry)
    context = {
        'accountIDs' : accountIDs,
        'accountData' : accountData,
        'totalCurrentBalance' : totalCurrentBalance,
        'totalCreditBalance' : totalCreditBalance,
        'totalBills' : totalBills,
        'remainingAmount' : totalCurrentBalance - totalCreditBalance - totalBills
    }
    return context


# Takes an account id, returns the balance on it, if "All accounts are selected, then it shows all
def getCurrAccountBalance(request, accountID):
    if accountID == "All":
        return False
    elif accountID == "AllCurr":
        total = 0
        for account in getAccountIDsFromModel(request.user.profile):
            if not isCreditAccount(account):
                total += float(getData(account)['Balance'][0]['Amount']['Amount'])
        return total
    elif accountID == "AllCC":
        total = 0
        for account in getAccountIDsFromModel(request.user.profile):
            if isCreditAccount(account):
                total += float(getData(account)['Balance'][0]['Amount']['Amount'])
        return total
    return float(getData(accountID)['Balance'][0]['Amount']['Amount'])



# creates all the lists required to store categorical data, 10 lists for 10 categories
# a couple other lists for supplementary data such as sums, these are then filed into
# the required context dictionary for later use
def makeCatContext(request, accountID):
    bpList, tpList, groceryList, fcList, financesList = [], [], [], [], []
    foodList, genList, entertainmentList, lsList, uncatList = [], [], [], [], []
    context = {
        'one': bpList, 'two': tpList, 'three': groceryList, 'four': fcList, 'five': financesList, 'six': foodList,
        'seven': genList, 'eight': entertainmentList, 'nine': lsList, 'zero': uncatList,
        'accountIDs': getAccountIDsFromModel(request.user.profile), 'selectedAccount': accountID
    }
    return context


# creates all the lists required to store aggregate data,
# a couple other lists for supplementary data such as sums, these are then filed into
# the required context dictionary for later use
def makeAggContext(request, accountID):
    context = {
        'accountIDs': getAccountIDsFromModel(request.user.profile), 'selectedAccount': accountID
    }
    return context


# Takes an accountID, returns true if it is associated to a credit card, false for current account
def isCreditAccount(accountID):
    return getData(accountID)['Account'][0]['AccountSubType'] == 'CreditCard'


def getAccountType(accountID):
    if accountID == "All":
        return "MyAcccounts"
    elif accountID == "AllCurr":
        return "Current Account"
    elif accountID == "AllCC":
        return "Credit-Card"

    if "All" not in accountID:
        if isCreditAccount(accountID):
            return "Credit-Card"
        else:
            return "Current Account"


# gets minimum payment for a credit account, returns false if current account
def getMinPayment(profile, accountID):
    if accountID == "AllCC":
        totalMp = 0.0
        for account in getAccountIDsFromModel(profile):
            if isCreditAccount(account):
                minimumRepaymentRate = float(
                    getData(account)['Product'][0]['CCC'][0]['CCCMarketingState'][1]['Repayment'][
                        'MinBalanceRepaymentRate'])
                mp = float(getData(account)['Balance'][0]['Amount']['Amount']) * minimumRepaymentRate / 100.0
                totalMp += mp
        return totalMp

    if isCreditAccount(accountID):
        minimumRepaymentRate = float(
            getData(accountID)['Product'][0]['CCC'][0]['CCCMarketingState'][1]['Repayment']['MinBalanceRepaymentRate'])
        mp = float(getData(accountID)['Balance'][0]['Amount']['Amount']) * minimumRepaymentRate / 100.0
        return mp
    return False


# the context dictionary needs to be updated with all sorts of different information retrieved from different
# methods, this function collates those variables and adds them to the context.
def updateContext(context, rows, request, accountID, home):
    if home:
        totalList, spendIndicatorList, context = getCategoricalTotal(context)
        context['count'] = getTransactionNum(context)
        context['totals'] = totalList
        context['caps'] = getAllCaps(request)
        context['spendIndicatorList'] = spendIndicatorList
    else:
        context['setCap'] = getAllCaps(request)[0]
        context['total'] = getTotal(rows)[0]
        context['spendIndicator'] = getTotal(rows)[1]
    context['balance'] = getCurrAccountBalance(request, accountID)
    context['accountType'] = getAccountType(accountID)

    if getAccountType(accountID) == "Credit-Card":
        context['minPayment'] = getMinPayment(request.user.profile, accountID)
        # context['prediction'] = prediction(datetime.datetime(2020, 2, 10), accountID)

    if getAccountType(accountID) == "Current Account":
        # whatever u need for current accounts only
        context['dd'] = getMonthlyDirectDebit(request, accountID)
        # context['prediction'] = prediction(datetime.datetime(2020, 2, 10), accountID)
    if rows != False:
        context['monthlyIncome'] = getMinIncome(rows)
        context['monthlySpend'] = getSpend(rows)
        context['leftOver'] = calcExcess(rows)

        #for lib kai, 4 lines below:
        context['averageSpend'] = getAverageMonthlySpend(rows)
        context['averageIncome'] = getAverageMonthlyIncome(rows)
        context['monthlySpendVIncome'] = getSpendVIncome(rows)
    context['prediction'] = buildPredictionDict(request)

    return context


# creates dictionary of monthly spend against monthly income
def getSpendVIncome(rows):
    monthDict = getMonthlySpendDict(rows, "spend")
    months = []
    spend = []
    income = []
    for key in sorted(monthDict, reverse=True):
        months.append(key)
        spend.append(monthDict[key])
    monthDict = getMonthlySpendDict(rows, "income")
    for key in sorted(monthDict, reverse=True):
        income.append(monthDict[key])
    months = getCleanMonths(months)
    return {'months': months, 'spend': spend, 'income': income}


# takes list of months, returns in neater format
def getCleanMonths(months):
    newList = []
    for month in months:
        date = datetime.datetime.strptime(str(month), "%m-%Y")
        date = (time.mktime(date.timetuple()) * 1000)
        newList.append(date)
    return newList


# builds a dictionary with predicted spend values for all accounts associated with user
def buildPredictionDict(request):
    current = []
    credit = []
    for account in getAccountIDsFromModel(request.user.profile):
        newDict = {}
        if isCreditAccount(account):
            credit.append(prediction(datetime.datetime(2020, 2, 10), account))
        else:
            newDict[str(account)] = {
                "dates": prediction(datetime.datetime(2020, 2, 10), account).get('date'),
                "values": prediction(datetime.datetime(2020, 2, 10), account).get('value')
            }
            current.append(newDict)

    pred = {
        'current': current,
        'credit': credit
    }
    return pred


# takes user bank accountID and returns a list of transactions.
def getSingleAccountRows(accountID):
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
# def getAllRows(IDs):
#     row = getSingleAccountRows(IDs[0])
#     for accountID in IDs:
#         if accountID == IDs[0]:
#             continue
#         for collectingDict in getSingleAccountRows(accountID):
#             row.append(collectingDict)
#     return sortedRows(row)


# combines list of transactions from all current accounts into one, by unpacking each list of dictionaries into one
def getAllRowsCurr(accountIDs):
    firstID = 0
    for accountID in accountIDs:
        if not isCreditAccount(accountID):
            firstID = accountID
            row = getSingleAccountRows(accountID)
            break

    if firstID == 0:
        return

    for accountID in accountIDs:
        if accountID == firstID:
            continue
        if not isCreditAccount(accountID):
            for collectingDict in getSingleAccountRows(accountID):
                row.append(collectingDict)
    return sortedRows(row)


# combines list of transactions from all credit accounts into one, by unpacking each list of dictionaries into one
def getAllRowsCC(accountIDs):
    firstID = 0
    for accountID in accountIDs:
        if isCreditAccount(accountID):
            firstID = accountID
            row = getSingleAccountRows(accountID)
            break

    if firstID == 0:
        return False

    for accountID in accountIDs:
        if accountID == firstID:
            continue
        if isCreditAccount(accountID):
            for collectingDict in getSingleAccountRows(accountID):
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


# our accountID list is stored in the sqlite3 database as a "QuerySet", this function converts it to a string
def getAccountIDsFromModel(profile):
    accountList = []
    for accounts in profile.getAccountIDList():
        accountList.append(str(accounts))
    return accountList


# our accountID list is stored in the sqlite3 database as a "QuerySet", this function converts it to a string
def getAccountsForDropDown(profile):
    accountList = []
    for accounts in profile.getAccountIDList():
        accountList.append(str(accounts))
    # accountList.append("All")
    accountList.append("AllCurr")
    accountList.append("AllCC")
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
    startdate = testDate - relativedelta(months=1)
    enddate = testDate
    totalamount = 0
    for transaction in a['Transaction']:
        bookingdate = datetime.datetime.strptime(transaction['BookingDateTime'], "%Y-%m-%dT%H:%M:%S+00:00")
        if enddate > bookingdate > startdate and transaction['ProprietaryBankTransactionCode'][
            'Code'] != "DirectDebit" and transaction['CreditDebitIndicator'] == 'Debit':
            totalamount += float(transaction['Amount']['Amount'])
    return totalamount / (enddate - startdate).days


# Works out the data of an account's salary, and returns a dictionary with the date and amount
def getSalaryData(rows):
    monthDict = {}
    fullDateDict = {}
    if rows != False:
        for row in rows:
            if float(row['Amount']) <= 0.0:
                continue
            date = row['BookingDateTime']
            amount = float(row['Amount'])
            if str(date.month) + str(date.year) not in monthDict:
                monthDict[str(date.month) + str(date.year)] = amount
                fullDateDict[str(date)] = amount
            elif amount > monthDict[str(date.month) + str(date.year)]:
                monthDict[str(date.month) + str(date.year)] = amount
                fullDateDict[str(date)] = amount

    salList = list(monthDict.values())
    modalValue = max(set(salList), key=salList.count)
    newDict = {}
    for item in fullDateDict:
        if fullDateDict[item] == modalValue:
            newDict[item] = modalValue

    salaryDates = list(newDict.keys())
    totalOfDays = 0
    for date in salaryDates:
        totalOfDays += int(datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").day)

    averageDay = totalOfDays // len(salaryDates)
    return [modalValue, averageDay]


def getMonthlyDirectDebit(request, accountID):
    if accountID == "AllCurr":
        total = 0
        for account in getAccountIDsFromModel(request.user.profile):
            if not isCreditAccount(account):
                data = getData(account)
                totalDirectDebit = 0
                for directdebit in data['DirectDebit']:
                    if directdebit['DirectDebitStatusCode'] == "Active":
                        totalDirectDebit += float(directdebit['PreviousPaymentAmount']['Amount'])
                total += totalDirectDebit
        return total

    data = getData(accountID)
    totalDirectDebit = 0.0
    for directdebit in data['DirectDebit']:
        if directdebit['DirectDebitStatusCode'] == "Active":
            totalDirectDebit += float(directdebit['PreviousPaymentAmount']['Amount'])
    return totalDirectDebit


# it takes the dataset a, the testdate and the account to return all the direct debits u need to pay from the
# testdate to the next billing day
def getDirectDebit(a, testDate, accountID):
    billingdate = datetime.datetime(testDate.year, testDate.month, int(a['BillingDate'].split('-')[1]))
    if testDate.day > billingdate.day:
        targetdate = billingdate + relativedelta(months=1)
    else:
        targetdate = billingdate
    directDebitToPay = {}
    for directdebit in a['DirectDebit']:
        if directdebit['DirectDebitStatusCode'] == "Active":
            previouspayment = datetime.datetime.strptime(directdebit['PreviousPaymentDateTime'],
                                                         "%Y-%m-%dT%H:%M:%S+00:00")
            nextpayment = previouspayment + relativedelta(months=1)
            # print(nextpayment, targetdate, testDate)
            if nextpayment <= targetdate and nextpayment > testDate:
                if nextpayment.date() in directDebitToPay:
                    directDebitToPay[nextpayment.date()] += float(directdebit['PreviousPaymentAmount']['Amount'])
                else:
                    directDebitToPay[nextpayment.date()] = float(directdebit['PreviousPaymentAmount']['Amount'])
    return directDebitToPay


# prediction for current account returns a dictionary with dates being the keys and predicted remaining balance on this account as the values
def getPredictionForCurrent(a, testDate, accountID):
    salaryData = getSalaryData(getSingleAccountRows(accountID))
    # print(salaryData)
    billingdate = datetime.datetime(testDate.year, testDate.month, int(a['BillingDate'].split('-')[1]))
    salaryDay = datetime.datetime(testDate.year, testDate.month, salaryData[1])
    # print(billingdate)
    averagespending = getAverageSpending(testDate, accountID)
    if testDate.day > billingdate.day:
        targetdate = billingdate + relativedelta(months=1)
    else:
        targetdate = billingdate
    salary = {}
    if salaryDay > testDate and salaryDay < targetdate:
        salary[salaryDay.date()] = salaryData[0]
    else:
        salaryDay = salaryDay + relativedelta(months=1)
        if salaryDay > testDate and salaryDay < targetdate:
            salary[salaryDay.date()] = salaryData[0]
    # print(salary)
    currentbalance = float(a['Balance'][0]['Amount']['Amount'])
    prediction = {
        "date": [],
        "value": [],
        "nextBillingDay" : targetdate
    }
    currentdate = testDate.date()
    timeInterval = targetdate - testDate
    directDebitToPay = getDirectDebit(a, testDate, accountID)
    # print(directDebitToPay)
    # print(timeInterval.days)
    daysPredicted = 0
    while daysPredicted < timeInterval.days:
        currentdate += relativedelta(days=1)
        # print(currentdate)
        currentbalance -= averagespending
        if currentdate in salary:
            currentbalance += salary[currentdate]
        if currentdate in directDebitToPay:
            currentbalance -= directDebitToPay[currentdate]
        # prediction[time.mktime(currentdate.timetuple()) * 1000] = currentbalance
        prediction["date"].append(time.mktime(currentdate.timetuple()) * 1000)
        prediction["value"].append(currentbalance)
        daysPredicted += 1

    return prediction


# prediction for cc returns a dictionary with different attributes being the total amount of interest a user needs to pay,
# amount a user needs to pay to avoid cc fee
# minimum payment amount
# and it check the status of a cc if it's still in promotion
def getPredictionForCreditCard(a, testDate, accountID):
    billingdate = datetime.datetime(testDate.year, testDate.month, int(a['BillingDate'].split('-')[1]))
    interest = 0
    balance = 0  # float(a['Balance'][0]['Amount']['Amount'])
    if testDate.day > billingdate.day:
        targetdate = billingdate + relativedelta(months=1)
    else:
        targetdate = billingdate

    # chargedDate is the date before which all the purchases will be charged the interest
    chargedDate = targetdate - relativedelta(
        days=int(a['Product'][0]['CCC'][0]['CCCMarketingState'][1]['CoreProduct']['MaxPurchaseInterestFreeLengthDays'])
    )

    # check if the credit card is still in promotion
    for marketingState in a['Product'][0]['CCC'][0]['CCCMarketingState']:
        if marketingState['Identification'] == "P1":
            startDate = datetime.datetime.strptime(a['Account'][0]['OpeningDate'],
                                                   "%d-%m-%Y")
            if startDate + relativedelta(months=int(marketingState['StateTenureLength'])) > testDate:
                return ({"Interest": "Still in promotion, the interest is 0."})
        elif marketingState['Identification'] == "R1":
            minRepaymentRate = float(marketingState['Repayment']['MinBalanceRepaymentRate'])
            nonRepaymentCharge = float(
                marketingState['Repayment']['NonRepaymentFeeCharges'][0]['NonRepaymentFeeChargeDetail'][0]['FeeAmount'])
            for charge in marketingState['OtherFeesCharges']['FeeChargeDetail']:
                if charge['FeeType'] == "Purchase":
                    purchaseRate = float(charge['FeeRate'])
    for transaction in a['Transaction']:
        if transaction['TransactionId'] == a['Balance'][0]['LastPaidTransaction']:
            lastPaymentTime = datetime.datetime.strptime(transaction['ValueDateTime'],
                                                         "%Y-%m-%dT%H:%M:%S+00:00")
    for transaction in a['Transaction']:
        paymentTime = datetime.datetime.strptime(transaction['ValueDateTime'],
                                                 "%Y-%m-%dT%H:%M:%S+00:00")
        if paymentTime > lastPaymentTime:
            if paymentTime < chargedDate:
                balance += float(transaction['Amount']['Amount'])
                interest += (chargedDate.date() - paymentTime.date()).days * purchaseRate / 365
    result = {}
    result['BalanceWithInterest'] = balance
    result["Interest"] = interest
    result["minRepaymentAmount"] = float(a['Balance'][0]['Amount']['Amount']) * minRepaymentRate / 100
    result['balance'] = float(a['Balance'][0]['Amount']['Amount'])
    result['nextBillingDay'] = targetdate
    print(result)
    return result


def prediction(testDate, accountID):
    if not getData(accountID):
        # no data found
        return False
    if isCreditAccount(accountID):
        return getPredictionForCreditCard(getData(accountID), testDate, accountID)
    return getPredictionForCurrent(getData(accountID), testDate, accountID)


def getMonthlySpendDict(rows, indicator):
    monthDict = {}
    for row in rows:
        amount = float(row['Amount'])
        date = row['BookingDateTime']
        if str(date.month) + "-" + str(date.year) not in monthDict:
            monthDict[str(date.month) + "-" + str(date.year)] = 0
        if indicator == "spend":
            if amount < 0:
                monthDict[str(date.month) + "-" + str(date.year)] += amount
        if indicator == "income":
            if amount > 0:
                monthDict[str(date.month) + "-" + str(date.year)] += amount
    return monthDict


# calculates the minimum income per month
def getAverageMonthlyIncome(rows):
    monthDict = getMonthlySpendDict(rows, "income")
    if len(monthDict.values()) == 0:
        return 0
    return round(sum(monthDict.values()) / len(monthDict.values()), 2)


# calculates the average income per month
def getMinIncome(rows):
    monthDict = getMonthlySpendDict(rows, "income")
    if len(monthDict.values()) > 0:
        return min(monthDict.values())
    else:
        return 0


# returns average monthly spend on account
def getAverageMonthlySpend(rows):
    monthDict = getMonthlySpendDict(rows, "spend")
    if len(monthDict.values()) == 0:
        return 0
    return -round(sum(monthDict.values()) / len(monthDict.values()), 2)


# calculates minimum monthly spend- this is not average spend but rather the lowest amount of money you usually
# spend on your account
def getSpend(rows):
    monthDict = getMonthlySpendDict(rows, "spend")
    if len(monthDict.values()) > 0:
        return -round(max(monthDict.values()), 2)
    else:
        return 0


def calcExcess(rows):
    leftOver = []
    left = getMinIncome(rows) - getSpend(rows)
    if left >= 0:
        leftOver.append("On track to save: ")
    else:
        left = -left
        leftOver.append("Spends predicted to exceed income by:")
    leftOver.append(round(left, 2))
    return leftOver


# check if post request has been sent to update a certain cap
def updateCaps(request):
    possibleCapSetOn = ["getValueAll", "getValueBP", "getValueTP", "getValueGC", "getValueFC", "getValueFSC",
                        "getValueFoodC", "getValueGeneralC", "getValueEC", "getValueLSC", "getValueOC"]

    if request.method == "POST" and any(cap in request.POST for cap in possibleCapSetOn):
        chosenCapName = str(list(dict(request.POST).keys())[1])
        capValue = request.POST[chosenCapName]
        request.user.profile.setCap(chosenCapName, capValue)


# gets all the numerical values of the caps set on each category
def getAllCaps(request):
    possibleCapSetOn = ["getValueAll", "getValueBP", "getValueTP", "getValueGC", "getValueFC", "getValueFSC",
                        "getValueFoodC", "getValueGeneralC", "getValueEC", "getValueLSC", "getValueOC"]
    capValues = []
    for caps in possibleCapSetOn:
        capValues.append(float(request.user.profile.getCap(caps)[0]))
    print(capValues)
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


# handles POST request which gets correct data for pagination including actual data to display,
# the key and the setting for number of items per page
## no longer in use, replaced by more elegant solution
@DeprecationWarning
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

    # This is the code to put in a views.py method to use the above method
    # allows you to edit number of transactions per page
    # fetches all attributes required to allow for pagination
    # transPerPageList = ["10", "15", "20", "50", "AllTransactions"]
    # if request.method == "POST" and (request.POST['submit'] in transPerPageList):
    #     request.user.profile.setTransPerPage(request.POST.get('submit'))
    #
    # transPerPage = request.user.profile.getTransPerPage()
    # transPerPageList = makeFirstElement(transPerPage, transPerPageList)
    # pageElem, elems = getPaginationElements(request, transPerPage, page, rows, pageElem)
    # transPerPageList.pop(transPerPageList.index("AllTransactions"))
    return pageElem, elems


# takes a list of transactions, the page number and the number of transactions to display
@DeprecationWarning
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

# class UserID():
#     def __init__(self, userID):
#         self.transactions = getRows(userID)
#
#     @register.filter
#     def getTransactions(self):
#         return self.transactions
