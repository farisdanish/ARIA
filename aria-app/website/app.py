from flask import Flask
from flask_restx import Api
import os
from os import path
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import UserMixin
from sqlalchemy import inspect, create_engine
from sqlalchemy.ext.automap import automap_base
from MySQLdb import _mysql
from sqlalchemy import MetaData, Table, Column, text, select
from datetime import datetime,timedelta
from flask_mail import Mail, Message
from flask_executor import Executor

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'

app.config['SECRET_KEY'] = 'UMSLIBRARYROOMBOOKINGSYSTEMWITHFACERECOGNITION'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://root:@localhost:3306/fyp_umsliblrbs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(minutes=480)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=480)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# configuration of mail 
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'fyplibraryroomalert@gmail.com'
app.config['MAIL_PASSWORD'] = 'xlng vjkb jouz mjku'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app) 

executor = Executor(app)

db = SQLAlchemy(app)
# api.init_app(app)