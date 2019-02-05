from django.contrib import admin
from django.utils.html import format_html
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
        'job_link',
        'started',
        'ended',
    )
    list_filter = [
        'user'
    ]
    def job_link(self, obj):
        url = f'/admin/crowdprinter/printjob/{obj.job_id}/change/'
        return format_html("<a href='{}'>{}</a>", url, obj.job_id)
    job_link.admin_order_field = 'job'
    job_link.short_description = 'job'
