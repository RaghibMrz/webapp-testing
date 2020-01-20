from django.db import models

class Contact(models.Model):
	subject = models.CharField(max_length=64)
	email = models.EmailField()
	message = models.TextField()

	def __str__(self):
		return f'{self.subject} {self.email}'
