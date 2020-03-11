from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework.views import APIView

from users.forms import UserUpdateForm, ProfileUpdateForm
from .forms import ContactForm
# auxilliary file I made to hold some of the logic
from .utils import *


@login_required
def home(request):
    request.session.set_expiry(600)
    gotAccount = False
    if len(request.user.profile.getAccount()) > 0:
        accountid = request.user.profile.getAccount()[0]
        gotAccount = True
    if request.method == 'POST':
        accountid = request.POST.get('accountDropdown')
        gotAccount = True

    # if not gotAccount, then if statement will execute before checking 2nd argument, else it will have an account
    # thus no error handling is required
    if not gotAccount:
        accountid = "Null"
    if not getRows(accountid):
        context = {
            'rows': [{
                'TransactionInformation': 'Incorrect UserID linked',
                'Amount': 'Update accountID',
                'Currency': 'and try again',
                'BookingDateTime': 'No Data Found',
                'accountIDs': getStrAccountIDs(request.user.profile),
                'selectedAccount': accountid
            }]}
        return render(request, 'transactions/home.html', context)

    bpList, tpList, groceryList, fcList, financesList = [], [], [], [], []
    foodList, genList, entertainmentList, lsList, uncatList = [], [], [], [], []
    totalList, spendIndicatorList, numOfTransactions = [], [], []

    context = {
        'one': bpList,
        'two': tpList,
        'three': groceryList,
        'four': fcList,
        'five': financesList,
        'six': foodList,
        'seven': genList,
        'eight': entertainmentList,
        'nine': lsList,
        'zero': uncatList,
        'totals': totalList,
        'count': numOfTransactions,
        'spendIndicatorList': spendIndicatorList,
        'accountIDs': getStrAccountIDs(request.user.profile),
        'selectedAccount': accountid
    }

    # get data from database, store into "context" dictionary
    for transaction in getRows(accountid):
        context[getCategory(transaction['MCC'])].append(transaction)

    # gets number of transactions for treemap
    for catList in context:
        if catList == "totals":
            break
        numOfTransactions.append(len(context[catList]))

    # works out totals spend for each category
    for catList in context:
        if catList == "totals":
            break
        total, spendIndicator = getTotal(context[catList])
        spendIndicatorList.append(spendIndicator)
        totalList.append(total)

    print(context['accountIDs'])
    return render(request, 'transactions/home.html', context)


@login_required
def transactions(request):
    global accountid
    request.session.set_expiry(600)
    gotAccount = False
    if len(request.user.profile.getAccount()) > 0:
        accountid = request.user.profile.getAccount()[0]
        gotAccount = True
    if request.method == 'POST':
        accountid = request.POST.get('accountDropdown')
        gotAccount = True

    # if not gotAccount, then if statement will execute before checking 2nd argument, else it will have an account
    # thus no error handling is required
    if not gotAccount:
        accountid = "Error"
    if not getRows(accountid):
        context = {
            'rows': [{
                'TransactionInformation': "Incorrect UserID linked",
                'Amount': "Update accountID and try again",
                'Currency': "Error",
                'BookingDateTime': "No Data Found",
                'accountIDs': getStrAccountIDs(request.user.profile),
                'selectedAccount': accountid
            }]
        }
        return render(request, "transactions/transactions.html", context)

    total, spendIndicator = getTotal(getRows(accountid))
    context = {
        'rows': getRows(accountid),
        'total': total,
        'spendIndicator': spendIndicator,
        'accountIDs': getStrAccountIDs(request.user.profile),
        'selectedAccount': accountid
    }
    return render(request, 'transactions/transactions.html', context)


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
        'accountIDs': getStrAccountIDs(request.user.profile)
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
        elif idToRemove in getStrAccountIDs(request.user.profile):
            request.user.profile.deleteAccount(idToRemove)
        return redirect('profile')

# class ChartData(LoginRequiredMixin, APIView):
#     authentication_classes = []
#     permission_classes = []
#
#     def get(self, request, format=None):
#         labels = ['Bills & Payments', 'Transport', 'Groceries', 'Fashion & Cosmetics', 'Finances', 'Food', 'General',
#                   'Entertainment', 'Leisure & Self-Care', 'Other']
#         default_items = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
#         data = {
#             "labels": labels,
#             "default": default_items,
#         }
#         return Response(data)
