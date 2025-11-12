import os
from os import listdir
from os.path import isdir
from PIL import Image as Img
from numpy import asarray
from numpy import expand_dims
from matplotlib import pyplot
from numpy import savez_compressed
from keras.models import load_model
import numpy as np
import tensorflow as tf
from keras_facenet import FaceNet

import pickle
import cv2

HaarCascade = cv2.CascadeClassifier(cv2.samples.findFile(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'))
MyFaceNet = FaceNet()
os.chdir('D:/Educational/FYP Web Development/website')

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
 gbr = Img.fromarray(gbr)                  # convert from OpenCV to PIL
 gbr_array = asarray(gbr)

 face_array = gbr_array[y1:y2, x1:x2]

 face_array = Img.fromarray(face_array)
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

# specify folder to plot
#folder = 'drive/MyDrive/Malaysian Faces Database/train/Ernest/'
#i = 1
# enumerate files
#for filename in listdir(folder):
  #path
 #path = folder + filename
 # get face
 #face = extract_face(path)
 #print(i, face.shape)
 # plot
 #pyplot.subplot(2, 7, i)
 #pyplot.axis('off')
 #pyplot.imshow(face)
 #pyplot.title(filename)
 #i += 1
#pyplot.show()
#checking for test folder

data = np.load('D:/Educational/FYP Web Development/website/static/registered-faces-db.npz')
trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
print('Loaded: ', trainX.shape, trainy.shape, testX.shape, testy.shape)

# get the face embedding for one face
def get_embedding(model, face_pixels):
 # scale pixel values
 #face_pixels = face_pixels.astype('float32')
 # standardize pixel values across channels (global)
 #mean, std = face_pixels.mean(), face_pixels.std()
 #face_pixels = (face_pixels - mean) / std
 # transform face into one sample
 samples = expand_dims(face_pixels, axis=0)
 # make prediction to get embedding
 yhat = model.embeddings(samples)
 return yhat[0]

# load the face dataset
data = np.load('D:/Educational/FYP Web Development/website/static/registered-faces-db.npz')
trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
print('Loaded: ', trainX.shape, trainy.shape, testX.shape, testy.shape)
# load the facenet model
#model = load_model('facenet_keras.h5')
#print('Loaded Model')
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

# develop a classifier for the 5 Celebrity Faces Dataset
from random import choice
from numpy import load
from numpy import expand_dims
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import SGDClassifier
from matplotlib import pyplot as plt
from sklearn.metrics import confusion_matrix
from sklearn.metrics import ConfusionMatrixDisplay

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
#model = SVC(kernel='linear', probability=True)
# model = SGDClassifier(loss='log_loss')
model = HistGradientBoostingClassifier()
fcnt = model.fit(trainX, trainy)
print(model.score(testX,testy)*100)
#plot graph

#fcnt.plot(ax=ax, alpha=0.8)
# test model on a 10 random examples from the test dataset
modelAccuracy = 0.0
iteration = 10
for i in range(0, iteration):
 selection = choice([i for i in range(testX.shape[0])])
 print(selection)
 random_face_pixels = testX_faces[selection]
 random_face_emb = testX[selection] #facenet embeddings
 random_face_class = testy[selection]
 random_face_name = out_encoder.inverse_transform([random_face_class])
 # prediction for the face
 samples = expand_dims(random_face_emb, axis=0)
 yhat_class = model.predict(samples)
 yhat_prob = model.predict_proba(samples)
 # get name
 class_index = yhat_class[0]
 class_probability = yhat_prob[0,class_index] * 100
 predict_names = out_encoder.inverse_transform(yhat_class)
 print('Predicted: %s (%.3f)' % (predict_names[0], class_probability))
 print('Expected: %s' % random_face_name[0])

 modelAccuracy += class_probability
print("Model accuracy based on ",iteration," iterations of test data: ",modelAccuracy/iteration)