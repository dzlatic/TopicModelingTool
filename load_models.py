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

def add_model(name, number_of_topics):
    file_name="./models/" + name
    lda_model = models.LdaModel.load(file_name)
    try:
        new_model = Model(name=name, number_of_topics=number_of_topics )
        db_session.add(new_model)
        db_session.commit()
        print("Model {}  with {} topics added successfully.".format(name, number_of_topics))
        #model_new = db_session.query(Model).filter_by(name=model_name).one()
        add_model_topics(new_model, lda_model.show_topics(formatted=False))
    except (exc.IntegrityError, AssertionError,
            AttributeError, NameError) as e:
        db_session.rollback()
        print("Model error: {}".format(e))

def add_model_topics(model, topics_def):
    for topic_number, words in topics_def:
        try:
            new_topic = Topic(number=topic_number, model_id=model.id)
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

add_model("NLTK_BROWN", 10)