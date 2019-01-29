from django.db import models
from django.conf import settings


class PrintJob(models.Model):
    slug = models.SlugField(primary_key=True)
    stl = models.FileField()
    render = models.FileField(null=True)
    finished = models.BooleanField(default=False)

    @property
    def running_attempt(self):
        return self.attempts.order_by('started').filter(ended__isnull=True).get()


class PrintAttempt(models.Model):
    job = models.ForeignKey('PrintJob', on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    started = models.DateField(auto_now_add=True)
    ended = models.DateField(null=True, blank=True)
