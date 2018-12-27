#!/usr/bin/env python
from flask import (Flask, render_template, request,
                   redirect, jsonify, url_for, flash)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from functools import wraps


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('/var/www/catalog/client_secrets.json', 'r').read())['web']['client_id']

APPLICATION_NAME = "Catalog App"

# Connect to Database and create database session
engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.
                      ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.
                                 dumps('Current user is already connected'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """' " style = "width: 300px; height: 300px;border-radius:150px;
                     -webkit-border-radius: 150px;
                     -moz-border-radius: 150px;"> '"""
    flash("you are now logged in as %s" % login_session['username'])
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


def login_required(f):
    @wraps(f)
    def decorate_login(*args, **kwargs):
        if 'username' not in login_session:
            flash('You need to login')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorate_login


# Show all categories
@app.route('/')
@app.route('/categories/')
def showcategories():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).order_by(Item.id).all()[::-1]
    if 'username' not in login_session:
        return render_template('publiccategories.html',
                               categories=categories,
                               items=items)
    else:
        return render_template('categories.html',
                               categories=categories,
                               items=items)


# Show items of category
@app.route('/categories/<string:category_name>/')
@app.route('/categories/<string:category_name>/items/')
def showItems(category_name):
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(name=category_name).one()
    creator = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(
        category=category).all()
    if ('username' not in login_session or
            creator.id != login_session.get('user_id')):
        return render_template('publicitems.html', items=items,
                               categories=categories, category=category,
                               category_name=category_name, creator=creator)
    else:
        return render_template('items.html', items=items,
                               categories=categories, category=category,
                               category_name=category_name, creator=creator)


# Show description of item
@app.route('/categories/<string:category_name>/')
@app.route('/categories/<string:category_name>/<string:item_name>/')
def showDescription(category_name, item_name):
    categories = session.query(Category).filter_by(name=category_name).one()
    creator = getUserInfo(categories.user_id)
    items = session.query(Item).filter_by(
        name=item_name).first()

    if ('username' not in login_session or
            creator.id != login_session.get('user_id')):
        return render_template('publicdescription.html',
                               items=items, categories=categories,
                               category_name=category_name,
                               item_name=item_name, creator=creator)
    else:
        return render_template('description.html', items=items,
                               categories=categories,
                               category_name=category_name,
                               item_name=item_name, creator=creator)


# Add new category
@app.route('/categories/new/', methods=['GET', 'POST'])
@login_required
def newcategory():
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], user_id=login_session.get('user_id'))
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showcategories'))
    else:
        return render_template('newcategory.html')


# Edit Category
@app.route('/categories/<string:category_name>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_name):
    editedCategory = session.query(
        Category).filter_by(name=category_name).one()
    if editedCategory.user_id != login_session.get('user_id'):
        return "<script>function myFunction() {alert(\
        'You are not authorized to edit this category.\
         Please create your own category in order to edit.');}\
         </script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('showcategories'))
    else:
        return render_template('editcategory.html', category=editedCategory,
                               category_name=category_name)


# Delete Category
@app.route('/categories/<string:category_name>/delete/',
           methods=['GET', 'POST'])
@login_required
def deleteCategory(category_name):
    categoryToDelete = session.query(
        Category).filter_by(name=category_name).one()
    if categoryToDelete.user_id != login_session.get('user_id'):
        return "<script>function myFunction() {alert(\
        'You are not authorized to delete this category.\
         Please create your own category in order to delete.');}\
         </script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.query(
            Item).filter_by(category=categoryToDelete).delete()
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('showcategories'))
    else:
        return render_template('deletecategory.html',
                               category=categoryToDelete)


# Create a new categories
@app.route('/categories/item/new/', methods=['GET', 'POST'])
@login_required
def newItem():
    categories = session.query(Category).all()
    if request.method == 'POST':
        category = session.query(Category).filter_by(
                                 name=request.form['category']).one()
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category=category, user_id=login_session.get('user_id'))
        session.add(newItem)
        session.commit()
        flash('New item %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showItems', category_name=category.name))
    else:
        return render_template('newitem.html', categories=categories)


# Edit an item
@app.route('/categories/<string:category_name>/item/<string:item_name>/edit/',
           methods=['GET', 'POST'])
@login_required
def editItem(category_name, item_name):
    categories = session.query(Category).all()
    editedItem = session.query(Item).filter_by(name=item_name).one()
    category = session.query(Category).filter_by(name=category_name).one()
    if login_session.get('user_id') != editedItem.user_id:
        return "<script>function myFunction(){alert(\
        'You are not authorized to edit items to this category.\
        Please create your own category in order to edit items.');}\
        </script><body onload='myFunction()''>"
    if request.method == 'POST':
        categoryradio = session.query(Category).filter_by(
                                      name=request.form['category']).one()
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            editedItem.category = categoryradio
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('showItems', category_name=category.name))
    else:
        return render_template('edititem.html',
                               category_name=category_name,
                               item_name=item_name, item=editedItem,
                               categories=categories)


# Delete an item
@app.route('/categories/<string:category_name>/item/<string:item_name>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteItem(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    itemToDelete = session.query(Item).filter_by(name=item_name).one()
    if login_session.get('user_id') != itemToDelete.user_id:
        return "<script>function myFunction(){alert(\
        'You are not authorized to delete items to this category.\
        Please create your own category in order to delete items.');}\
        </script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showItems', category_name=category.name))
    else:
        return render_template('deleteItem.html', item=itemToDelete,
                               category=category)


# JSON APIs to view categories Information
@app.route('/categories/JSON')
def showcategoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[c.serialize for c in categories])


# JSON APIs to view items Information
@app.route('/categories/<string:category_name>/items/JSON')
def showItemsJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(
        category=category).all()
    return jsonify(items=[i.serialize for i in items])


@app.route('/categories/<string:category_name>/items/<string:item_name>/JSON')
def ItemJSON(category_name, item_name):
    items = session.query(Item).filter_by(name=item_name).one()
    return jsonify(items=items.serialize)


@app.route('/categories.json')
def showJSON():
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return jsonify(Categories=[c.serialize for c in categories],
                   Item=[c.serialize for c in items])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
