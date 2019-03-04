# Kyak

![Python 3](https://img.shields.io/badge/python-3-blue.svg)

This is a simple application for business contract.


## Installing modules

```bash
python3 -m venv $HOME/.venv/kyak
$HOME/.venv/kyak/bin/python -m pip install -U pip -r requirements.txt
```


## Setting configuration file

```bash
cp example.kyak $HOME/.kyak
```


## Initializing database

```bash
$HOME/.venv/kyak/bin/python -c "from app import db; db.create_all()"
```


## Running server

```bash
FLASK_APP=app.py $HOME/.venv/kyak/bin/flask run
```

in debug mode.

```bash
FLASK_APP=app.py FLASK_DEBUG=1 $HOME/.venv/kyak/bin/flask run
```


## Using APIs

Post new personal account.

```bash
curl -v -d id=corp.kyak.employee1 \
        -d name=Employee1 \
        -d type=personal \
        -d hook=https://discordapp.com/api/webhooks/$DISCORD_WEBHOOK_ID/$DISCORD_WEBHOOK_TOKEN \
        http://localhost:5000/accounts
```

Post new corporate account.

```bash
curl -v -d id=corp.kyak \
        -d name=Kyak+Inc. \
        -d type=corporate \
        -d admin=corp.kyak.employee1 \
        http://localhost:5000/accounts
```
