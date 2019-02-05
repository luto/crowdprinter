from django.contrib import admin
from .models import PrintJob, PrintAttempt


class PrintAttemptInline(admin.TabularInline):
    model = PrintAttempt
    readonly_fields = (
        'started',
    )
    fields = (
        'user',
        'started',
        'finished',
    )


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    model = PrintJob
    inlines = [
        PrintAttemptInline,
    ]
    list_filter = [
        'finished'
    ]


@admin.register(PrintAttempt)
class PrintAttemptAdmin(admin.ModelAdmin):
    model = PrintAttempt
    list_display = (
        'user',
        'job',
        'started',
        'ended',
    )
    list_display_links = (
        'user',
        'job',
    )
    list_filter = [
        'user'
    ]
