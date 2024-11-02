import datetime
import math
import os.path
import random

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.base import View

import crowdprinter.models as models


class PrintJobListView(ListView):
    model = models.PrintJob
    paginate_by = 50

    def get_context_data(self):
        context = super().get_context_data()
        all_count = models.PrintJob.objects.count()
        done_count = models.PrintJob.objects.filter(finished=True).count()
        context["progress_percent"] = max(
            math.floor((done_count / max(1, all_count)) * 100), 5
        )
        count = context["object_list"].count()
        if count < self.paginate_by:
            context["object_list"] = list(context["object_list"])
            context["object_list"] = context["object_list"] * math.ceil(
                (self.paginate_by - count) / max(1, count)
            )
            random.shuffle(context["object_list"])
        return context

    def get_queryset(self):
        return super().get_queryset().filter(can_attempt=True).order_by("?")


class MyPrintAttempts(ListView):
    model = models.PrintAttempt
    template_name = "crowdprinter/myprintattempts.html"
    ordering = ["ended"]

    def get_context_data(self):
        context = super().get_context_data()
        context["finished"] = context["object_list"].filter(ended__isnull=False)
        context["running"] = context["object_list"].filter(ended__isnull=True)
        del context["object_list"]
        return context

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


max_jobs = 3


def can_take_job(user, job):
    return (
        models.PrintAttempt.objects.filter(user=user, ended__isnull=True).count()
        < max_jobs
    ) and user not in job.attempting_users


class PrintJobDetailView(DetailView):
    model = models.PrintJob

    def get_context_data(self, object):
        context = super().get_context_data()
        if self.request.user.is_authenticated:
            context["can_take"] = can_take_job(self.request.user, self.object)
        context["max_jobs"] = max_jobs
        return context


@login_required
def take_print_job(request, slug):
    job = get_object_or_404(models.PrintJob, slug=slug)
    if request.method == "POST" and can_take_job(request.user, job):
        models.PrintAttempt.objects.create(job=job, user=request.user)

    return HttpResponseRedirect(reverse("printjob_detail", kwargs={"slug": slug}))


@login_required
def give_back_print_job(request, slug):
    if request.method == "POST":
        attempt = get_object_or_404(
            models.PrintAttempt, job__slug=slug, user=request.user, ended__isnull=True
        )
        attempt.ended = datetime.date.today()
        attempt.save()

    return HttpResponseRedirect(reverse("printjob_detail", kwargs={"slug": slug}))


@login_required
def printjob_done(request, slug):
    if request.method == "POST":
        attempt = get_object_or_404(
            models.PrintAttempt, job__slug=slug, user=request.user, ended__isnull=True
        )
        attempt.ended = datetime.date.today()
        attempt.finished = True
        attempt.save()

    return HttpResponseRedirect(reverse("printjob_detail", kwargs={"slug": slug}))


class ServeFileView(View):
    as_attachment = True

    def get(self, *args, **kwargs):
        path = self.get_file_path(**kwargs)
        ext = os.path.splitext(path)[1]
        dl_filename = f'{settings.DOWNLOAD_FILE_PREFIX}_{kwargs["slug"]}.{ext}'
        return FileResponse(
            open(path, mode="rb"),
            as_attachment=self.as_attachment,
            filename=dl_filename,
        )

    def get_file_path(self, **kwargs):
        raise NotImplementedError()


class ServeStlView(ServeFileView):
    def get_file_path(self, **kwargs):
        printjob = get_object_or_404(models.PrintJob, slug=kwargs["slug"])
        if self.request.user not in printjob.attempting_users:
            raise Http404()
        return printjob.file_stl.path


class ServeRenderView(ServeFileView):
    as_attachment = False

    def get_file_path(self, **kwargs):
        printjob = get_object_or_404(models.PrintJob, slug=kwargs["slug"])
        return printjob.file_render.path


class ServeJobFileView(ServeFileView):
    def get_file_path(self, **kwargs):
        printjobfile = get_object_or_404(models.PrintJobFile, pk=kwargs["fileid"])

        if printjobfile.job.slug != kwargs["slug"]:
            raise Http404()
        if self.request.user not in printjobfile.job.attempting_users:
            raise Http404()

        if kwargs["ext"] == "3mf":
            return printjobfile.file_3mf.path
        elif kwargs["ext"] == "gcode":
            return printjobfile.file_gcode.path
        else:
            raise Http404()
