from django.conf import settings
from django.db import models


class Printer(models.Model):
    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"Printer {self.slug} ({self.name})"


class PrintJob(models.Model):
    slug = models.SlugField(primary_key=True)
    file_stl = models.FileField(null=True, blank=True)
    file_render = models.FileField(null=True)
    finished = models.BooleanField(default=False)

    @property
    def running_attempt(self):
        return self.attempts.order_by("started").filter(ended__isnull=True).get()

    def __str__(self):
        return f"{self.slug}"


class PrintJobFile(models.Model):
    file_3mf = models.FileField(null=True, blank=True)
    file_gcode = models.FileField()
    job = models.ForeignKey(PrintJob, models.CASCADE, related_name="files")
    printer = models.ForeignKey(Printer, models.PROTECT)


class PrintAttempt(models.Model):
    job = models.ForeignKey(
        "PrintJob", on_delete=models.CASCADE, related_name="attempts"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    started = models.DateField(auto_now_add=True)
    ended = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Print Attempt at {self.job}: user={self.user}, ended={self.ended}"
