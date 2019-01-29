import crowdprinter.models as models


def add_header_footer_stls(request):
    return {
        'stls_header': models.PrintJob.objects.order_by('?')[:40],
        'stls_footer': models.PrintJob.objects.order_by('?')[:40],
    }
