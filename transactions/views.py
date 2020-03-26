import calendar

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from users.forms import UserUpdateForm, ProfileUpdateForm
from .forms import *
# auxiliary file I made to hold some of the logic
from .utils import *


# noinspection PySimplifyBooleanCheck
@login_required
def home(request):
    request.session.set_expiry(600)
    if getAccount(request) == "All":
        return redirect('summary')

    accountID = getAccount(request)

    if validateID(request, accountID) == True:
        context, rows = makeCatContext(request, accountID), getRows(request, accountID)

        # update categorical caps if necessary
        updateCaps(request)

        # gets date range selected by user, parses it and then updates transactions+details displayed
        if request.method == "POST" and 'submit' in request.POST:
            if request.POST['submit'] == "Enter":
                request.user.profile.setDateRange(request.POST.get('datetimes'))
            if request.POST['submit'] == "Clear":
                request.user.profile.setUseDateFilter("0")

        if request.user.profile.useDateFilter == "1":
            rawDates = request.user.profile.getDateRange().split("-")
            startDate, endDate = rawDates[0], rawDates[1]
            rows = getFilteredRows(rows, startDate, endDate)
            context['dateIndicator'] = "Transactions between " + str(startDate) + " - " + str(endDate)
        else:
            context['dateIndicator'] = "All transactions"

        # get data from database, store into "context" dictionary
        if rows != False:
            for transaction in rows:
                context[getCategory(transaction['MCC'])].append(transaction)

        return render(request, 'transactions/home.html', updateContext(context, rows, request, accountID, True))
    else:
        return render(validateID(request, accountID)[0], validateID(request, accountID)[1],
                      validateID(request, accountID)[2])


@login_required
def summary(request):
    request.session.set_expiry(600)
    context = getSummaryContext(request)
    return render(request, 'transactions/summary.html', context)


# special page for user's budgeting insights insights
@login_required
def caps(request):
    request.session.set_expiry(600)
    if getAccount(request) == "All":
        return redirect('summary')
    accountID = getAccount(request)

    if validateID(request, accountID) == True:
        tempcontext, rows = makeCatContext(request, accountID), getRows(request, accountID)
        if rows != False:
            endDay = str(calendar.monthrange(dateNow.year, dateNow.month)[1])
            startDate = "1/" + str(dateNow.month) + "/" + str(dateNow.year) + " 00:00 "
            endDate = " " + endDay + "/" + str(dateNow.month) + "/" + str(dateNow.year) + " 00:00"
            rows = getFilteredRows(rows, startDate, endDate)
            for transaction in rows:
                tempcontext[getCategory(transaction['MCC'])].append(transaction)
        totalList, spendIndicatorList, tempcontext = getCategoricalTotal(tempcontext)
        possibleCapSetOn = ["getValueBP", "getValueTP", "getValueGC", "getValueFC", "getValueFSC",
                            "getValueFoodC", "getValueGeneralC", "getValueEC", "getValueLSC", "getValueOC"]
        categories = ['Bills & Payments', 'Transport', 'Groceries', 'Fashion & Cosmetics', 'Finances', 'Food', 'General',
                      'Entertainment', 'Leisure & Self-Care', 'Other']

        categoricalSpend = {}
        for i in range(len(possibleCapSetOn)):
            if spendIndicatorList[i] == 'Spent':
                categoricalSpend[possibleCapSetOn[i]] = totalList[i]
            else:
                categoricalSpend[possibleCapSetOn[i]] = 0
        context = makeAggContext(request, accountID)
        context['spend'] = getAverageMonthlySpend(getRows(request, accountID))
        context['accountType'] = getAccountType(accountID)
        capvalues = getAllCaps(request)
        capsContext = []

        for num in range(len(categories)):
            capsContext.append(
                {'Category': categories[num], 'Spend': categoricalSpend[possibleCapSetOn[num]],
                 'Cap': capvalues[(num + 1)]})

        for cap in capsContext:
            if cap['Cap'] != 0:
                cap['Percentage'] = cap['Spend'] / cap['Cap'] * 100
            else:
                cap['Percentage'] = 0
        context['allCap'] = capvalues.pop(0)
        context['allSpend'] = sum(totalList)
        context['totalCap'] = sum(capvalues)
        if context['allCap'] > 0:
            context['totalPercentage'] = sum(totalList) / context['allCap'] * 100
        else:
            context['totalPercentage'] = 0
        context['capData'] = capsContext

        vals = list(categoricalSpend.values())
        context['mostExpCat'] = context['capData'][vals.index(max(vals))]
        return render(request, 'transactions/caps.html', context)
    else:
        return render(validateID(request, accountID)[0], validateID(request, accountID)[1],
               validateID(request, accountID)[2])


