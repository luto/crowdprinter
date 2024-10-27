# crowdprinter

![](screenshot.png)

1. have 100s of STLs to be printed
2. have 20s of people with printers
3. people log into crowdprinter
4. people download 1-3 STLs
5. people report success

Note: most of this code is pretty ugly and has been writted in a couple of days. it's more of a throw-away project ;)

## Setup

```
virtualenv env --python python3.6
pip install -r src/requirements.txt
cd src
./manage.py migrate
./manage.py createsuperuser
./manage.py runserver
```

visit http://127.0.0.1:8000/ :)
