from django.db import models
from django.contrib.auth.models import User
from PIL import Image


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    img = models.ImageField(default='default.png', upload_to='profilePics')
    accountID = models.CharField(max_length=14, blank=True,
                                 help_text="Enter Account ID to link us to your debit/credit card")
    gotAccount = models.CharField(max_length=1, blank=False, default="0")
    transPerPage = models.CharField(max_length=14, blank=False, default="10")
    dateRange = models.CharField(max_length=128, blank=False, default="None")
    useDateFilter = models.CharField(max_length=1, blank=False, default="0")

    def __str__(self):
        return f'{self.user.username}\'s Profile'

    # below are the methods for getting/setting categorical caps
    def getCap(self, name):
        if name not in self.getCapNames():
            return [0]
        return CategoryCap.objects.filter(name=name, accountid=self.getAccountID(), user=self.user).values_list('amount', flat=True)

    def setCap(self, name, value):
        if name not in self.getCapNames():
            CategoryCap.objects.create(amount=value, name=name, accountid=self.getAccountID(), user=self.user)
        else:
            CategoryCap.objects.filter(name=name, accountid=self.getAccountID(), user=self.user).delete()
            CategoryCap.objects.create(amount=value, name=name, accountid=self.getAccountID(), user=self.user)

    def getCapNames(self):
        return CategoryCap.objects.filter(accountid=self.getAccountID(), user__username=self.user.username).values_list('name', flat=True)

    # below are the methods for accessing a user's bank accountID's
    def getGotAccount(self):
        return self.gotAccount

    def setGotAccount(self, value):
        self.gotAccount = value
        self.save()

    def setAccountID(self, accountID):
        self.gotAccount = "1"
        self.accountID = accountID
        self.save()

    def getAccountID(self):
        return self.accountID

    def getAccount(self):
        return Account.objects.filter(user__username=self.user.username).values_list('accountid', flat=True)

    def addToAccountList(self, accountID):
        if accountID not in self.getAccount():
            Account.objects.create(accountid=str(accountID), user=self.user)

    def clearAccountList(self):
        for accountid in self.getAccount():
            Account.objects.filter(accountid=str(accountid), user=self.user).delete()
        self.gotAccount = "0"
        self.accountID = "Null"

    def deleteAccount(self, accountID):
        if accountID in self.getAccount():
            Account.objects.filter(accountid=str(accountID), user=self.user).delete()
        if accountID == self.accountID:
            self.accountID = "Null"
            self.gotAccount = "0"

    def getTransPerPage(self):
        return self.transPerPage

    def setTransPerPage(self, transactions):
        self.transPerPage = transactions
        self.save()

    def getDateRange(self):
        return self.dateRange

    def setDateRange(self, data):
        self.dateRange = data
        self.useDateFilter = "1"
        self.save()

    def setUseDateFilter(self, data):
        self.useDateFilter = data
        self.dateRange = "None"
        self.save()

    def getUseDateFilter(self):
        return self.useDateFilter

    # overriding save method to scale down any uploaded picture
    # optimises speed and saves space
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        image = Image.open(self.img.path)
        if image.height > 200 or image.width > 200:
            outputSize = (200, 200)
            image = image.resize(outputSize)
            image.save(self.img.path)


# Auxiliary class with a user field, and accountID field to allow one "IcyBank" user to connect multiple accountIDs
class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    accountid = models.CharField(max_length=20)


# Same principle as list of accountIDs used to give one account multiple caps
class CategoryCap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    accountid = models.CharField(max_length=20)
    name = models.CharField(max_length=64, blank=False)
    amount = models.CharField(max_length=64, blank=False, default="0")