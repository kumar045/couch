from django.db import models

# Create your models here.
class Stream(models.Model):
    query = models.CharField(max_length=1110010000)

    

