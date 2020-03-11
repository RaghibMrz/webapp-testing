from django.db import models
from django.contrib.auth.models import User
from PIL import Image


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    img = models.ImageField(default='default.png', upload_to='profilePics')
    accountID = models.CharField(max_length=14, blank=True,
                                 help_text="Enter Account ID to link us to your debit/credit card")
    accountIDList = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f'{self.user.username}\'s Profile'

	def getAccount(self):  # this returns a qeury set of all accountids under the user, loop through the query set just as a list
		return Account.objects.filter(user__username = self.user.username).values_list('accountid', flat=True)
    def clearAccountList(self):
        for accountid in self.getAccount():
            Account.objects.filter(accountid=str(accountid), user=self.user).delete()

    def deleteAccount(self, accountID):
        if accountID in self.getAccount():
            Account.objects.filter(accountid=str(accountID), user=self.user).delete()

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
