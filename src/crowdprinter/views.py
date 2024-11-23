import datetime
import math
import os.path
import random
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import FileResponse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic.base import View

import crowdprinter.models as models
import stl_generator
import stl_generator_jadyn

from .models import PrintJob


class SuperUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class PrintJobListView(ListView):
    model = models.PrintJob
    paginate_by = 6 * 4
    context_object_name = "jobs"

    def get_context_data(self):
        context = super().get_context_data()
        all_count = models.PrintJob.objects.count()
        done_count = models.PrintJob.objects.filter(finished=True).count()
        context["progress_percent"] = max(
            math.floor((done_count / max(1, all_count)) * 100), 5
        )
        count = context["jobs"].count()
        if count < self.paginate_by:
            context["jobs"] = list(context["jobs"])
            context["jobs"] = context["jobs"] * math.ceil(
                (self.paginate_by - count) / max(1, count)
            )
            random.shuffle(context["jobs"])
        return context

    def get_queryset(self):
        return super().get_queryset().filter(can_attempt=True).order_by("?")


def make_gcode_files(job):
    for printer in [
        # TODO: support multiple printers w/ presets
        models.Printer.objects.first()
    ]:
        with (tempfile.NamedTemporaryFile(suffix=".gcode", delete=False) as f_gcode,):
            stl_generator.stl_to_gcode(job.file_stl.path, f_gcode)
            models.PrintJobFile.objects.create(
                job=job,
                printer=printer,
                file_gcode=ContentFile(f_gcode.read(), name=f"{job.slug}.gcode"),
            )


class PrintJobTextForm(forms.ModelForm):
    text = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"rows": 4, "cols": 40}),
    )

    class Meta:
        model = PrintJob
        fields = [
            "slug",
            "count_needed",
            "text",
        ]

    @transaction.atomic
    def save(self, commit=True):
        job = super().save(commit=False)
        slug = self.cleaned_data.get("slug")

        with (
            tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f_stl,
            tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f_png,
        ):
            sign = stl_generator_jadyn.Sign(
                content=stl_generator_jadyn.SignContent(
                    text=self.cleaned_data.get("text"),
                    braille="⠓⠓⠓",  # TODO: use JS code on the client? rewrite in python?
                ),
            ).render()
            sign.save(f_stl, angularTolerance=0.5)
            job.file_stl = ContentFile(f_stl.read(), name=f"{slug}.stl")

            stl_generator.stl_to_png(f_stl.name, f_png)
            f_png.seek(0)
            job.file_render = ContentFile(f_png.read(), name=f"{slug}.png")

            job.save()
            make_gcode_files(job)

        return job


class PrintJobTextCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "crowdprinter/printjob_create_form.html"
    model = PrintJob
    form_class = PrintJobTextForm
    success_url = reverse_lazy("printjob_create_text")
    success_message = "Job %(slug)s was created successfully"


class PrintJobStlForm(forms.ModelForm):
    class Meta:
        model = PrintJob
        fields = [
            "slug",
            "count_needed",
            "file_stl",
        ]

    @transaction.atomic
    def save(self, commit=True):
        job = super().save(commit=False)
        slug = self.cleaned_data.get("slug")

        with (tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f_png,):
            stl_generator.stl_to_png(job.file_stl.path, f_png)
            f_png.seek(0)
            job.file_render = ContentFile(f_png.read(), name=f"{slug}.png")

            job.save()

            make_gcode_files(job)

        return job


class PrintJobStlCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "crowdprinter/printjob_create_form.html"
    model = PrintJob
    form_class = PrintJobStlForm
    success_url = reverse_lazy("printjob_create_stl")
    success_message = "Job %(slug)s was created successfully"


class MyPrintAttempts(ListView):
    model = models.PrintAttempt
    template_name = "crowdprinter/myprintattempts.html"
    ordering = ["ended"]
    context_object_name = "attempts"

    def get_context_data(self):
        context = super().get_context_data()
        context["finished_attempts"] = context["attempts"].filter(
            ended__isnull=False, finished=True
        )
        context["running_attempts"] = context["attempts"].filter(ended__isnull=True)
        del context["attempts"]
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
    context_object_name = "job"

    def get_context_data(self, object):
        context = super().get_context_data()
        if self.request.user.is_authenticated:
            context["can_take_job"] = can_take_job(self.request.user, self.object)
        context["max_jobs"] = max_jobs
        return context


@login_required
def take_print_job(request, slug):
    job = get_object_or_404(models.PrintJob, slug=slug)
    if request.method == "POST" and can_take_job(request.user, job):
        models.PrintAttempt.objects.create(
            job=job,
            user=request.user,
        )

    return HttpResponseRedirect(reverse("printjob_detail", kwargs={"slug": slug}))


@login_required
def give_back_print_job(request, slug):
    if request.method == "POST":
        attempt = get_object_or_404(
            models.PrintAttempt,
            job__slug=slug,
            user=request.user,
            ended__isnull=True,
        )
        attempt.ended = datetime.date.today()
        attempt.save()

    return HttpResponseRedirect(reverse("printjob_detail", kwargs={"slug": slug}))


@login_required
def printjob_done(request, slug):
    if request.method == "POST":
        attempt = get_object_or_404(
            models.PrintAttempt,
            job__slug=slug,
            user=request.user,
            ended__isnull=True,
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
        dl_filename = f'{settings.DOWNLOAD_FILE_PREFIX}{kwargs["slug"]}{ext}'
        return FileResponse(
            open(path, mode="rb"),
            as_attachment=self.as_attachment,
            filename=dl_filename,
        )

    def get_file_path(self, **kwargs):
        raise NotImplementedError()


class ServeStlView(ServeFileView):
    def get_file_path(self, **kwargs):
        printjob = get_object_or_404(
            models.PrintJob,
            slug=kwargs["slug"],
        )
        if self.request.user not in printjob.attempting_users:
            raise Http404()
        return printjob.file_stl.path


@method_decorator([cache_control(max_age=315360000)], name="dispatch")
class ServeRenderView(ServeFileView):
    as_attachment = False

    def get_file_path(self, **kwargs):
        printjob = get_object_or_404(
            models.PrintJob,
            slug=kwargs["slug"],
        )
        return printjob.file_render.path


class ServeJobFileView(ServeFileView):
    def get_file_path(self, **kwargs):
        printjobfile = get_object_or_404(
            models.PrintJobFile,
            printer=kwargs["printer"],
            job__slug=kwargs["slug"],
            job__attempts__user=self.request.user,
        )

        if kwargs["ext"] == "3mf":
            return printjobfile.file_3mf.path
        elif kwargs["ext"] == "gcode":
            return printjobfile.file_gcode.path
        else:
            raise Http404()


class InfoView(TemplateView):
    template_name = "crowdprinter/info.html"


class FaqView(TemplateView):
    template_name = "crowdprinter/faq.html"