# noinspection PySimplifyBooleanCheck
@login_required
def transactions(request):
    request.session.set_expiry(600)
    if getAccount(request) == "All":
        return redirect('summary')

    accountID = getAccount(request)

    # update categorical caps if necessary
    updateCaps(request)

    if validateID(request, accountID) == True:
        context, rows = makeAggContext(request, accountID), getRows(request, accountID)

        # gets date range selected by user, parses it and then updates transactions+details displayed
        if request.method == "POST" and 'submit' in request.POST:
            if request.POST['submit'] == "Enter":
                request.user.profile.setDateRange(request.POST.get('datetimes'))
            if request.POST['submit'] == "Clear":
                request.user.profile.setUseDateFilter("0")

        if request.user.profile.useDateFilter == "1":
            rawDates = request.user.profile.getDateRange().split("-")
            startDate, endDate = rawDates[0], rawDates[1]
            rows = getFilteredRows(rows, startDate, endDate)
            context['dateIndicator'] = "Transactions between " + str(startDate) + " - " + str(endDate)
        else:
            context['dateIndicator'] = "All transactions"
        context['rows'] = rows
        return render(request, 'transactions/transactions.html',
                      updateContext(context, rows, request, accountID, False))
    else:
        return render(validateID(request, accountID)[0], validateID(request, accountID)[1],
                      validateID(request, accountID)[2])


@login_required
def profile(request):
    request.session.set_expiry(600)
    if request.method == 'POST':
        uForm = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        pForm = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if uForm.is_valid() and pForm.is_valid():
            newAccountID = pForm.cleaned_data.get('accountID')
            request.user.profile.addToAccountList(newAccountID)

            # getDataForAccount(newAccountID)
            uForm.save()
            pForm.save()
            messages.success(request, f'Account successfully updated')
            return redirect('profile')
    # return statement in line above is to prevent user from falling to line below
    # phenomenon called 'get-redirect pattern'- when u reload browser after submitting data
    # post request will be duplicated.
    else:
        uForm = UserUpdateForm(instance=request.user)
        pForm = ProfileUpdateForm(instance=request.user.profile)
    context = {
        'uForm': uForm,
        'pForm': pForm,
        'accountIDs': getAccountIDsFromModel(request.user.profile)
    }
    return render(request, "transactions/profile.html", context)


@login_required
def report(request):
    request.session.set_expiry(600)
    return render(request, 'transactions/report.html')


@login_required
def helpPage(request):
    request.session.set_expiry(600)
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid:
            form.save()
            messages.success(request, f'Message sent!')
            send_mail(form.cleaned_data.get('subject'),
                      form.cleaned_data.get('message') + "\n\n Reply to: " + form.cleaned_data.get('email'),
                      'pwresetst45@gmail.com', ['pwresetst45@gmail.com'])
            return redirect('home')
    else:
        form = ContactForm()
    context = {
        'form': form
    }
    return render(request, 'transactions/help.html', context)


@login_required
def delete(request):
    request.session.set_expiry(600)
    if request.method == "POST":
        idToRemove = request.POST.get('accountDropdown')
        if idToRemove == "All":
            request.user.profile.clearAccountList()
        if idToRemove == "AllCurr":
            request.user.profile.clearCurrAccounts()
        if idToRemove == "AllCC":
            request.user.profile.clearCCAccounts()
        elif idToRemove in getAccountIDsFromModel(request.user.profile):
            request.user.profile.deleteAccount(idToRemove)

        accountList = getAccountIDsFromModel(request.user.profile)
        if len(accountList) > 0:
            request.user.profile.setAccountID(accountList[0])
        else:
            request.user.profile.setAccountID("None")
        return redirect('profile')
