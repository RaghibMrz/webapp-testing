from django.db import models
from django.contrib.auth.models import User
from PIL import Image


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    img = models.ImageField(default='default.png', upload_to='profilePics')
    accountID = models.CharField(max_length=14, blank=True,
                                 help_text="Enter Account ID to link us to your debit/credit card")
    accountIDList = models.CharField(max_length=128, blank=True)
    gotAccount = models.CharField(max_length=1, blank=False)

    def __str__(self):
        return f'{self.user.username}\'s Profile'

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

    # overriding save method to scale down any uploaded picture
    # optimises speed and saves space
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        image = Image.open(self.img.path)
        if image.height > 200 or image.width > 200:
            outputSize = (200, 200)
            image = image.resize(outputSize)
            image.save(self.img.path)


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    accountid = models.CharField(max_length=20)
