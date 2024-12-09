from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models


class Printer(models.Model):
    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"Printer {self.slug} ({self.name})"


class PrintJobQuerySet(models.QuerySet):
    def with_finished(self):
        return self.annotate(
            finished_count=models.Count(
                "attempts", filter=models.Q(attempts__finished=True)
            ),
            finished=models.Q(finished_count__gte=models.F("count_needed")),
            running_or_finished_count=models.Count(
                "attempts",
                filter=(
                    models.Q(attempts__ended__isnull=True)
                    | models.Q(attempts__finished=True)
                ),
            ),
            can_attempt=models.Q(
                running_or_finished_count__lt=models.F("count_needed")
            ),
        )


class PrintJobManager(models.Manager):
    def get_queryset(self):
        return PrintJobQuerySet(self.model, using=self._db).with_finished()


class PrintJob(models.Model):
    slug = models.SlugField(primary_key=True)
    file_stl = models.FileField(null=True, blank=True)
    file_render = models.FileField(null=True)
    priority = models.PositiveIntegerField(
        default=100,
        help_text="Zahl von 0 bis 100. Jobs mit kleinen Zahlen werden weiter oben angezeigt.",
    )
    count_needed = models.PositiveIntegerField(default=1)

    objects = PrintJobManager()

    @property
    def running_attempts(self):
        return self.attempts.filter(ended__isnull=True)

    @property
    def attempting_users(self):
        user_ids = self.running_attempts.values_list("user", flat=True)
        users = get_user_model().objects.filter(pk__in=user_ids)
        return users

    def get_user_attempt(self, user):
        return self.running_attempts.filter(user=user).get()

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
    finished = models.BooleanField(default=False)
    dropped_off = models.BooleanField(default=False)

    def __str__(self):
        return f"Print Attempt at {self.job}: user={self.user}, ended={self.ended}"


class User(AbstractUser):
    max_attempts = models.IntegerField(
        null=True,
        blank=True,
        help_text=f"Maximale anzahl gleichzeitiger Drucke. 0 für unbegrenzt, leer = Default({settings.CROWDPRINTER_DEFAULT_MAX_ATTEMPTS})",
    )

    class Meta:
        db_table = "auth_user"
