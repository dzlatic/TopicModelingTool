import re
from sqlalchemy import Column, ForeignKey, Integer, String, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy import create_engine
import json
import psycopg2


Base = declarative_base()

DB_USER = json.loads(
    # open("/var/www/TopicModelingTool/db_secrets.json", 'r').read())['database']['user']
    open("./db_secrets.json", 'r').read())['database']['user']

DB_PASSWORD = json.loads(
    # open("/var/www/TopicModelingTool/db_secrets.json", 'r').read())['database']['password']
    open("./db_secrets.json", 'r').read())['database']['password']

DB_NAME = json.loads(
    # open("/var/www/TopicModelingTool/db_secrets.json", 'r').read())['database']['name']
    open("./db_secrets.json", 'r').read())['database']['name']

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    picture = Column(String(250))
    # user_items = relationship("CategoryItem")

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
    model_topics = relationship("ModelTopic")
    __table_args__ = (
        CheckConstraint(
            name.expression != "JSON",
            name='model_name_cannot_be_JSON'
        ),
        {})

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        if not self.model_topics:
            return {
                'id': self.id,
                'name': self.name}
        else:
            return {
                'id': self.id,
                'name': self.name,
                'Item': [i.serialize for i in self.model_topics]}

    @validates('name')
    def validate_model_name(self, key, name):
        if not name:
            raise AssertionError('No model name provided')
        if len(name) < 1 or len(name) > 40:
            raise AssertionError('Model name must be between'
                                 ' 1 and 40 characters')
        return name


class ModelTopic(Base):
    __tablename__ = 'model_topic'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    # description = Column(String(250), nullable=False)
    model_id = Column(Integer, ForeignKey('model.id'))
    model = relationship("Model", back_populates='model_topics')
    back_populates = 'topics'
    # user_id = Column(Integer, ForeignKey('user.id'))
    # user = relationship("User", back_populates='user_items')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'model_id': self.model_id,
            # 'description': self.description,
            'id': self.id,
            'name': self.name}

    @validates('name')
    def validate_topic_name(self, key, title):
        if not name:
            raise AssertionError('No topic name provided')
        if len(name) < 1 or len(name) > 40:
            raise AssertionError('Topic name must be between'
                                 ' 1 and 40 characters')
        return name

    # @validates('description')
    # def validate_item_description(self, key, description):
    #    if not description:
    #        raise AssertionError('No item description provided')
    #    if len(description) < 1 or len(description) > 250:
    #        raise AssertionError('Item description must be between'
    #                             ' 5 and 40 characters')
    #    return description


class TopicWord(Base):
    __tablename__ = 'topic_word'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    # description = Column(String(250), nullable=False)
    topic_id = Column(Integer, ForeignKey('model_topic.id'))
    topic = relationship("ModelTopic", back_populates='topic_words')
    back_populates = 'words'
    # user_id = Column(Integer, ForeignKey('user.id'))
    # user = relationship("User", back_populates='user_items')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'topic_id': self.topic_id,
            # 'description': self.description,
            'id': self.id,
            'name': self.name}

    @validates('name')
    def validate_word_name(self, key, title):
        if not name:
            raise AssertionError('No word name provided')
        if len(name) < 1 or len(name) > 40:
            raise AssertionError('Word name must be between'
                                 ' 1 and 40 characters')
        return name

print ("DB_USER={}, DB_PASSWORD={}, DB_NAME={}".format(DB_USER,DB_PASSWORD,DB_NAME ))
engine = create_engine(
    'postgresql://' + DB_USER + ':' + DB_PASSWORD + '@localhost:5432/' + DB_NAME)

Base.metadata.create_all(engine)
