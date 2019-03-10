import json
import requests
import random
import string
from datetime import datetime, timedelta
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from osnk.http.auth import EmailAuthentication, TokenAuthentication
from osnk.validations import requires
from os import urandom
from pathlib import Path


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def config(path):
    r = AttrDict()
    with open(path) as f:
        for line in f:
            s = line.split('#', 1)[0]
            if s:
                kv = s.split(' ', 1)
                if len(kv) == 2:
                    k, v = [x.strip() for x in kv]
                    r[k] = v
    return r


def rand16hex():
    return urandom(16).hex()


conf = config(Path.home() / '.kyak')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = conf.database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.String(16), primary_key=True)
    type = db.Column(db.String(16), nullable=False, default='personal')
    name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=True)
    address = db.Column(db.String(), nullable=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class Access(db.Model):
    __tablename__ = 'accesses'
    account_id = db.Column(db.String(16), primary_key=True)
    owner = db.Column(db.String(16), primary_key=True)
    access = db.Column(db.String(), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class Hook(db.Model):
    __tablename__ = 'hooks'
    account_id = db.Column(db.String(16), primary_key=True)
    type = db.Column(db.String(16), primary_key=True)
    url = db.Column(db.String(), unique=True, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class Offer(db.Model):
    __tablename__ = 'offers'
    account_id = db.Column(db.String(16), primary_key=True)
    offeror = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class Contract(db.Model):
    __tablename__ = 'contracts'
    account_id = db.Column(db.String(16), primary_key=True)
    contractor = db.Column(db.String(16), primary_key=True)
    contractee = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    type = db.Column(db.String(16), nullable=False)
    since = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    until = db.Column(db.DateTime, nullable=True)
    payment_terms = db.Column(db.String(), nullable=True)
    deposit = db.Column(db.Integer, nullable=True)
    contractor_signed = db.Column(db.DateTime, nullable=True)
    contractee_signed = db.Column(db.DateTime, nullable=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class Term(db.Model):
    __tablename__ = 'terms'
    account_id = db.Column(db.String(16), primary_key=True)
    contractor = db.Column(db.String(16), primary_key=True)
    contractee = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    cc = db.Column(db.String(32), primary_key=True, default=rand16hex)
    order = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class TimeAndMaterialsPrice(db.Model):
    __tablename__ = 'time_and_materials_prices'
    account_id = db.Column(db.String(16), primary_key=True)
    contractor = db.Column(db.String(16), primary_key=True)
    contractee = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    cc = db.Column(db.String(32), primary_key=True, default=rand16hex)
    until = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class TimeAndMaterialsActivity(db.Model):
    __tablename__ = 'time_and_materials_activities'
    account_id = db.Column(db.String(16), primary_key=True)
    contractor = db.Column(db.String(16), primary_key=True)
    contractee = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    cc = db.Column(db.String(32), primary_key=True, default=rand16hex)
    day = db.Column(db.Integer, nullable=False)
    since = db.Column(db.DateTime, nullable=True)
    until = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.String(), nullable=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class Payment(db.Model):
    __tablename__ = 'payments'
    account_id = db.Column(db.String(16), primary_key=True)
    contractor = db.Column(db.String(16), primary_key=True)
    contractee = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    amount = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, nullable=False)
    requested = db.Column(db.DateTime, nullable=True)
    paid = db.Column(db.DateTime, nullable=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class ContractTemplates(db.Model):
    __tablename__ = 'contract_templates'
    account_id = db.Column(db.String(16), primary_key=True)
    contractor = db.Column(db.String(16), primary_key=True)
    contractee = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    cc = db.Column(db.String(32), primary_key=True, default=rand16hex)
    title = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class TermTemplates(db.Model):
    __tablename__ = 'term_templates'
    account_id = db.Column(db.String(16), primary_key=True)
    contractor = db.Column(db.String(16), primary_key=True)
    contractee = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    cc = db.Column(db.String(32), primary_key=True, default=rand16hex)
    title = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account


def get_system_contracts(*, contractors=None, when=datetime.now()):
    return None


@app.route('/')
def index():
    accounts = Account.query.all()
    return render_template('index.html', accounts=accounts)

secret = conf.secret.encode()
auth = EmailAuthentication(secret, scheme='Hook')
hook_token = TokenAuthentication(secret)
account_token = TokenAuthentication(secret)


@auth.authorization
@hook_token.authorization
@account_token.authorization
def authorization(header):
    return request.headers.get(header)


@auth.authenticate
@hook_token.authenticate
@account_token.authenticate
def authenticate(header, scheme):
    return jsonify(error='Unauthorized'), 401, {header: scheme}


@hook_token.payload_from_bytes
@account_token.payload_from_bytes
def token_payload_from_bytes(b):
    return json.loads(b.decode())


@hook_token.payload_to_bytes
@account_token.payload_to_bytes
def token_payload_to_bytes(payload):
    return json.dumps(payload).encode()


@hook_token.confirm
def hook_token_confirm(payload):
    return 'hook' in payload


@account_token.confirm
def account_token_confirm(payload):
    return 'account' in payload


@app.route('/auth', methods=['POST'])
def post_auth():
    expires = datetime.now() + timedelta(hours=1)
    aid_or_hook = request.form['id']
    if aid_or_hook.startswith('http'):
        url = aid_or_hook
        hook = Hook.query.filter_by(url=url).first()
        if hook:
            payload = {'account': hook.account_id}
        else:
            payload = {'hook': url}
    else:
        aid = aid_or_hook
        hook = Hook.query.filter_by(account_id=aid, type='auth').first_or_404()
        payload = {'account': hook.account_id}
        url = hook.url
    s = string.ascii_uppercase + string.digits
    password = ''.join(random.choices(s, k=8))
    encoded = json.dumps(payload).encode()
    hint = auth.hint([(aid_or_hook, password)], expires, encoded)
    requests.post(url, json={'text': password})
    return jsonify(hint)


@app.route('/token', methods=['GET'])
@requires(auth)
def get_token():
    expires = datetime.now() + timedelta(hours=1)
    payload = json.loads(auth.payload)
    token = hook_token if hook_token_confirm(payload) else account_token
    return jsonify(token.build(expires, payload))


@app.route('/personal/accounts', methods=['POST'])
@requires(hook_token)
def post_personal_accounts():
    account = Account()
    account.id = request.form['id']
    account.name = request.form['name']
    account.email = request.form.get('email')
    account.address = request.form.get('address')
    db.session.add(account)

    hook = Hook()
    hook.account_id = account.id
    hook.type = 'auth'
    hook.url = hook_token.payload['hook']
    db.session.add(hook)

    db.session.commit()

    return jsonify(AccountSchema().dump(account).data)


@app.route('/corporate/accounts', methods=['POST'])
@requires(account_token)
def post_corporate_accounts():
    account = Account()
    account.id = request.form['id']
    account.name = request.form['name']
    account.type = 'corporate'
    account.email = request.form.get('email')
    account.address = request.form.get('address')
    db.session.add(account)

    access = Access()
    access.account_id = account.id
    access.owner = account_token.payload['account']
    access.access = 'Allow full access'
    db.session.add(access)

    db.session.commit()

    return jsonify(AccountSchema().dump(account).data)


@app.route('/accounts/<aid>')
@requires(account_token)
def get_accounts(aid):
    account = Account.query.get_or_404(aid)
    return jsonify(AccountSchema().dump(account).data)


@app.route('/accounts/<aid>', methods=['DELETE'])
@requires(account_token)
def delete_accounts(aid):
    account = Account.query.get_or_404(aid)
    db.session.delete(account)
    db.session.commit()
    return jsonify(AccountSchema().dump(account).data)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('usage:', sys.argv[0], 'show create tables', file=sys.stderr)
        exit(1)

    import inspect
    import sqlalchemy.schema

    for _, obj in dict(globals()).items():
        if inspect.isclass(obj) and hasattr(obj, '__table__'):
            print(sqlalchemy.schema.CreateTable(obj.__table__))
