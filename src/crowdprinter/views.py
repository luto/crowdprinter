from django.views.generic.base import TemplateView, View
import crowdprinter.models as models
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import os.path


class IndexView(TemplateView):
    template_name = "crowdprinter/index.html"


class ServeFileView(View):

    def get(self, *args, **kwargs):
        with open(self.get_file_path(**kwargs)) as f:
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
        printfile = get_object_or_404(models.PrintFile, slug=kwargs['slug'])
        return printfile.stl.path

    def get_download_file_name(self, **kwargs):
        return f'eh19_{kwargs["slug"]}.stl'
