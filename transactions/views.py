from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect

from users.forms import UserUpdateForm, ProfileUpdateForm
from .forms import *
# auxiliary file I made to hold some of the logic
from .utils import *


# noinspection PySimplifyBooleanCheck
@login_required
def home(request):
    request.session.set_expiry(600)
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
        # print(rows)
        if rows != False:
            for transaction in rows:
                context[getCategory(transaction['MCC'])].append(transaction)

        return render(request, 'transactions/home.html', updateContext(context, rows, request, accountID, True))
    else:
        return render(validateID(request, accountID)[0], validateID(request, accountID)[1], validateID(request, accountID)[2])

@login_required
def summary(request):
    request.session.set_expiry(600)
    accountID = getAccount(request)
    return render(request, 'transactions/summary.html')

# special page for user's budgeting insights insights
@login_required
def caps(request):
    request.session.set_expiry(600)
    accountID = getAccount(request)
    context = makeAggContext(request, accountID)
    context['spend'] = getAverageMonthlySpend(getRows(request, accountID))
    context['accountType'] = getAccountType(accountID)
    caps = getAllCaps(request)
    context['allCap'] = caps.pop(0)
    context['totalCap'] = sum(caps)
    return render(request, 'transactions/caps.html', context)

# noinspection PySimplifyBooleanCheck
@login_required
def transactions(request):
    request.session.set_expiry(600)
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
        return render(validateID(request, accountID)[0], validateID(request, accountID)[1], validateID(request, accountID)[2])


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
