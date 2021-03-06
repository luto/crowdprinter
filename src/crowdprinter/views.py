from django.contrib.auth.decorators import login_required
from django.views.generic.base import View, TemplateView
from django.views.generic import DetailView, ListView
import crowdprinter.models as models
from django.db.models import IntegerField, Count, Case, When, Q
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect, Http404
from django.urls import reverse
import os.path
import math
import random
import datetime


class PrintJobListView(ListView):
    model = models.PrintJob
    paginate_by = 50

    def get_context_data(self):
        context = super().get_context_data()
        all_count = models.PrintJob.objects.count()
        done_count = models.PrintJob.objects.filter(finished=True).count()
        context['progress_percent'] = max(math.floor((done_count / all_count) * 100), 5)
        count = context['object_list'].count()
        if count < self.paginate_by:
            context['object_list'] = list(context['object_list'])
            context['object_list'] = context['object_list'] * math.ceil((self.paginate_by - count) / count)
            random.shuffle(context['object_list'])
        return context

    def get_queryset(self):
        return super().get_queryset().annotate(
            running_attempts_count=Count(
                Case(When(~Q(attempts__ended__isnull=False), then=1), output_field=IntegerField())
            ),
            attempts_count=Count('attempts')
        ).filter(Q(running_attempts_count=0) | Q(attempts_count=0), finished=False)
    def get_ordering(self):
        return '?'


class MyPrintAttempts(ListView):
    model = models.PrintAttempt
    template_name = 'crowdprinter/myprintattempts.html'
    ordering = ['ended']

    def get_context_data(self):
        context = super().get_context_data()
        context['finished'] = context['object_list'].filter(ended__isnull=False)
        context['running'] = context['object_list'].filter(ended__isnull=True)
        del context['object_list']
        return context

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


max_jobs = 3

class PrintJobDetailView(DetailView):
    model = models.PrintJob

    def get_context_data(self, object):
        context = super().get_context_data()
        if self.request.user.is_authenticated:
            context['can_take'] = models.PrintAttempt.objects.filter(user=self.request.user, ended__isnull=True).count() < max_jobs
        context['max_jobs'] = max_jobs
        return context


@login_required
def take_print_job(request, slug):
    if request.method == 'POST' and (models.PrintAttempt.objects.filter(user=request.user, ended__isnull=True).count() < max_jobs):
        models.PrintAttempt.objects.create(
            job=get_object_or_404(models.PrintJob, slug=slug),
            user=request.user,
        )

    return HttpResponseRedirect(reverse('printjob_detail', kwargs={'slug': slug}))


@login_required
def give_back_print_job(request, slug):
    if request.method == 'POST':
        job = get_object_or_404(models.PrintJob, slug=slug)
        if job.running_attempt.user == request.user:
            # setting job.running_attempt.ended doesn't work
            models.PrintAttempt.objects.filter(pk=job.running_attempt.pk).update(
                ended=datetime.date.today()
            )

    return HttpResponseRedirect(reverse('printjob_detail', kwargs={'slug': slug}))


@login_required
def printjob_done(request, slug):
    if request.method == 'POST':
        job = get_object_or_404(models.PrintJob, slug=slug)
        if job.running_attempt.user == request.user:
            # setting job.running_attempt.ended doesn't work
            models.PrintAttempt.objects.filter(pk=job.running_attempt.pk).update(
                ended=datetime.date.today()
            )
            job.finished = True
            job.save()

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
        response['Cache-Control'] = 'public, max-age=31536000'
        return response

    def get_file_path(self, **kwargs):
        raise NotImplementedError()

    def get_download_file_name(self, **kwargs):
        raise NotImplementedError()


class ServeStlView(ServeFileView):
    def get_file_path(self, **kwargs):
        printjob = get_object_or_404(models.PrintJob, slug=kwargs['slug'])
        if printjob.running_attempt.user != self.request.user:
            raise Http404()
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
