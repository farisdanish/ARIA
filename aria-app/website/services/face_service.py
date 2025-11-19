"""Face recognition service."""
import os
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
from numpy import asarray, expand_dims, savez_compressed, load
from PIL import Image
from sklearn.preprocessing import LabelEncoder, Normalizer
from sklearn.linear_model import SGDClassifier
from keras_facenet import FaceNet
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class FaceService:
    """Service for face recognition operations."""
    
    def __init__(self):
        self.haar_cascade = cv2.CascadeClassifier(
            cv2.samples.findFile(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        )
        self.facenet = FaceNet()
        self.model = None
        self.label_encoder = None
        self.normalizer = None
    
    def get_faces_db_path(self) -> Path:
        """Get path to faces database directory."""
        return Path(current_app.config.get('FACES_DB_PATH', 'static/MalaysianFacesDB'))
    
    def get_faces_db_file(self) -> Path:
        """Get path to faces database file."""
        return Path(current_app.config.get('FACES_DB_FILE', 'static/registered-faces-db.npz'))
    
    def get_faces_embeddings_file(self) -> Path:
        """Get path to faces embeddings file."""
        return Path(current_app.config.get('FACES_EMBEDDINGS_PATH', 'static/registered-faces-db-embeddings.npz'))
    
    def get_face(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], int, int, int, int]:
        """
        Extract face from image.
        
        Returns:
            (face_array, x1, x2, y1, y2)
        """
        faces = self.haar_cascade.detectMultiScale(image, 1.1, 4)
        
        if len(faces) == 0:
            return None, 0, 0, 0, 0
        
        x1, y1, width, height = faces[0]
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        
        gbr = Image.fromarray(image)
        gbr_array = asarray(gbr)
        face = gbr_array[y1:y2, x1:x2]
        
        return face, x1, x2, y1, y2
    
    def extract_face(self, filename: str, required_size: Tuple[int, int] = (160, 160)) -> Optional[np.ndarray]:
        """Extract face from image file."""
        try:
            image = cv2.imread(filename)
            if image is None:
                logger.warning(f"Could not read image: {filename}")
                return None
            
            faces = self.haar_cascade.detectMultiScale(image, 1.1, 4)
            if len(faces) == 0:
                logger.warning(f"No face detected in: {filename}")
                return None
            
            x1, y1, width, height = faces[0]
            x1, y1 = abs(x1), abs(y1)
            x2, y2 = x1 + width, y1 + height
            
            gbr = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            gbr = Image.fromarray(gbr)
            gbr_array = asarray(gbr)
            
            face_array = gbr_array[y1:y2, x1:x2]
            face_array = Image.fromarray(face_array)
            face_array = face_array.resize(required_size)
            face_array = asarray(face_array)
            
            return face_array
        except Exception as e:
            logger.error(f"Error extracting face from {filename}: {str(e)}")
            return None
    
    def load_faces(self, directory: str) -> list:
        """Load all faces from a directory."""
        faces = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return faces
        
        for filename in os.listdir(directory):
            filepath = dir_path / filename
            if filepath.is_file():
                face = self.extract_face(str(filepath))
                if face is not None:
                    faces.append(face)
        
        return faces
    
    def load_dataset(self, directory: str) -> Tuple[np.ndarray, np.ndarray]:
        """Load face dataset from directory structure."""
        X, y = [], []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            logger.warning(f"Dataset directory does not exist: {directory}")
            return np.array(X), np.array(y)
        
        for subdir in os.listdir(directory):
            subdir_path = dir_path / subdir
            if not subdir_path.is_dir():
                continue
            
            faces = self.load_faces(str(subdir_path))
            labels = [subdir for _ in range(len(faces))]
            
            logger.info(f"Loaded {len(faces)} examples for class: {subdir}")
            X.extend(faces)
            y.extend(labels)
        
        return np.array(X), np.array(y)
    
    def get_embedding(self, face_pixels: np.ndarray) -> np.ndarray:
        """Get face embedding using FaceNet."""
        samples = expand_dims(face_pixels, axis=0)
        yhat = self.facenet.embeddings(samples)
        return yhat[0]
    
    def train_model(self) -> bool:
        """Train the face recognition model."""
        try:
            faces_db_path = self.get_faces_db_path()
            train_path = faces_db_path / 'train'
            test_path = faces_db_path / 'test'
            
            # Load datasets
            logger.info("Loading training dataset...")
            trainX, trainy = self.load_dataset(str(train_path))
            logger.info(f"Training data shape: {trainX.shape}, {trainy.shape}")
            
            logger.info("Loading test dataset...")
            testX, testy = self.load_dataset(str(test_path))
            logger.info(f"Test data shape: {testX.shape}, {testy.shape}")
            
            # Save raw face data
            faces_db_file = self.get_faces_db_file()
            faces_db_file.parent.mkdir(parents=True, exist_ok=True)
            savez_compressed(str(faces_db_file), trainX, trainy, testX, testy)
            logger.info(f"Saved face database to {faces_db_file}")
            
            # Generate embeddings
            logger.info("Generating embeddings...")
            newTrainX = []
            for face_pixels in trainX:
                embedding = self.get_embedding(face_pixels)
                newTrainX.append(embedding)
            newTrainX = np.array(newTrainX)
            
            newTestX = []
            for face_pixels in testX:
                embedding = self.get_embedding(face_pixels)
                newTestX.append(embedding)
            newTestX = np.array(newTestX)
            
            # Save embeddings
            embeddings_file = self.get_faces_embeddings_file()
            savez_compressed(str(embeddings_file), newTrainX, trainy, newTestX, testy)
            logger.info(f"Saved embeddings to {embeddings_file}")
            
            logger.info("Face recognition model training completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training face recognition model: {str(e)}")
            return False
    
    def load_trained_model(self) -> bool:
        """Load the trained face recognition model."""
        try:
            embeddings_file = self.get_faces_embeddings_file()
            
            if not embeddings_file.exists():
                logger.warning("Face embeddings file not found. Model needs to be trained first.")
                return False
            
            # Load embeddings
            data = load(str(embeddings_file))
            trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
            
            # Normalize
            self.normalizer = Normalizer(norm='l2')
            trainX = self.normalizer.transform(trainX)
            testX = self.normalizer.transform(testX)
            
            # Label encode
            self.label_encoder = LabelEncoder()
            self.label_encoder.fit(trainy)
            trainy_encoded = self.label_encoder.transform(trainy)
            testy_encoded = self.label_encoder.transform(testy)
            
            # Train classifier
            self.model = SGDClassifier(loss='log_loss')
            self.model.fit(trainX, trainy_encoded)
            
            logger.info("Face recognition model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading face recognition model: {str(e)}")
            return False
    
    def recognize_face(self, face_image: np.ndarray, confidence_threshold: float = None) -> Tuple[Optional[str], float]:
        """
        Recognize a face from an image.
        
        Returns:
            (identity, confidence) or (None, 0.0) if not recognized
        """
        if self.model is None or self.label_encoder is None or self.normalizer is None:
            if not self.load_trained_model():
                return None, 0.0
        
        if confidence_threshold is None:
            confidence_threshold = current_app.config.get('FACE_CONFIDENCE_THRESHOLD', 0.85)
        
        try:
            # Resize face
            face = Image.fromarray(face_image)
            face = face.resize((160, 160))
            face = asarray(face)
            
            # Get embedding
            face_embedding = self.get_embedding(face)
            
            # Normalize
            face_embedding = self.normalizer.transform([face_embedding])
            
            # Predict
            samples = expand_dims(face_embedding, axis=0)
            nsamples, nx, ny = samples.shape
            samples = samples.reshape((nsamples, nx * ny))
            
            yhat_class = self.model.predict(samples)
            yhat_prob = self.model.predict_proba(samples)
            
            class_index = yhat_class[0]
            class_probability = yhat_prob[0, class_index]
            
            predict_names = self.label_encoder.inverse_transform(yhat_class)
            identity = predict_names[0]
            
            if class_probability > confidence_threshold:
                return identity, float(class_probability)
            else:
                return None, float(class_probability)
                
        except Exception as e:
            logger.error(f"Error recognizing face: {str(e)}")
            return None, 0.0
    
    def save_face_image(self, user_id: str, face_image: np.ndarray, 
                       image_index: int, is_training: bool = True) -> Optional[str]:
        """
        Save a face image to the database.
        
        Returns:
            Relative path to saved image, or None if save failed
        """
        try:
            faces_db_path = self.get_faces_db_path()
            subfolder = 'train' if is_training else 'test'
            user_dir = faces_db_path / subfolder / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{user_id}{image_index}.jpg"
            filepath = user_dir / filename
            
            # Resize and save
            face_resized = cv2.resize(face_image, (200, 200))
            cv2.imwrite(str(filepath), face_resized)
            
            relative_path = f"{subfolder}/{user_id}/{filename}"
            logger.info(f"Saved face image: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Error saving face image: {str(e)}")
            return None

