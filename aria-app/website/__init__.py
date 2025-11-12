from os import path
from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import LoginManager
from sqlalchemy import inspect, create_engine
from sqlalchemy.ext.automap import automap_base
from MySQLdb import _mysql
from sqlalchemy import MetaData, Table, Column, text, select
from datetime import datetime, timedelta
from .app import app, db
import bcrypt
from flask_login import login_required, current_user
from .apiroutes import ns, api

#db = _mysql.connect(host="localhost",port=3306,user="root",password="",database="fyp_umsliblrbs")
# db = SQLAlchemy()

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'UMSLIBRARYROOMBOOKINGSYSTEMWITHFACERECOGNITION'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://root:@localhost:3306/fyp_umsliblrbs'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db.create_engine('mysql+mysqldb://root:@localhost:3306/fyp_umsliblrbs')

def create_app(): 
    from .views import views #import blueprints to app
    from .auth import auth
    from .apiroutes import apiroute
    from .face import facenet
    with app.app_context():
        from .models import admin, staff, student, announcement
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(apiroute, url_prefix='/api')
    app.register_blueprint(facenet, url_prefix='/')
    
    #add namespace for api to app (namespace is basically blueprints for api)
    api.add_namespace(ns)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        if db.session.query(student).filter_by(StudID = id).first():
            return db.session.query(student).get(id)
        elif db.session.query(staff).filter_by(StaffID = id).first():
            return db.session.query(staff).get(id)
        elif db.session.query(admin).filter_by(AdminID = id).first():
            return db.session.query(admin).get(id)
    
    return app
