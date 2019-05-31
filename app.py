import json
import random
import string
import urllib.request
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_marshmallow import Marshmallow
from flask_sharded_sqlalchemy import ShardedSQLAlchemy as SQLAlchemy
from flask_sharded_sqlalchemy import BindKeyPattern
from osnk.http.auth import EmailAuthentication, TokenAuthentication
from osnk.validations import requires
from os import urandom
from pathlib import Path


def post(url, **kwargs):
    headers = {'User-Agent': 'Kyak/0.0.0'}
    if 'json' in kwargs:
        data = json.dumps(kwargs['json']).encode()
        headers['Content-Type'] = 'application/json'
    elif 'data' in kwargs:
        data = kwargs['data']
    else:
        data = None
    req = urllib.request.Request(url, data, headers, method='POST')
    urllib.request.urlopen(req)


def tree(keytree, value, dict_class=dict):
    try:
        k = next(keytree)
    except StopIteration:
        return value
    else:
        return dict_class({k: tree(keytree, value)})


def merge(a, b, dict_class=dict, inplace=False):
    if not inplace:
        a = a.copy()
    for k, v in b.items():
        if isinstance(v, dict):
            a[k] = merge(a.get(k, dict_class()), v, dict_class, inplace=True)
        else:
            a[k] = v
    return a


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def normalize(d, dict_class=dict):
    if isinstance(d, dict):
        if all(x.isdigit() for x in d.keys()):
            return [normalize(v, dict_class) for k, v in d.items()]
        else:
            return dict_class({k: normalize(v, dict_class)
                               for k, v in d.items()})
    return d


def load(f, dict_class=dict):
    loaded = dict_class()
    for line in f:
        s = line.split('#', 1)[0]
        if s:
            kv = s.split(' ', 1)
            if len(kv) == 2:
                k, v = [x.strip() for x in kv]
                t = tree(iter(k.split('.')), v, dict_class)
                merge(loaded, t, dict_class, inplace=True)
    return normalize(loaded, dict_class)


def config(path, dict_class=dict):
    with open(path) as f:
        return load(f, dict_class)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def rand16hex():
    return urandom(16).hex()


conf = config(Path.home() / '.kyak', dict_class=AttrDict)

binds = {}

for k, v in conf.databases.items():
    if isinstance(v, list):
        binds.update({':'.join([k, str(i)]): bind for i, bind in enumerate(v)})
    else:
        binds.update({k + ':0': v})

app = Flask(__name__)
app.config['SQLALCHEMY_BINDS'] = binds
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = app.debug

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Account(db.Model):
    __tablename__ = 'accounts'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
    id = db.Column(db.String(16), primary_key=True)
    type = db.Column(db.String(16), nullable=False, default='personal')
    name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=True)
    address = db.Column(db.String(), nullable=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])

class Access(db.Model):
    __tablename__ = 'accesses'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
    account_id = db.Column(db.String(16), primary_key=True)
    owner = db.Column(db.String(16), primary_key=True)
    access = db.Column(db.String(), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class Hook(db.Model):
    __tablename__ = 'hooks'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
    account_id = db.Column(db.String(16), primary_key=True)
    type = db.Column(db.String(16), primary_key=True)
    url = db.Column(db.String(), unique=True, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class Offer(db.Model):
    __tablename__ = 'offers'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
    account_id = db.Column(db.String(16), primary_key=True)
    offeror = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class Contract(db.Model):
    __tablename__ = 'contracts'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
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

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class Term(db.Model):
    __tablename__ = 'terms'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
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

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class TimeAndMaterialsPrice(db.Model):
    __tablename__ = 'time_and_materials_prices'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
    account_id = db.Column(db.String(16), primary_key=True)
    contractor = db.Column(db.String(16), primary_key=True)
    contractee = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    cc = db.Column(db.String(32), primary_key=True, default=rand16hex)
    until = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class TimeAndMaterialsActivity(db.Model):
    __tablename__ = 'time_and_materials_activities'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
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

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class Payment(db.Model):
    __tablename__ = 'payments'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
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

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class ContractTemplates(db.Model):
    __tablename__ = 'contract_templates'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
    account_id = db.Column(db.String(16), primary_key=True)
    contractor = db.Column(db.String(16), primary_key=True)
    contractee = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    cc = db.Column(db.String(32), primary_key=True, default=rand16hex)
    title = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class TermTemplates(db.Model):
    __tablename__ = 'term_templates'
    __bind_key__ = BindKeyPattern(r'accounts:\d+')
    account_id = db.Column(db.String(16), primary_key=True)
    contractor = db.Column(db.String(16), primary_key=True)
    contractee = db.Column(db.String(16), primary_key=True)
    c = db.Column(db.String(32), primary_key=True, default=rand16hex)
    cc = db.Column(db.String(32), primary_key=True, default=rand16hex)
    title = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class Alias(db.Model):
    __tablename__ = 'aliases'
    __bind_key__ = BindKeyPattern(r'aliases:\d+')
    id = db.Column(db.String(16), primary_key=True)
    account_id = db.Column(db.String(16), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)

    @classmethod
    def __hash_id__(cls, ident):
        return ord(ident[0][0])


class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account


def get_system_contracts(*, contractors=None, when=datetime.now()):
    return None


@app.before_first_request
def init():
    db.create_all()


@app.route('/')
def index():
    return Path('index.html').read_text().replace('{{ title }}', conf.title)


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
    return jsonify('Unauthorized'), 401, {header: scheme}


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
        hook = Hook.query.filter_by(account_id=aid, type='auth').first()
        payload = {'account': hook.account_id}
        url = hook.url
    s = string.ascii_uppercase + string.digits
    password = ''.join(random.choices(s, k=8))
    encoded = json.dumps(payload).encode()
    hint = auth.hint([(aid_or_hook, password)], expires, encoded)
    post(url, json={'text': password})
    return jsonify(hint)


@app.route('/token', methods=['GET'])
@requires(auth)
def get_token():
    expires = datetime.now() + timedelta(hours=1)
    payload = json.loads(auth.payload)
    if hook_token_confirm(payload):
        t, token = 'hook', hook_token
    else:
        t, token = 'account', account_token
    return jsonify(type=t, value=token.build(expires, payload))


@app.route('/accounts', methods=['POST'])
@requires(hook_token | account_token)
def post_accounts(passed):
    aid = request.form['id']
    if aid == 'me':
        return jsonify('Bad Request', 400)
    account = Account()
    account.id = aid
    account.name = request.form['name']
    if hook_token in passed:
        hook = Hook()
        hook.account_id = account.id
        hook.type = 'auth'
        hook.url = hook_token.payload['hook']
        db.session.add(hook)
    else:
        account.type = 'corporate'
        access = Access()
        access.account_id = account.id
        access.owner = account_token.payload['account']
        access.access = 'Allow full access'
        db.session.add(access)
    account.email = request.form.get('email')
    account.address = request.form.get('address')
    db.session.add(account)
    db.session.commit()
    return jsonify(AccountSchema().dump(account).data)


@app.route('/accounts/<aid>')
@requires(account_token)
def get_accounts(aid):
    if aid == 'me':
        account = Account.query.get(account_token.payload['account'])
    else:
        account = Account.query.get(aid)
    return jsonify(AccountSchema().dump(account).data)


@app.route('/accounts/<aid>', methods=['DELETE'])
@requires(account_token)
def delete_accounts(aid):
    if aid != account_token.payload['account']:
        return jsonify('Forbidden'), 403
    account = Account.query.get(aid)
    db.session.delete(account)
    db.session.commit()
    return jsonify(AccountSchema().dump(account).data)
