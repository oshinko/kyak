import config
from datetime import datetime
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from osnk.httpauth import EmailAuthentication, TokenAuthentication
from osnk.validations import requires
from os import urandom
from pathlib import Path

def rand16hex():
    return urandom(16).hex()


conf = config.read(Path.home() / '.kyak')

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
    url = db.Column(db.String(), nullable=False)
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


@app.route('/accounts', methods=['POST'])
def post_accounts():
    account = Account()
    account.id = request.form['id']
    account.name = request.form['name']
    account.type = request.form['type']
    account.parent = request.form.get('parent')
    account.email = request.form.get('email')
    account.address = request.form.get('address')
    db.session.add(account)

    if account.type == 'corporate':
        admin = request.form['admin']
        if Account.query.get(admin):
            access = Access()
            access.account_id = account.id
            access.owner = admin
            access.access = 'Allow full access'
            db.session.add(access)
        else:
            db.rollback()
            return jsonify('Bad Request'), 400
    else:
        hook = Hook()
        hook.account_id = account.id
        hook.type = 'auth'
        hook.url = request.form['hook']
        db.session.add(hook)

    db.session.commit()
    return jsonify(AccountSchema().dump(account).data)


secret = b'Your secret words'
otp_auth = EmailAuthentication(secret, scheme='OTP')
token_auth = TokenAuthentication(secret)


@app.route('/auth', methods=['POST'])
def post_auth():
    expires = datetime.now() + timedelta(hours=1)
    aid = request.form['account']
    account = Account.get(aid)
    if not account:
        return jsonify('Not Found'), 404
    credentials = [(aid, password())]
    hint = otp_auth.hint(credentials, expires)
    posthook(credentials)
    return jsonify(hint)


@app.route('/token', methods=['GET'])
@requires(otp_auth)
def get_token():
    expires = datetime.now() + timedelta(hours=1)
    return jsonify(token_auth.build(expires, otp_auth.payload))


@app.route('/accounts/<aid>')
@requires(token_auth)
def get_accounts(aid):
    account = Account.query.get(aid)
    if account:
        return jsonify(AccountSchema().dump(account).data)
    return jsonify('Not Found'), 404


@app.route('/accounts/<aid>', methods=['DELETE'])
def delete_accounts(aid):
    account = Account.query.get(aid)
    if account:
        db.session.delete(account)
        db.session.commit()
        return jsonify(AccountSchema().dump(account).data)
    return jsonify('Not Found'), 404


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
