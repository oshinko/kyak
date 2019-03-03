import config
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
    type = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=True)
    address = db.Column(db.String(), nullable=True)


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
