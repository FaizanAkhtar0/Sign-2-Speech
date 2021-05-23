from django.db import models

# Create your models here.


class HistoryModel(models.Model):
    id = models.IntegerField(primary_key=True)
    history = models.CharField(max_length=2000)
    date_time = models.CharField(max_length=500)

