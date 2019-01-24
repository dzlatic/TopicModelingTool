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

import re

import numpy as np

#import pandas as pd



# Gensim

import gensim

import gensim.corpora as corpora

from gensim.utils import simple_preprocess

from gensim.models import CoherenceModel

# spacy for lemmatization

import spacy

# Plotting tools

import pyLDAvis

import pyLDAvis.gensim  # don't skip this

#import matplotlib.pyplot as plt

# Enable logging for gensim - optional

import logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.ERROR)

from tqdm import tqdm

import collections as cl

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)




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



STOPWORDS = stopwords.words('english')
STOPWORDS.extend(['from', 'subject', 're', 'edu', 'use', 'go', 'get', 'not', 'be', 'know', 'good',
                  'do', 'think', 'would', 'see', 'pm', 'want', 'send', 'work', 'time', 'call', 's',
                  'day', 'week', 'let', 'may', 'come', 'look', 'well', 'take', 'back', 'phone',
                  'need', 'make', 'also'])


## Tokenize words and Clean-up text
def sent_to_words(sentences):
    for sentence in sentences:
        yield (gensim.utils.simple_preprocess(str(sentence), deacc=True))  # deacc=True removes punctuations

## Remove Stopwords, Make Bigrams and Lemmatize
# Define functions for stopwords, bigrams, trigrams and lemmatization


def get_inference_distribution (name, text):
    def clean_text(text):
        # helper functions
        def remove_stopwords(texts):
            return [[word for word in simple_preprocess(str(doc)) if word not in STOPWORDS] for doc in texts]

        def make_bigrams(texts):
            model_file_name = APPLICATION_PATH + "models/" + name + ".bigram"
            bigram_mod = models.phrases.Phraser.load(model_file_name)
            return [bigram_mod[doc] for doc in texts]

        def make_trigrams(texts):
            model_file_name = APPLICATION_PATH + "models/" + name + ".trigram"
            trigram_mod = models.phrases.Phraser.load(model_file_name)
            return [trigram_mod[doc] for doc in texts]

        def lemmatization(texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
            """https://spacy.io/api/annotation"""
            texts_out = []
            for sent in texts:
                doc = nlp(" ".join(sent))
                texts_out.append([token.lemma_ for token in doc if token.pos_ in allowed_postags])
            return texts_out

        # Convert to list
        data = [text]
        # Remove Emails
        # data = [re.sub('\S*@\S*\s?', '', sent) for sent in data]
        # Remove new line characters
        data = [re.sub('\s+', ' ', sent) for sent in data]
        # Remove distracting single quotes
        data = [re.sub("\'", "", sent) for sent in data]
        ## Tokenize words and Clean-up text
        data_words = list(sent_to_words(data))
        # Form Bigrams
        data_words_bigrams = make_bigrams(data_words)
        # Form Trigrams
        data_words_trigrams = make_trigrams(data_words_bigrams)
        # Do lemmatization keeping only noun, adj, vb, adv
        nlp = spacy.load('en', disable=['parser', 'ner'])
        data_lemmatized = lemmatization(data_words_trigrams, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])
        # Remove Stop Words
        data_words_final = remove_stopwords(data_lemmatized)
        return data_words_final

    model_file_name = APPLICATION_PATH + "models/" + name
    dict_file_name = APPLICATION_PATH + "models/" + name + ".id2word"
    lda_model = models.LdaModel.load(model_file_name)
    dictionary = corpora.Dictionary.load(dict_file_name)
    bow = dictionary.doc2bow(clean_text(text)[0])
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
    if request.headers['Content-Type'] == 'text/plain;charset=UTF-8':
        try:
            #db_session.autoflush = False
            model = db_session.query(Model).filter_by(id=model_id).one()
            try:
                text = request.get_data(as_text=True)
            except KeyError:
                #db_session.autoflush = True
                message = "Invalid request body format."
                return jsonify(Error=message)
            inference = Inference(model_id=model_id, text=text)
            db_session.add(inference)
            db_session.commit()
            topic_distribution = get_inference_distribution(model.name, text)
            for topic_number, dist in topic_distribution[0]:
                #db_session.autoflush = False
                topic = db_session.query(Topic).filter_by(model_id=model_id, number=topic_number + 1).one() # +1 to harmonize with lyLDAviz
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
        message = "'Content-Type' must be 'text/plain;charset=UTF-8'"
        return jsonify(Error=message)

@app.route('/model/<int:model_id>/inference_json', methods=['POST'])
def post_model_inference_json(model_id):
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
            for topic_number, dist in topic_distribution[0]:
                #db_session.autoflush = False
                topic = db_session.query(Topic).filter_by(model_id=model_id, number=topic_number + 1).one() # +1 to harmonize with lyLDAviz
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

@app.route('/model/<int:model_id>/topic/<int:topic_number>', methods=['GET', 'POST'])
def topic_json(model_id, topic_number):
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
        message = "Topic with id:{} doesn't exist.".format(topic_number)
        return jsonify(Error=message)


@app.route('/model/<int:model_id>/edit_topics', methods=['GET', 'POST'])
def edit_topics(model_id):
    try:
        model = db_session.query(Model).filter_by(id=model_id).one()
        #topics = db_session.query(Topic).filter_by(model_id=model_id).order_by(asc(Topic.number))
        if request.method == 'GET':
            return render_template('editTopics.html', model_name=model.name, model_id=model.id, topics=model.topics)
        elif request.method == 'POST':
            try:
                for topic in model.topics:
                    alias_ = 'alias'+str(topic.number)
                    if request.form[alias_]:
                        topic.alias = request.form[alias_]
                    action_ = 'action' + str(topic.number)
                    if request.form[action_]:
                        topic.action = request.form[action_]
                    db_session.add(topic)
                db_session.commit()
            except (IntegrityError,
                    orm_exc.NoResultFound,
                    AssertionError,
                    NameError) as e:
                db_session.rollback()
                flash("Error: {}".format(e), "flash-error")
                return render_template('editTopics.html', model_name=model.name, model_id=model.id, topics=model.topics)

            flash("Item successfully edited.", "flash-ok")
            return render_template('editTopics.html', model_name=model.name, model_id=model.id, topics=model.topics)

    except orm_exc.NoResultFound:
        flash("Model with id:{} doesn't exist.".format(model_id), "flash-error")
        return render_template('index.html')

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
