from django.db import models
from django.contrib.auth.models import User
from PIL import Image

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	img = models.ImageField(default='default.png', upload_to='profilePics')
	accountID = models.CharField(max_length=14, blank=True, help_text="Please enter the 14 digit identification to allow us to connect you to the database")
	accountIDList = models.CharField(max_length=128, blank=True)

	def __str__(self):
		return f'{self.user.username}\'s Profile'

	def getAccount(self):
		return self.accountIDList

	def storeAccount(self, accList):
		self.accountIDList = self.accountIDList+","+(accList)

	def clearAccountList(self):
		self.accountIDList = ""

	#overriding save method to scale down any uploaded picture
	#optimises speed and saves space
	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		image = Image.open(self.img.path)
		if image.height > 200 or image.width > 200:
			outputSize = (200, 200)
			image = image.resize(outputSize)
			image.save(self.img.path)