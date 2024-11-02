# crowdprinter

![](screenshot.png)

A tool to crowdsource a big 3D print by splitting it into hundreds, or thousands
of parts. The parts will then be distributed amount of a number of people. They
can fetch a part of the site, print it and report back. At some point all parts
will be collected, e.g. during an event or via post. The big 3D print can then
be assembled.

## Development Setup

```bash
virtualenv env --python python3
pip install -r src/requirements.txt -r src/requirements.dev.txt
pre-commit install --install-hooks
cd src
./manage.py migrate
./manage.py createsuperuser
./manage.py runserver
```

visit http://127.0.0.1:8000/ :)

## Production Setup

```bash
git clone https://github.com/luto/crowdprinter.git
cd crowdprinter/src
# create a user, or virtualenv, or anything else to isolate the deps
pip install -r requirements.txt
pip install gunicorn
# apply database schema
python3 manage.py migrate
# find frontend assets
python3 manage.py collectstatic --no-input
```

Then setup your favorite daemon tool (systemd, supervisord, docker, whatever)
to run `gunicorn crowdprinter.wsgi --chdir /path/to/crowdprinter/src/ --address 0.0.0.0`.
