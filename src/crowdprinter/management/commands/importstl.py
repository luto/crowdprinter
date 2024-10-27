import argparse
import os.path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.utils.text import slugify

import crowdprinter.models as models


class Command(BaseCommand):
    help = "add the given STL file to the database"

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, required=True)
        parser.add_argument(
            "--stl-file", type=argparse.FileType(mode="br"), required=True
        )
        parser.add_argument(
            "--render-file", type=argparse.FileType(mode="br"), required=True
        )

    def _save_file(self, f, slug, extension):
        path = default_storage.get_available_name(f"{slug}.{extension}")
        cfile = ContentFile(f.read())
        default_storage.save(path, cfile)
        return path, cfile

    def handle(self, *args, **options):
        slug = slugify(options["slug"])

        if models.PrintJob.objects.filter(slug=slug).exists():
            raise CommandError(f"slug {slug} is already taken.")

        f = models.PrintJob(slug=slug)
        f.stl.save(*self._save_file(options["stl_file"], slug, "stl"))
        render_ext = os.path.splitext(options["render_file"].name)[1]
        f.render.save(*self._save_file(options["render_file"], slug, render_ext))
