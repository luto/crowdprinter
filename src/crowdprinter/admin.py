from django.contrib import admin
from .models import PrintJob, PrintAttempt


class PrintAttemptInline(admin.TabularInline):
    model = PrintAttempt


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    model = PrintJob
    inlines = [
        PrintAttemptInline,
    ]
