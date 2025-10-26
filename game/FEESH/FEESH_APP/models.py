from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.db import models
# Create your models here.
#Every user is gonna have a point 
class User(AbstractUser): 
    ID = models.BigAutoField(primary_key= True)
    point = models.IntegerField(default=0)
    pass
