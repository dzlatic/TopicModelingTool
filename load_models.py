from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from database_setup import Model, ModelTopic, TopicWord, Base
import psycopg2
import json

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

# IMPORTANT: YOUR CATEGORY CANNOT BE NAMED 'JSON'!
# This is a reserved route for JSON database export.
# Add Categories.this also includes some test cases for various errors
model_topic_word = [("Model1", [
                        ("business",["growth", "stock", "expense"]),
                        ("sales",["finance", "revenue", "competition"]),
                        ("complain",["problem", "issue", "frustration"])]
                    )]

def add_model(model_def):
    for model_name, topics in model_def:
        try:
            new_model = Model(name=model_name)
            db_session.add(new_model)
            db_session.commit()
            print("Model {} added successfully.".format(model_name))
            model_new = db_session.query(Model).filter_by(name="Model1").one()
            add_model_topics(model_new, topics)
        except (exc.IntegrityError, AssertionError,
                AttributeError, NameError) as e:
            db_session.rollback()
            print("Model error: {}".format(e))

def add_model_topics(model, topics_def):
    for topic_name, words in topics_def:
        try:
            new_topic = ModelTopic(name=topic_name, model=model)
            db_session.add(new_topic)
            db_session.commit()
            print("Topic {} added successfully for model.".format(topic_name, model.name))
            topic_new = db_session.query(ModelTopic).filter_by(name=topic_name, model_id=model.id).one()
            add_topic_words(topic_new, words)
        except (exc.IntegrityError, AssertionError,
                AttributeError, NameError) as e:
            db_session.rollback()
            print("Topic error: {}".format(e))

def add_topic_words(topic, words):
    for word in words:
        try:
            new_word = TopicWord(name=word, topic_id=topic.id)
            db_session.add(new_word)
            db_session.commit()
            print("Topic {} added successfully for topic.".format(word, topic.name))
        except (exc.IntegrityError, AssertionError,
                AttributeError, NameError) as e:
            db_session.rollback()
            print("Topic error: {}".format(e))

add_model(model_topic_word)