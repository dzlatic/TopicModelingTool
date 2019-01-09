import re
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy import create_engine
import json
import psycopg2


Base = declarative_base()

APPLICATION_PATH = "/var/www/CatalogApp/CatalogApp/"
# APPLICATION_PATH = "./"

DB_SECREATS_PATH = APPLICATION_PATH + "db_secrets.json"

DB_USER = json.loads(
    open(DB_SECREATS_PATH, 'r').read())['database']['user']

DB_PASSWORD = json.loads(
    open(DB_SECREATS_PATH, 'r').read())['database']['password']

DB_NAME = json.loads(
    open(DB_SECREATS_PATH, 'r').read())['database']['name']

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'email': self.email
        }

    @validates('name')
    def validate_username(self, key, name):
        if not name:
            raise AssertionError('No username provided')
        if len(name) < 1 or len(name) > 20:
            raise AssertionError('Username must be '
                                 'between 5 and 40 characters')

        return name

    @validates('email')
    def validate_email(self, key, email):
        if not email:
            raise AssertionError('No email provided')
        if not re.match("[^@]+@[^@]+\.[^@]+", email):
            raise AssertionError('Provided email is not an email address')
        if len(email) < 5 or len(email) > 254:
            raise AssertionError('Username must be '
                                 'between 5 and 254 characters')
        return email


class Model(Base):
    __tablename__ = 'model'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), unique=True, nullable=False)
    topics = relationship("Topic")
    inferences = relationship("Inference")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,'name': self.name}

    @property
    def serialize_all(self):
        """Return object data in easily serializeable format"""
        if not self.topics:
            return {
                'id': self.id,
                'name': self.name}
        else:
            return {
                'id': self.id,
                'name': self.name,
                'Topics': [t.serialize for t in self.topics]}


    @validates('name')
    def validate_model_name(self, key, name):
        if not name:
            raise AssertionError('No model name provided')
        if len(name) < 1 or len(name) > 40:
            raise AssertionError('Model name must be between'
                                 ' 1 and 40 characters')
        return name


class Topic(Base):
    __tablename__ = 'topic'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), unique=True, nullable=False)
    action = Column(String(40), nullable=True)
    model_id = Column(Integer, ForeignKey('model.id'),nullable=False)
    model = relationship("Model", back_populates='topics')
    #back_populates = 'topics'
    words = relationship("Word")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'action': self.action
        }

    @property
    def serialize_all(self):
        """Return object data in easily serializeable format"""
        if not self.words:
            return {
                'id': self.id,
                'name': self.name,
                'action': self.action
            }
        else:
            return {
                'id': self.id,
                'name': self.name,
                'action': self.action,
                'Words': [w.serialize for w in self.words]
            }

    @validates('name')
    def validate_topic_name(self, key, name):
        if not name:
            raise AssertionError('No topic name provided')
        if len(name) < 1 or len(name) > 40:
            raise AssertionError('Topic name must be between'
                                 ' 1 and 40 characters')
        return name


class Word(Base):
    __tablename__ = 'word'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    distribution = Column(Float, nullable=False)
    topic_id = Column(Integer, ForeignKey('topic.id'),nullable=False)
    topic = relationship("Topic", back_populates='words')
    #back_populates = 'words'

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
	        'dist': self.distribution
        }

    @validates('name')
    def validate_word_name(self, key, name):
        if not name:
            raise AssertionError('No word name provided')
        if len(name) < 1 or len(name) > 40:
            raise AssertionError('Word name must be between'
                                 ' 1 and 40 characters')
        return name


class Inference(Base):
    __tablename__ = 'inference'

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    model_id = Column(Integer, ForeignKey('model.id'),nullable=False)
    model = relationship("Model", back_populates='inferences')
    # back_populates = 'inferences'
    distribution = relationship("Distribution", cascade="all, delete-orphan")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'text': self.text
        }

    @property
    def serialize_all(self):
        """Return object data in easily serializeable format"""
        if not self.distribution:
            return {
                'id': self.id,
                'text': self.text
            }
        else:
            return {
                'id': self.id,
	            'text': self.text,
                'Distribution': [d.serialize for d in self.distribution]}

class Distribution(Base):
    __tablename__ = 'distribution'

    distribution = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    inference_id = Column(Integer, ForeignKey('inference.id'),primary_key=True)
    topic_id = Column(Integer, ForeignKey('topic.id'),primary_key=True)
    topic_name = Column(String(40), nullable=False)
    topic_action = Column(String(40), nullable=True)
    inference = relationship("Inference", back_populates='distribution')
    #back_populates = 'inferences'

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'rank': self.rank,
            'topic_id': self.topic_id,
            'topic_name:': self.topic_name,
            'topic_action': self.topic_action,
            'distribution': self.distribution
        }

print ("DB_USER={}, DB_PASSWORD={}, DB_NAME={}".format(DB_USER,DB_PASSWORD,DB_NAME ))
engine = create_engine(
    'postgresql://' + DB_USER + ':' + DB_PASSWORD + '@localhost:5432/' + DB_NAME)

Base.metadata.create_all(engine)
