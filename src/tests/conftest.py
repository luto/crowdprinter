from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile

from crowdprinter.models import PrintAttempt
from crowdprinter.models import Printer
from crowdprinter.models import PrintJob


@pytest.fixture
def client_user(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def printer_prusa_xl():
    return Printer.objects.create(
        slug="xl",
        name="Prusa XL",
    )


@pytest.fixture
def printer_prusa_mini():
    return Printer.objects.create(
        slug="mini",
        name="Prusa MINI",
    )


def make_file(id):
    content = (str(id) * 100).encode("utf-8")
    return InMemoryUploadedFile(
        BytesIO(content),
        "field",
        str(id),
        "application/octet-stream",
        len(content),
        "utf-8",
    )


def make_job(name, **kwargs):
    return PrintJob.objects.create(
        slug=name,
        file_stl=make_file(f"stl_{name}"),
        file_render=make_file(f"render_{name}"),
        **kwargs,
    )


@pytest.fixture
def job_basic():
    return make_job("job_basic")


@pytest.fixture
def job_taken(user):
    job = make_job("job_taken")
    PrintAttempt.objects.create(
        job=job,
        user=user,
    )
    return job


@pytest.fixture
def job_basic_x50():
    return [make_job(f"job_basic_{i}") for i in range(100)]


@pytest.fixture
def job_basic_taken():
    return make_job("job_basic")


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        "user",
        "user@example.org",
    )
