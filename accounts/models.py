from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=50)
    gcash_number = models.CharField(max_length=20)
    gcash_name = models.CharField(max_length=100)   
    bank_name = models.CharField(max_length=100)     
    bank_number = models.CharField(max_length=30)    

    def __str__(self):
        return f"{self.user.username}'s profile"
