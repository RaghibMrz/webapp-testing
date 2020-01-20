from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile 

#kwards just accepts any additional key word arguements on the end of the funct call
@receiver(post_save, sender=User)
def createProfile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def saveProfile(sender, instance, **kwargs):
	instance.profile.save()