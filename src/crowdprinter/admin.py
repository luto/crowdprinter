from django.contrib import admin
from django.utils.html import format_html

from .models import PrintAttempt
from .models import Printer
from .models import PrintJob
from .models import PrintJobFile


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    model = Printer


class PrintAttemptInline(admin.TabularInline):
    model = PrintAttempt
    readonly_fields = ("started",)
    fields = (
        "user",
        "started",
        "ended",
        "finished",
        "dropped_off",
    )
    extra = 0


class PrintJobFileInline(admin.TabularInline):
    model = PrintJobFile
    fields = (
        "file_3mf",
        "file_gcode",
        "printer",
    )
    extra = 0


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    model = PrintJob
    inlines = [
        PrintJobFileInline,
        PrintAttemptInline,
    ]


@admin.register(PrintAttempt)
class PrintAttemptAdmin(admin.ModelAdmin):
    model = PrintAttempt
    list_display = (
        "user",
        "job_link",
        "started",
        "ended",
    )
    list_filter = ["user"]

    def job_link(self, obj):
        url = f"/admin/crowdprinter/printjob/{obj.job_id}/change/"
        return format_html("<a href='{}'>{}</a>", url, obj.job_id)

    job_link.admin_order_field = "job"
    job_link.short_description = "job"
