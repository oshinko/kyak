import config
import datetime
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path

conf = config.read(Path.home() / '.kyak')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = conf.database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.String(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    type = db.Column(db.String(), nullable=False, default='personal')
    email = db.Column(db.String(), nullable=True)
    address = db.Column(db.String(), nullable=True)
    created = db.Column(db.DateTime, nullable=False,
                        default=datetime.datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class Access(db.Model):
    __tablename__ = 'accesses'
    account_id = db.Column(db.String(), primary_key=True)
    owner = db.Column(db.String(), primary_key=True)
    access = db.Column(db.String(), nullable=False)
    created = db.Column(db.DateTime, nullable=False,
                        default=datetime.datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class Hook(db.Model):
    __tablename__ = 'hooks'
    account_id = db.Column(db.String(), primary_key=True)
    type = db.Column(db.String(), primary_key=True, nullable=False)
    url = db.Column(db.String(), nullable=False)
    created = db.Column(db.DateTime, nullable=False,
                        default=datetime.datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True)


class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account


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


@app.route('/accounts/<aid>')
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
    import sqlalchemy.schema
    import sys

    if len(sys.argv) < 2:
        print('usage:', sys.argv[0], 'show create tables', file=sys.stderr)
        exit(1)

    for model in (Account,):
            print(sqlalchemy.schema.CreateTable(model.__table__))
