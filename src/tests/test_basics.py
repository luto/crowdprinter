import re

import pytest

from crowdprinter.models import PrintAttempt


@pytest.mark.django_db
def test_index_empty(client):
    resp = client.get("/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_index(client, job_basic_x50):
    resp = client.get("/")
    assert resp.status_code == 200
    content = resp.content.decode()
    # images
    assert len(re.findall("/printjob/[^/]+/render", content)) > 5
    # links
    assert len(re.findall('/printjob/[^/]+/"', content)) > 5
    # title
    assert "crowdprinter" in content
    # nav
    assert "/login/" in content
    assert "/signup/" in content
    assert "/info" in content
    assert "/faq" in content


@pytest.mark.django_db
def test_index_authed(client_user, job_basic_x50):
    resp = client_user.get("/")
    assert resp.status_code == 200
    content = resp.content.decode()
    # title
    assert "/logout/" in content


@pytest.mark.django_db
def test_detail_noauth(client, job_basic):
    resp = client.get(f"/printjob/{job_basic.slug}/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert "need to be logged in" in content


@pytest.mark.django_db
def test_detail_can_take(client_user, job_basic):
    url = f"/printjob/{job_basic.slug}"
    resp = client_user.get(f"{url}/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert f"{url}/take" in content
    assert f"{url}/render" in content


@pytest.mark.django_db
def test_take(client_user, user, job_basic):
    assert PrintAttempt.objects.count() == 0
    resp = client_user.post(f"/printjob/{job_basic.slug}/take", follow=True)
    assert resp.status_code == 200
    assert resp.redirect_chain[0][0] == f"/printjob/{job_basic.slug}/"
    assert PrintAttempt.objects.count() == 1
    attempt = PrintAttempt.objects.first()
    assert attempt.user == user
    assert attempt.job == job_basic
    assert attempt.started
    assert attempt.ended is None
    assert attempt.finished is False
    assert attempt.dropped_off is False


@pytest.mark.django_db
def test_detail_taken(client_user, job_taken):
    url = f"/printjob/{job_taken.slug}"
    resp = client_user.get(f"{url}/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert f"{url}/take" not in content
    assert f"{url}/give_back" in content
    assert f"{url}/done" in content
    assert f"{url}/stl" in content


@pytest.mark.django_db
def test_give_back(client_user, user, job_taken):
    assert PrintAttempt.objects.count() == 1
    resp = client_user.post(f"/printjob/{job_taken.slug}/give_back", follow=True)
    assert resp.status_code == 200
    assert resp.redirect_chain[0][0] == f"/printjob/{job_taken.slug}/"
    assert PrintAttempt.objects.count() == 1
    attempt = PrintAttempt.objects.first()
    assert attempt.user == user
    assert attempt.job == job_taken
    assert attempt.started
    assert attempt.ended
    assert attempt.finished is False
    assert attempt.dropped_off is False


@pytest.mark.django_db
def test_done(client_user, user, job_taken):
    assert PrintAttempt.objects.count() == 1
    resp = client_user.post(f"/printjob/{job_taken.slug}/done", follow=True)
    assert resp.status_code == 200
    assert resp.redirect_chain[0][0] == f"/printjob/{job_taken.slug}/"
    assert PrintAttempt.objects.count() == 1
    attempt = PrintAttempt.objects.first()
    assert attempt.user == user
    assert attempt.job == job_taken
    assert attempt.started
    assert attempt.ended
    assert attempt.finished is True
    assert attempt.dropped_off is False


@pytest.mark.django_db
def test_give_back_not_taken(client_user, user, job_basic):
    resp = client_user.post(f"/printjob/{job_basic.slug}/give_back", follow=True)
    assert resp.status_code == 404


@pytest.mark.django_db
def test_stl(client_user, user, job_taken):
    assert PrintAttempt.objects.count() == 1
    resp = client_user.get(f"/printjob/{job_taken.slug}/stl")
    assert resp.status_code == 200
    content = b"".join(resp.streaming_content).decode()
    assert "stl_job_taken" in content
