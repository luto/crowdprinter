from django.contrib.auth.decorators import login_required
from django.views.generic.base import View, TemplateView
from django.views.generic import DetailView, ListView
import crowdprinter.models as models
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
from django.urls import reverse
import os.path
import math
import random


class PrintJobListView(ListView):
    model = models.PrintJob
    paginate_by = 50

    def get_context_data(self):
        context = super().get_context_data()
        all_count = models.PrintJob.objects.count()
        done_count = models.PrintJob.objects.filter(finished=True).count()
        context['progress_percent'] = math.floor((done_count / all_count) * 100)
        count = context['object_list'].count()
        if count < self.paginate_by:
            context['object_list'] = list(context['object_list'])
            context['object_list'] = context['object_list'] * math.ceil((self.paginate_by - count) / count)
            random.shuffle(context['object_list'])
        return context

    def get_queryset(self):
        return super().get_queryset().filter(finished=False)

    def get_ordering(self):
        return '?'


class PrintJobDetailView(DetailView):
    model = models.PrintJob


@login_required
def take_print_job(request, slug):
    if request.method == 'POST':
        models.PrintAttempt.objects.create(
            job=get_object_or_404(models.PrintJob, slug=slug),
            user=request.user,
        )

    return HttpResponseRedirect(reverse('printjob_detail', kwargs={'slug': slug}))


class ServeFileView(View):

    def get(self, *args, **kwargs):
        with open(self.get_file_path(**kwargs), mode='rb') as f:
            response = HttpResponse(
                f.read(),
                content_type='application/force-download',
            )
        dl_path = self.get_download_file_name(**kwargs)
        response['Content-Disposition'] = f'attachment; filename={dl_path}'
        return response

    def get_file_path(self, **kwargs):
        raise NotImplementedError()

    def get_download_file_name(self, **kwargs):
        raise NotImplementedError()


class ServeStlView(ServeFileView):
    def get_file_path(self, **kwargs):
        printjob = get_object_or_404(models.PrintJob, slug=kwargs['slug'])
        return printjob.stl.path

    def get_download_file_name(self, **kwargs):
        return f'eh19_{kwargs["slug"]}.stl'


class ServeRenderView(ServeFileView):
    def get_file_path(self, **kwargs):
        printjob = get_object_or_404(models.PrintJob, slug=kwargs['slug'])
        return printjob.render.path

    def get_download_file_name(self, **kwargs):
        printjob = get_object_or_404(models.PrintJob, slug=kwargs['slug'])
        ext = os.path.splitext(printjob.render.path)[1]
        return f'eh19_{kwargs["slug"]}.{ext}'
