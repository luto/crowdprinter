from django.db import models
from django.conf import settings


class PrintFile(models.Model):
    slug = models.SlugField(primary_key=True)
    stl = models.FileField()


class PrintAttempt(models.Model):
    printfile = models.ForeignKey('PrintFile', on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    started = models.DateField(auto_now_add=True)
    finished = models.DateField(null=True, blank=True)
