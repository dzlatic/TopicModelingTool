import os
from flask import Flask, render_template, request, \
    redirect, jsonify, url_for, flash, send_from_directory
import functools
from sqlalchemy import asc, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, joinedload, exc as orm_exc

import psycopg2
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


from database_setup import Base, Model, Topic, Word, User, Inference, Distribution

app = Flask(__name__)

#  APPLICATION_PATH = "/var/www/CatalogApp/CatalogApp/"
APPLICATION_PATH = "./"

DB_SECREATS_PATH = APPLICATION_PATH + "db_secrets.json"
CLIENT_SECTRETS_PATH = APPLICATION_PATH + "client_secrets.json"


CLIENT_ID = json.loads(
    open(CLIENT_SECTRETS_PATH, 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

DB_USER = json.loads(
    open(DB_SECREATS_PATH, 'r').read())['database']['user']

DB_PASSWORD = json.loads(
    open(DB_SECREATS_PATH, 'r').read())['database']['password']

DB_NAME = json.loads(
    open(DB_SECREATS_PATH, 'r').read())['database']['name']

APPLICATION_NAME = "Catalog App"


engine = create_engine(
    'postgresql://' + DB_USER + ':' + DB_PASSWORD + '@localhost:5432/' + DB_NAME)


Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
db_session = DBSession()

"""
def login_required(f):
    @functools.wraps(f)
    def x(*args, **kwargs):
        if 'username' not in login_session:
            flash("Please sign in to perform desired operation.", "flash-warn")
            return redirect(location=url_for('show_catalog'),
                            code=302,
                            Response=None)
        return f(*args, **kwargs)
    return x


def check_session_status(f):
    @functools.wraps(f)
    def x(*args, **kwargs):
        try:
            session_code = login_session['session_code']
        except KeyError:
            login_session.clear()
            session_code = ''.join(
                random.choice(
                    string.ascii_uppercase + string.digits) for x in range(32))
            login_session['session_code'] = session_code
            flash("Welcome!", "flash-ok")
            print("New session has been initialized {}".format(login_session))
        return f(*args, **kwargs)
    return x
"""
def get_inference_distribution(inference, text):
    topic_distribution =[]
    model_id=inference.model_id
    model = db_session.query(Model).filter_by(id=model_id).one()
    topics = model.topics
    for topic in topics:
        print("appending: id:{}, distribution: 0.05 ".format(topic.id))
        topic_distribution.append({"id":topic.id, "distribution": 0.05})
    print("APPENDED: {}".format(topic_distribution))
    return topic_distribution

@app.route('/')
@app.route('/models')
#  @check_session_status
def get_models_json():
    models = db_session.query(Model)
    return jsonify(AvailableModels=[m.serialize for m in models])

@app.route('/model/<int:model_id>/')
def get_model_json(model_id):
    try:
        model = db_session.query(Model).filter_by(id=model_id).one()
        return jsonify(Model=[model.serialize_all])
    except orm_exc.NoResultFound:
        message = "Model with id:{} doesn't exist.".format(model_id)
        return jsonify(Error=message)

@app.route('/model/<int:model_id>/inference', methods=['POST'])
def post_model_inference(model_id):
    if request.headers['Content-Type'] == 'application/json':
        try:
            model = db_session.query(Model).filter_by(id=model_id).one()
            text = request.json["text"]
            inference = Inference(model_id=model.id, text=text)
            db_session.add(inference)
            topic_distribution = get_inference_distribution(inference, text)
            for topic in topic_distribution:
                print("Topic: {}".format(topic))
                distribution = Distribution(inference_id=inference.id, topic_id=topic['id'], distribution=topic['distribution'])
                db_session.add(distribution)
            db_session.commit()
            return jsonify(Inference=[inference.serialize_all])
        except orm_exc.NoResultFound:
            message = "Model with id:{} doesn't exist.".format(model_id)
            return jsonify(Error=message)
    else:
        message = "415 Unsupported Media Type"
        return jsonify(Error=message)

@app.route('/model/<int:model_id>/inferences')
def get_model_inferences(model_id):
    try:
        model = db_session.query(Model).filter_by(id=model_id).one()
        return jsonify(Inferences=[i.serialize_all for i in model.inferences])
    except orm_exc.NoResultFound:
        message = "Model with id:{} doesn't exist.".format(model_id)
        return jsonify(Error=message)

@app.route('/inference/<int:inference_id>')
def get_inference(inference_id):
    try:
        inference = db_session.query(Inference).filter_by(id=inference_id).one()
        return jsonify(Inference=inference.serialize_all)
    except orm_exc.NoResultFound:
        message = "Inference with id:{} doesn't exist.".format(inference_id)
        return jsonify(Error=message)

@app.route('/inference/<int:inference_id>/remove', methods=['DELETE'])
def delete_inference(inference_id):
    try:
        inference = db_session.query(Inference).filter_by(id=inference_id).one()
        db_session.delete(inference)
        db_session.commit()
        message = "Inference has been deleted."
        return jsonify(Success=message)
    except orm_exc.NoResultFound:
        message = "Inference with id:{} doesn't exist.".format(inference_id)
        return jsonify(Error=message)


@app.route('/topic/<int:topic_id>', methods=['GET','POST'])
def topic_json(topic_id):
    try:
        topic = db_session.query(Topic).filter_by(id=topic_id).one()
        if request.method == 'GET':
            return jsonify(Topic=[topic.serialize_all])
        elif request.method == 'POST':
            print ("request.method == POST")

            new_name = request.json["name"]
            print("name retrieved {}".format(new_name))
            topic.name = new_name
            try:
                db_session.add(topic)
                db_session.commit()
                return jsonify(Topic=[topic.serialize])
            except (IntegrityError,
                    orm_exc.NoResultFound,
                    AssertionError,
                    NameError) as e:
                return jsonify(Error=e)
        else:
            message = "415 Unsupported Request Type"
            return jsonify(Error=message)
    except orm_exc.NoResultFound:
        message = "Topic with id:{} doesn't exist.".format(topic_id)
        return jsonify(Error=message)



@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# Handle wrong URLs in a friendly way
@app.errorhandler(404)
# @check_session_status
def default_route(e):
    message = "Wrong URL."
    return jsonify(Error=message)


if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=8000)
