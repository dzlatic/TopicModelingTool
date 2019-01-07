from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base
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
categories = ["Soccer", "Basketball", "Baseball", "Frisbee", "Snowboarding",
              "Rock Climbing", "Foosball", "Skating", "Hockey", "Tennis",
              "JSON"]
for cat_name in categories:
    try:
        category = Category(name=cat_name)
        db_session.add(category)
        db_session.commit()
        print("Category {} added successfully.".format(cat_name))
    except (exc.IntegrityError, AssertionError,
            AttributeError, NameError) as e:
        db_session.rollback()
        print("Error: {}".format(e))
