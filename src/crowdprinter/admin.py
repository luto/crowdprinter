from django.contrib import admin
from .models import PrintFile, PrintAttempt


class PrintAttemptInline(admin.TabularInline):
    model = PrintAttempt


@admin.register(PrintFile)
class PrintFileAdmin(admin.ModelAdmin):
    model = PrintFile
    inlines = [
        PrintAttemptInline,
    ]
