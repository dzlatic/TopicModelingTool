from flask import Flask, render_template, request, \
    redirect, jsonify, url_for, flash
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


from database_setup import Base, Category, CategoryItem, User

app = Flask(__name__)


CLIENT_ID = json.loads(
    open("/var/www/CatalogApp/CatalogApp/client_secrets.json", 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

DB_USER = json.loads(
    open("/var/www/CatalogApp/CatalogApp/db_secrets.json", 'r').read())['database']['user']

DB_PASSWORD = json.loads(
    open("/var/www/CatalogApp/CatalogApp/db_secrets.json", 'r').read())['database']['password']

DB_NAME = json.loads(
    open("/var/www/CatalogApp/CatalogApp/db_secrets.json", 'r').read())['database']['name']

APPLICATION_NAME = "Catalog App"


engine = create_engine(
    'postgresql://' + DB_USER + ':' + DB_PASSWORD + '@localhost:5432/' + DB_NAME)


Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
db_session = DBSession()


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


@app.route('/catalog/JSON')
@check_session_status
def catalog_json():
    categories = db_session.query(Category)\
        .options(joinedload(Category.category_items))
    return jsonify(Category=[c.serialize for c in categories])


@app.route('/')
@app.route('/catalog/')
@check_session_status
def show_catalog():
    login_session['last_category'] = "Latest Items"
    categories = db_session.query(Category).order_by(asc(Category.name))
    latest_items = db_session \
        .query(CategoryItem, Category) \
        .join(Category, CategoryItem.cat_id == Category.id) \
        .order_by(asc(CategoryItem.id)) \
        .limit(10)
    if 'username' not in login_session:
        helper_categories = []
    else:
        helper_categories = [{'name': "My Items"}]
    active_category = {'name': "Latest Items", 'category_items': latest_items}
    return render_template('catalog.html',
                           categories=categories,
                           helper_categories=helper_categories,
                           active_category=active_category,
                           latest=True,
                           session=login_session)


@app.route('/catalog/<category_name>/JSON')
@check_session_status
def show_category_json(category_name):
    try:
        category = db_session.query(Category)\
            .filter_by(name=category_name).one()
        return jsonify(Category=[category.serialize])
    except orm_exc.NoResultFound:
        flash(
            "Category {} doesn't exist.".format(category_name), "flash-warn")
        return redirect(location=url_for('show_catalog'),
                        code=302,
                        Response=None)


@app.route('/catalog/<category_name>/')
@check_session_status
def show_catalog_category(category_name):
    login_session['last_category'] = category_name
    categories = db_session.query(Category).order_by(asc(Category.name))
    if category_name == "Latest Items":
        latest_items = db_session \
            .query(CategoryItem, Category) \
            .join(Category, CategoryItem.cat_id == Category.id)\
            .order_by(asc(CategoryItem.id)) \
            .limit(10)
        active_category = {'name': "Latest Items",
                           'category_items': latest_items}
        latest = True
        my = False
        if 'username' not in login_session:
            helper_categories = []
        else:
            helper_categories = [{'name': "My Items"}]
    elif category_name == "My Items":
        my_items = db_session \
            .query(CategoryItem, User) \
            .join(User, CategoryItem.user_id == User.id) \
            .order_by(asc(CategoryItem.title))
        active_category = {'name': "My Items", 'category_items': my_items}
        latest = False
        my = True
        helper_categories = [{'name': "Latest Items"}]
    else:
        categories = db_session.query(Category).order_by(asc(Category.name))
        if 'username' not in login_session:
            helper_categories = [{'name': "Latest Items"}]
        else:
            helper_categories = [{'name': "My Items"},
                                 {'name': "Latest Items"}]
        latest = False
        my = False
        try:
            active_category = db_session.query(Category)\
                .filter_by(name=category_name).one()
            login_session['count'] = len(active_category.category_items)
        except orm_exc.NoResultFound:
            flash("Category {} doesn't exist.".format(category_name),
                  "flash-warn")
            return redirect(location=url_for('show_catalog'),
                            code=302,
                            Response=None)

    return render_template('catalog.html',
                           categories=categories,
                           helper_categories=helper_categories,
                           active_category=active_category,
                           latest=latest,
                           my=my,
                           session=login_session)


@app.route('/item/<int:item_id>/JSON')
@check_session_status
def show_item_json(item_id):
    try:
        item = db_session.query(CategoryItem).filter_by(id=item_id).one()
        return jsonify(Item=[item.serialize])
    except orm_exc.NoResultFound:
        flash("Item with id:{} doesn't exist.".format(item_id),
              "flash-warn")
        return redirect(location=url_for('show_catalog'),
                        code=302,
                        Response=None)


@app.route('/item/<int:item_id>/')
@check_session_status
def show_item(item_id):
    try:
        item = db_session.query(CategoryItem).filter_by(id=item_id).one()
    except orm_exc.NoResultFound:
        flash("Item with id:{} doesn't exist.".format(item_id),
              "flash-warn")
        return redirect(location=url_for('show_catalog'),
                        code=302,
                        Response=None)
    return render_template('item.html', item=item, session=login_session)


@app.route('/catalog/<category_name>/new_item/', methods=['GET', 'POST'])
@check_session_status
@login_required
def add_item(category_name):
    try:
        category = db_session.query(Category)\
            .filter_by(name=category_name)\
            .one()
        if request.method == 'POST':
            try:
                new_item = CategoryItem(title=request.form['title'],
                                        description=request.form[
                                            'description'],
                                        cat_id=category.id,
                                        user_id=login_session['user_id'])
                db_session.add(new_item)
                db_session.commit()
                flash("Item successfully created.", "flash-ok")
                return redirect(url_for('show_catalog_category',
                                        category_name=login_session[
                                            'last_category']))
            except (IntegrityError, orm_exc.NoResultFound,
                    AssertionError, NameError) as e:
                db_session.rollback()
                flash("Error: {}".format(e), "flash-error")
                categories = db_session.query(Category)\
                    .order_by(Category.name)
                return render_template('newItem.html',
                                       categories=categories,
                                       session=login_session)
        else:
            return render_template('newItem.html',
                                   category=category,
                                   session=login_session)
    except orm_exc.NoResultFound:
        flash("Category {} doesn't exist.".format(category_name),
              "flash-warn")
        return redirect(location=url_for('show_catalog'),
                        code=302,
                        Response=None)


@app.route('/item/<int:item_id>/edit/', methods=['GET', 'POST'])
@check_session_status
@login_required
def edit_item(item_id):
    try:
        item = db_session.query(CategoryItem).filter_by(id=item_id).one()
        if request.method == 'POST':
            try:
                if request.form['title']:
                    item.title = request.form['title']
                if request.form['description']:
                    item.description = request.form['description']
                if request.form['category_id']:
                    item.cat_id = request.form['category_id']
                db_session.add(item)
                db_session.commit()
                flash("Item successfully edited.", "flash-ok")
            except (IntegrityError,
                    orm_exc.NoResultFound,
                    AssertionError,
                    NameError) as e:
                db_session.rollback()
                flash("Error: {}".format(e), "flash-error")
                categories = db_session.query(Category)\
                    .order_by(Category.name)
                return render_template('editItem.html',
                                       item=item,
                                       categories=categories,
                                       session=login_session)
            flash("Item successfully edited.", "flash-ok")
            return redirect(url_for('show_catalog_category',
                                    category_name=login_session[
                                        'last_category']))
        else:
            categories = db_session.query(Category).order_by(Category.name)
            return render_template('editItem.html',
                                   item=item,
                                   categories=categories,
                                   session=login_session)
    except orm_exc.NoResultFound:
        flash("Item with id:{} doesn't exist.".format(item_id),
              "flash-warn")
        return redirect(location=url_for('show_catalog'),
                        code=302,
                        Response=None)


@app.route('/item/<int:item_id>/delete/', methods=['GET', 'POST'])
@check_session_status
@login_required
def delete_item(item_id):
    try:
        item = db_session.query(CategoryItem).filter_by(id=item_id).one()
        if request.method == 'POST':
            try:
                db_session.delete(item)
                db_session.commit()
                flash("Item successfully deleted.", "flash-ok")
                return redirect(url_for('show_catalog_category',
                                        category_name=login_session[
                                            'last_category']))
            except (IntegrityError,
                    orm_exc.NoResultFound,
                    AssertionError,
                    NameError) as e:
                db_session.rollback()
                flash("Error: {}".format(e), "flash-error")
                return redirect(location=url_for('show_catalog'),
                                code=302,
                                Response=None)
        else:
            return render_template('deleteItem.html',
                                   item=item,
                                   session=login_session)
    except orm_exc.NoResultFound:
        flash("Item with id:{} doesn't exist.".format(item_id),
              "flash-warn")
        return redirect(location=url_for('show_catalog'),
                        code=302,
                        Response=None)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['session_code']:
        flash("Invalid state parameter. received: {}  sent {}".format(
            request.args.get('state'), login_session['session_code']),
            "flash-error")
        return redirect(location=url_for('show_catalog'),
                        code=401,
                        Response=None)
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets("/var/www/CatalogApp/CatalogApp/client_secrets.json", scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        flash("Failed to upgrade the authorization code with Google",
              "flash-error")
        return redirect(location=url_for('show_catalog'),
                        code=401,
                        Response=None)

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)  # noqa
    h = httplib2.Http()
    result = json.loads((h.request(url, 'GET')[1]).decode())
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        flash("There was an error in the access token info.",
              "flash-error")
        return redirect(location=url_for('show_catalog'),
                        code=401,
                        Response=None)

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        flash("Token's user ID doesn't match given user ID.",
              "flash-error")
        return redirect(location=url_for('show_catalog'),
                        code=401,
                        Response=None)

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        flash("Token's client ID does not match app's.",
              "flash-error")
        return redirect(location=url_for('show_catalog'),
                        code=401,
                        Response=None)

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        flash("Current user is already connected.",
              "flash-ok")
        return redirect(location=url_for('show_catalog'),
                        code=302,
                        Response=None)

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    # login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = get_user_id(data["email"])
    if not user_id:
        user_id = create_user(login_session)

    if user_id is None:
        return redirect(location=url_for('show_catalog'),
                        code=401,
                        Response=None)

    login_session['user_id'] = user_id

    flash("You have successfully signed in with Google.",
          "flash-ok")
    return redirect(location=url_for('show_catalog'),
                    code=302,
                    Response=None)


# User Helper Functions
def create_user(session):
    try:
        new_user = User(name=session['username'],
                        email=session['email'],
                        picture=session['picture'])
        db_session.add(new_user)
        db_session.commit()
        user = db_session.query(User)\
            .filter_by(email=login_session['email']).one()
    except (IntegrityError,
            orm_exc.NoResultFound,
            AssertionError,
            AttributeError,
            NameError) as e:
        db_session.rollback()
        flash("Error: {}".format(e), "flash-error")
        return None
    return user.id


def get_user_id(email):
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except (IntegrityError,
            orm_exc.NoResultFound,
            AssertionError,
            AttributeError,
            NameError) as e:
        db_session.rollback()
        flash("Error: {}".format(e), "flash-error")
        return None


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.

    access_token = login_session.get('access_token')
    login_session.clear()
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return redirect(location=url_for('show_catalog'),
                        code=302,
                        Response=None)
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(location=url_for('show_catalog'),
                        code=302,
                        Response=None)
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return redirect(location=url_for('show_catalog'),
                        code=302,
                        Response=None)


# Handle wrong URLs in a friendly way
@app.errorhandler(404)
@check_session_status
def default_route(e):
    flash("You have typed an invalid URL", "flash-error")
    return redirect(location=url_for('show_catalog'),
                    code=302,
                    Response=None)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=80)
