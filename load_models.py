import sys
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from database_setup import Model, Topic, Word, Base
import psycopg2
import json
import nltk
import re
from gensim import models, corpora
from nltk import word_tokenize
from nltk.corpus import stopwords
from decimal import Decimal


DB_USER = json.loads(
    open('db_secrets.json', 'r').read())['database']['user']

DB_PASSWORD = json.loads(
    open('db_secrets.json', 'r').read())['database']['password']

DB_NAME = json.loads(
    open('db_secrets.json', 'r').read())['database']['name']

engine = create_engine(
    'postgresql://' + DB_USER + ':' + DB_PASSWORD + '@localhost:5432/' + DB_NAME)  # echo=True

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

db_session = DBSession()

def add_model(name):

    model_file_name = "./models/" + name
    json_file_name = "./models/" + name + ".json"
    print(json_file_name)

    model_type = json.loads(
        open(json_file_name, 'r').read())['model_type']
    print(model_type)
    coherence_score = json.loads(
        open(json_file_name, 'r').read(), parse_float=Decimal)['coherence_score']



    number_of_topics = json.loads(
        open(json_file_name, 'r').read(), parse_int=Decimal)['number_of_topics']



    if model_type=='LDA':
        model = models.LdaModel.load(model_file_name)
    elif model_type=='LSI':
        model = models.LsiModel.load(model_file_name)

    try:
        new_model = Model(name=name, number_of_topics=number_of_topics, coherence_score=coherence_score )
        db_session.add(new_model)
        db_session.commit()
        print("Model {}  with {} topics added successfully.".format(name, number_of_topics))
        #model_new = db_session.query(Model).filter_by(name=model_name).one()
        add_model_topics(new_model, model.show_topics(formatted=False))
    except (exc.IntegrityError, AssertionError,
            AttributeError, NameError) as e:
        db_session.rollback()
        print("Model error: {}".format(e))

def add_model_topics(model, topics_def):
    for topic_number, words in topics_def:
        try:
            new_topic = Topic(number=topic_number + 1, model_id=model.id) # + 1 for harmonizing with pyLDAviz
            db_session.add(new_topic)
            db_session.commit()
            print("Topic {} added successfully for model {}.".format(str(topic_number), model.name))
            add_topic_words(model, new_topic, words)
        except (exc.IntegrityError, AssertionError,
                AttributeError, NameError) as e:
            db_session.rollback()
            print("Topic error: {}".format(e))

def add_topic_words(model, topic, words):
    for word, dist in words:
        try:
            new_word = Word(model_id=model.id, topic_number=topic.number, name=word, distribution=dist.astype(float))
            db_session.add(new_word)
            db_session.commit()
            print("Word {} added successfully for topic {}.".format(word, topic.number))
        except (exc.IntegrityError, AssertionError,
                AttributeError, NameError) as e:
            db_session.rollback()
            print("Word error: {}".format(e))


add_model(sys.argv[1])
#print('Number of arguments:', len(sys.argv), 'arguments.')
#print('Argument List:', str(sys.argv))