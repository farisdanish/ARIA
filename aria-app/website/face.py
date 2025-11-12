from PIL import Image
from keras.models import load_model
from keras_facenet import FaceNet
import numpy as np
from numpy import asarray
from numpy import expand_dims
import pickle
import cv2
from pathlib import Path
from random import choice
from numpy import load
from numpy import expand_dims
from numpy import savez_compressed
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import SGDClassifier
from matplotlib import pyplot as plt
from sklearn.metrics import confusion_matrix
from sklearn.metrics import ConfusionMatrixDisplay

from flask import Blueprint, Response, render_template, request, flash, redirect, url_for, jsonify, session, current_app
from flask_login import login_required, current_user
from .app import app, db, executor
from .models import admin, staff, student, registeredfaces
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
import json
import urllib.request
import os
import re
from os import listdir
from os.path import join, dirname, realpath,isdir
from werkzeug.utils import secure_filename
from .views import views

facenet = Blueprint('facenet', __name__)

HaarCascade = cv2.CascadeClassifier(cv2.samples.findFile(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'))
MyFaceNet = FaceNet()
os.chdir('D:/Educational/FYP Web Development/website')

def get_face(gbr1):
    face = HaarCascade.detectMultiScale(gbr1,1.1,4)
    
    if face is ():
        face = None
        x1, y1 = 0, 0
        x2, y2 = 0, 0
    else:
        if len(face)>0:
            x1, y1, width, height = face[0]
        else:
            x1, y1, width, height = 1, 1, 10, 10
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        #gbr = cv2.cvtColor(gbr1, cv2.COLOR_BGR2RGB)
        gbr = gbr1
        gbr = Image.fromarray(gbr)                  # convert from OpenCV to PIL format
        gbr_array = asarray(gbr)
        face = gbr_array[y1:y2, x1:x2]
    return face, x1, x2, y1, y2
        

def detect_facenet():
    # load faces
    data = np.load('D:/Educational/FYP Web Development/website/static/registered-faces-db.npz')
    testX_faces = data['arr_2']
    # load face embeddings
    data = np.load('D:/Educational/FYP Web Development/website/static/registered-faces-db-embeddings.npz')
    trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
    # normalize input vectors
    in_encoder = Normalizer(norm='l2')
    trainX = in_encoder.transform(trainX)
    testX = in_encoder.transform(testX)
    # label encode targets
    out_encoder = LabelEncoder()
    out_encoder.fit(trainy)
    trainy = out_encoder.transform(trainy)
    testy = out_encoder.transform(testy)

    # fit model
    model = SGDClassifier(loss='log_loss')
    # model = HistGradientBoostingClassifier()
    model.fit(trainX, trainy)

    detected = False
    count=0
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG")) #compressed video format for video processing
    #print (cap.read())
    
    while(True):
        _, gbr1 = cap.read()

        
        face, x1, x2, y1, y2 = get_face(gbr1)

        if type(face) is np.ndarray:
            face = Image.fromarray(face)
            face = face.resize((160,160))
            face = asarray(face)

            face = expand_dims(face, axis=0)
            signature = MyFaceNet.embeddings(face)
    
            #predict face
            samples = expand_dims(signature, axis=0)
            nsamples, nx, ny = samples.shape
            samples = samples.reshape((nsamples,nx*ny))
            yhat_class = model.predict(samples)
            yhat_prob = model.predict_proba(samples)
            # get name
            class_index = yhat_class[0]
            class_probability = yhat_prob[0,class_index] * 100
            predict_names = out_encoder.inverse_transform(yhat_class)
            identity = predict_names[0]
    
            if class_probability > 85:
                print('Predicted: %s (%.3f)' % (predict_names[0], class_probability))
                cv2.putText(gbr1,identity, (100,100),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 128, 0), 2, cv2.LINE_AA)
                #cv2.putText(gbr1,str(min_dist*100), (100,100),cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)
                cv2.rectangle(gbr1,(x1,y1),(x2,y2), (0,255,0), 2)
                #detected = True
                count = count + 1
            else:
                print('(Might be Wrong face)Predicted: %s (%.3f)' % (predict_names[0], class_probability))
                cv2.putText(gbr1,identity, (100,100),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                #cv2.putText(gbr1,str(min_dist*100), (100,100),cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)
                cv2.rectangle(gbr1,(x1,y1),(x2,y2), (0,255,0), 2)
        else:
            cv2.putText(gbr1,"No face found", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 2)
        
        ret, buffer = cv2.imencode('.jpg', gbr1)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def train():
    print("START REFRESH")
    # extract a single face from a given photograph
    def extract_face(filename, required_size=(160, 160)):
        gbr1 = cv2.imread(filename)
        wajah = HaarCascade.detectMultiScale(gbr1,1.1,4) #extract face from photograph read using Haar Cascade
        print(filename)
        if len(wajah)>0:
            x1, y1, width, height = wajah[0]
        else:
            x1, y1, width, height = 1, 1, 10, 10

        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        print(filename)
        gbr = cv2.cvtColor(gbr1, cv2.COLOR_BGR2RGB)
        gbr = Image.fromarray(gbr)                  # convert from OpenCV to PIL
        gbr_array = asarray(gbr)

        face_array = gbr_array[y1:y2, x1:x2]

        face_array = Image.fromarray(face_array)
        face_array = face_array.resize(required_size)
        face_array = asarray(face_array)
        return face_array

    # function to load images and extract faces for all images in a directory
    def load_faces(directory):
        faces = list()
        # enumerate files
        for filename in listdir(directory):
            #print(filename)
            # path
            path = directory + filename
            # get face
            face = extract_face(path)
            # store
            faces.append(face)
        return faces


    # load a dataset that contains one subdir for each class that in turn contains images
    def load_dataset(directory):
        X, y = list(), list()
        # enumerate folders, on per class
        for subdir in listdir(directory):
            #print(subdir)
            # path
            path = directory + subdir + '/'
            # skip any files that might be in the dir
            if not isdir(path):
                continue
            # load all faces in the subdirectory
            faces = load_faces(path)
            # create labels
            labels = [subdir for _ in range(len(faces))]
            # summarize progress
            print('>loaded %d examples for class: %s' % (len(faces), subdir))
            # store
            X.extend(faces)
            y.extend(labels)
        return asarray(X), asarray(y)

    # load train datasetcomment
    trainX, trainy = load_dataset('D:/Educational/FYP Web Development/website/static/MalaysianFacesDB/train/')
    print(trainX.shape, trainy.shape)
    #load test datasetcomment
    testX, testy = load_dataset('D:/Educational/FYP Web Development/website/static/MalaysianFacesDB/test/')
    print(testX.shape, testy.shape)
    #save arrays to one file in compressed formatcomment
    savez_compressed('D:/Educational/FYP Web Development/website/static/registered-faces-db.npz', trainX, trainy, testX, testy)

    data = np.load('D:/Educational/FYP Web Development/website/static/registered-faces-db.npz')
    trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
    print('Loaded: ', trainX.shape, trainy.shape, testX.shape, testy.shape)

    # get the face embedding for one face
    def get_embedding(model, face_pixels):
        samples = expand_dims(face_pixels, axis=0)
        # make prediction to get embedding
        yhat = model.embeddings(samples)
        return yhat[0]

    # load the face dataset
    data = np.load('D:/Educational/FYP Web Development/website/static/registered-faces-db.npz')
    trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
    print('Loaded: ', trainX.shape, trainy.shape, testX.shape, testy.shape)
    
    # convert each face in the train set to an embedding
    newTrainX = list()
    for face_pixels in trainX:
        embedding = get_embedding(MyFaceNet, face_pixels)
        newTrainX.append(embedding)
    newTrainX = asarray(newTrainX)
    print(newTrainX.shape)
    # convert each face in the test set to an embedding
    newTestX = list()
    for face_pixels in testX:
        embedding = get_embedding(MyFaceNet, face_pixels)
        newTestX.append(embedding)
    newTestX = asarray(newTestX)
    print(newTestX.shape)
    # save arrays to one file in compressed format
    savez_compressed('D:/Educational/FYP Web Development/website/static/registered-faces-db-embeddings.npz', newTrainX, trainy, newTestX, testy)

    print("END REFRESH")

#REGISTER FACE ALGORITHM
#--------------------------------------------------------------------
def face_reg(name):
    userName = name
    video_capture = cv2.VideoCapture(0)
    count = 0
    faceDirectoryPath = ""
    train_limit=9
    while True:
        _, frame = video_capture.read()
        
        face, x1, x2, y1, y2 = get_face(frame)
        
        if face is not None and count<train_limit:
            count+=1
            #print(count)
            face = cv2.resize(face,(200,200))
            #face=cv2.cvtColor(face,cv2.COLOR_BGR2GRAY)
            if count < train_limit:
                Path("D:/Educational/FYP Web Development/website/static/MalaysianFacesDB/train/{}".format(userName)).mkdir(parents=True, exist_ok=True) #tukar path
                train_file_name_path='D:/Educational/FYP Web Development/website/static/MalaysianFacesDB/train/{}/{}{}.jpg'.format(userName,userName, count) #tukar path
                cv2.imwrite( train_file_name_path,face)
                savename = "train/" + "{}/{}{}.jpg".format(userName,userName, count)
                if faceDirectoryPath == "":
                    faceDirectoryPath = savename
                else:
                    faceDirectoryPath = faceDirectoryPath + "\n" + savename
            else:
                Path("D:/Educational/FYP Web Development/website/static/MalaysianFacesDB/test/{}".format(userName)).mkdir(parents=True, exist_ok=True) #tukar path
                test_file_name_path='D:/Educational/FYP Web Development/website/static/MalaysianFacesDB/test/{}/{}{}.jpg'.format(userName,userName, count) #tukar path
                cv2.imwrite(test_file_name_path,face)
                savename = "test/" + "{}/{}{}.jpg".format(userName,userName, count)
                faceDirectoryPath = faceDirectoryPath + "\n" + savename
            cv2.putText(frame,str(count),(50,50),cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),2)
        elif face is None and count<train_limit:
            print("Face not found")
            cv2.putText(frame,"No face found", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 2)
            pass
        if count>=train_limit:
            # print("SCAN COMPLETE!")
            with app.app_context():
                Student = db.session.query(student).filter_by(StudID = userName).first()
                Staff = db.session.query(staff).filter_by(StaffID = userName).first()
                if Student and count == train_limit:
                    new_face = registeredfaces(FaceIMG = faceDirectoryPath, StudID = userName, StaffID = None )
                elif Staff and count == train_limit:
                    new_face = registeredfaces(FaceIMG = faceDirectoryPath, StudID = None, StaffID = userName )
                if count == train_limit:
                    db.session.add(new_face)
                    db.session.commit()
                msg = "Face Registered!,\nPlease Press the Back Button!"
                count+=1
                y0, dy = 50, 24
                for i, line in enumerate(msg.split('\n')): #Split text at newlines
                    y = y0 + i*dy
                    cv2.putText(frame,line, (50, y), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 2)
        
        if count==200:
            print("SCAN COMPLETE!")
            break
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# FACE RECOGNITION
#--------------------------------------------------------------------
@facenet.route('/face_recog', methods=['GET','POST'])
@login_required
def face_regstr():
    if current_user.is_Student():
        return Response(face_reg(current_user.StudID), mimetype='multipart/x-mixed-replace; boundary=frame')
    elif current_user.is_Staff():
        return Response(face_reg(current_user.StaffID), mimetype='multipart/x-mixed-replace; boundary=frame')

@facenet.route('/register_face', methods=['GET','POST'])
@login_required
def register_face():
    return render_template("faceRegister.html", user=current_user, is_Student=True, is_Staff=False, is_Admin=False)

@app.route('/train_data')
@login_required
def train_data():
   if current_user.is_Admin():
        executor.submit(train)
        # Redirect to a specific page after training
        flash('Face Detection Model is refreshing...', category='info')
        return redirect(url_for('views.home'))
   return redirect(url_for('views.home'))