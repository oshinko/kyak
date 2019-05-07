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
$HOME/.venv/kyak/bin/python -c "from app import db; db.drop_all(); db.create_all()"
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

The authentication password is sent to Slack compatible Webhook.

If you use Discord.

```bash
DISCORD_WEBHOOK_ID=Your-Discord-Webhook-ID
DISCORD_WEBHOOK_TOKEN=Your-Discord-Webhook-Token
HOOK=https://discordapp.com/api/webhooks/$DISCORD_WEBHOOK_ID/$DISCORD_WEBHOOK_TOKEN/slack
```

Post your account.

```bash
HINT=`curl -d id=$HOOK http://localhost:5000/auth | sed -e 's/^"//' -e 's/"$//'`

RECEIVED_PASSWORD=Your-Received-Password

ADDR=`echo -n $HOOK | base64`
PASS=`echo -n $RECEIVED_PASSWORD | base64`

TOKEN=`curl -H "Authorization: Hook $ADDR $PASS $HINT" \
            http://localhost:5000/token |
       grep -o '"value": "[^"]*' |
       grep -o '[^"]*$'`

ACCOUNT=corp.kyak.employee1

curl -H "Authorization: Bearer $TOKEN" \
     -d id=$ACCOUNT \
     -d name=Employee1 \
     http://localhost:5000/accounts
```

Sign in to your account.

```bash
HINT=`curl -d id=$ACCOUNT http://localhost:5000/auth | sed -e 's/^"//' -e 's/"$//'`

RECEIVED_PASSWORD=Your-Received-Password

ADDR=`echo -n $ACCOUNT | base64`
PASS=`echo -n $RECEIVED_PASSWORD | base64`

TOKEN=`curl -H "Authorization: Hook $ADDR $PASS $HINT" \
            http://localhost:5000/token |
       grep -o '"value": "[^"]*' |
       grep -o '[^"]*$'`

curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/accounts/$ACCOUNT
```

## Deploying on Amazon Linux 2

AWS key pair is below.

`KEYPAIR=$HOME/.ssh/kyak.pem`

EC2 instance is below.

`HOST=your-instance`

App secret is below.

`SECRET=Your-Secret-Text`

Run this command in a shell prompt.

```bash
curl -fsSL https://raw.githubusercontent.com/oshinko/kyak/draft/deploy-on-amazon-linux-2.sh | sed -e "s/\$1/$SECRET/" | ssh -i $KEYPAIR ec2-user@$HOST
```
