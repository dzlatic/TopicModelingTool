import os
from flask import Flask, render_template, request, \
    redirect, jsonify, url_for, flash, send_from_directory
import functools
from sqlalchemy import asc, desc, create_engine
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

import nltk
import re
from gensim import models, corpora
from nltk import word_tokenize
from nltk.corpus import stopwords
STOPWORDS = stopwords.words('english')


from database_setup import Base, Model, Topic, Word, Inference, Distribution

app = Flask(__name__)

APPLICATION_PATH = "/var/www/TopicModelingTool/TopicModelingTool/"
# APPLICATION_PATH = "./"

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

APPLICATION_NAME = "TopicModelingTool"


engine = create_engine(
    'postgresql://' + DB_USER + ':' + DB_PASSWORD + '@localhost:5432/' + DB_NAME)


Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
db_session = DBSession()

def clean_text(text):
	tokenized_text = word_tokenize(text.lower())
	cleaned_text = [t for t in tokenized_text if t not in STOPWORDS and re.match('[a-zA-Z\-][a-zA-Z\-]{2,}', t)]
	return cleaned_text

def get_inference_distribution (name, text):
    print("original text: {}".format(text))
    print("cleaned text: {}".format(clean_text(text)))
    file_name = APPLICATION_PATH + "models/" + name
    print("Reading file: {}".format(file_name))
    lda_model = models.LdaModel.load(file_name)
    dictionary = corpora.Dictionary([clean_text(text)])
    bow = dictionary.doc2bow(clean_text(text))
    return lda_model[bow]

@app.route('/')
def show_home():
    return render_template('index.html')

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
            #db_session.autoflush = False
            model = db_session.query(Model).filter_by(id=model_id).one()
            try:
                text = request.json["text"]
            except KeyError:
                #db_session.autoflush = True
                message = "Invalid request body format."
                return jsonify(Error=message)
            inference = Inference(model_id=model_id, text=text)
            db_session.add(inference)
            db_session.commit()
            topic_distribution = get_inference_distribution(model.name, text)
            for topic_number, dist in topic_distribution:
                #db_session.autoflush = False
                topic = db_session.query(Topic).filter_by(number=topic_number).one()
                distribution = Distribution(model_id=model_id, inference_id=inference.id, rank=0, topic_number=topic.number, topic_alias=topic.alias, topic_action=topic.action, distribution=dist.astype(float))
                #db_session.autoflush = True
                db_session.add(distribution)
                db_session.commit()
            distributions = db_session.query(Distribution).filter_by(inference_id=inference.id, model_id=model_id).order_by(desc(Distribution.distribution), asc(Distribution.topic_number))
            rank = 1
            for distribution in distributions:
                distribution.rank = rank
                db_session.add(distribution)
                rank += 1
            db_session.commit()
            #db_session.autoflush = True
            return jsonify(Inference=[inference.serialize_all])
        except orm_exc.NoResultFound:
            #db_session.autoflush = True
            message = "Model with id:{} doesn't exist.".format(model_id)
            return jsonify(Error=message)
    else:
        message = "'Content-Type' must be 'application/json'"
        return jsonify(Error=message)

@app.route('/model/<int:model_id>/inferences')
def get_model_inferences(model_id):
    try:
        model = db_session.query(Model).filter_by(id=model_id).one()
        return jsonify(Inferences=[i.serialize_all for i in model.inferences])
    except orm_exc.NoResultFound:
        message = "Model with id:{} doesn't exist.".format(model_id)
        return jsonify(Error=message)

@app.route('/model/<int:model_id>/inference/<int:inference_id>', methods=['GET','DELETE'])
def get_inference(model_id, inference_id):
    try:
        inference = db_session.query(Inference).filter_by(model_id=model_id, id=inference_id).one()
        if request.method == 'GET':
            return jsonify(Inference=inference.serialize_all)
        elif request.method == 'DELETE':
            db_session.delete(inference)
            db_session.commit()
            message = "Inference has been deleted."
            return jsonify(Success=message)
    except orm_exc.NoResultFound:
            message = "Inference with id:{} doesn't exist.".format(inference_id)
            return jsonify(Error=message)

@app.route('/model/<int:model_id>/topic/<int:topic_number>', methods=['GET','POST'])
def topic_json(model_id,topic_number):
    try:
        topic = db_session.query(Topic).filter_by(model_id=model_id, number=topic_number).one()
        if request.method == 'GET':
            return jsonify(Topic=[topic.serialize_all])
        elif request.method == 'POST':
            if request.headers['Content-Type'] == 'application/json':
                try:
                    new_alias = request.json["alias"]
                    topic.alias = new_alias
                    alias_provided = True
                except KeyError:
                    alias_provided = False
                try:
                    new_action = request.json["action"]
                    topic.action = new_action
                    action_provided = True
                except KeyError:
                    action_provided = False
                if alias_provided or action_provided:
                    db_session.add(topic)
                    db_session.commit()
                    return jsonify(Topic=[topic.serialize])
                else:
                    message = "Invalid request body format."
                    return jsonify(Error=message)
            else:
                message = "'Content-Type' must be 'application/json'"
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
    app.debug = False
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=80)
