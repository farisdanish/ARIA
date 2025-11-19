"""
Face recognition module for edge device.
"""
import cv2
import numpy as np
from numpy import asarray, expand_dims, load
from PIL import Image
from sklearn.preprocessing import LabelEncoder, Normalizer
from sklearn.linear_model import SGDClassifier
from keras_facenet import FaceNet
from pathlib import Path
import logging
from typing import Optional, Tuple

from .config import ClientConfig

logger = logging.getLogger(__name__)


class FaceRecognizer:
    """Face recognition for edge device."""
    
    def __init__(self):
        self.haar_cascade = cv2.CascadeClassifier(
            cv2.samples.findFile(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        )
        self.facenet = FaceNet()
        self.model = None
        self.label_encoder = None
        self.normalizer = None
        self.loaded = False
    
    def load_model(self, faces_db_path: Path = None, embeddings_path: Path = None) -> bool:
        """
        Load face recognition model.
        
        Args:
            faces_db_path: Path to faces database file
            embeddings_path: Path to embeddings file
        """
        faces_db_path = faces_db_path or ClientConfig.FACES_DB_FILE
        embeddings_path = embeddings_path or ClientConfig.FACES_EMBEDDINGS_FILE
        
        if not embeddings_path.exists():
            logger.error(f"Embeddings file not found: {embeddings_path}")
            return False
        
        try:
            # Load embeddings
            data = load(str(embeddings_path))
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
            
            self.loaded = True
            logger.info("Face recognition model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading face recognition model: {str(e)}")
            return False
    
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
    
    def recognize_face(self, face_image: np.ndarray, expected_identity: str = None) -> Tuple[Optional[str], float]:
        """
        Recognize a face from an image.
        
        Args:
            face_image: Face image array
            expected_identity: Expected user ID (optional, for verification)
            
        Returns:
            (identity, confidence) or (None, 0.0) if not recognized
        """
        if not self.loaded:
            logger.warning("Model not loaded. Call load_model() first.")
            return None, 0.0
        
        try:
            # Resize face
            face = Image.fromarray(face_image)
            face = face.resize((160, 160))
            face = asarray(face)
            
            # Get embedding
            face_embedding = expand_dims(face, axis=0)
            signature = self.facenet.embeddings(face_embedding)
            
            # Normalize
            samples = expand_dims(signature, axis=0)
            nsamples, nx, ny = samples.shape
            samples = samples.reshape((nsamples, nx * ny))
            samples = self.normalizer.transform(samples)
            
            # Predict
            yhat_class = self.model.predict(samples)
            yhat_prob = self.model.predict_proba(samples)
            
            class_index = yhat_class[0]
            class_probability = yhat_prob[0, class_index]
            
            predict_names = self.label_encoder.inverse_transform(yhat_class)
            identity = predict_names[0]
            
            # Check if matches expected identity
            if expected_identity and identity != expected_identity:
                logger.debug(f"Identity mismatch: expected {expected_identity}, got {identity}")
                return None, float(class_probability)
            
            # Check confidence threshold
            if class_probability >= ClientConfig.FACE_CONFIDENCE_THRESHOLD:
                return identity, float(class_probability)
            else:
                logger.debug(f"Confidence too low: {class_probability:.2f} < {ClientConfig.FACE_CONFIDENCE_THRESHOLD}")
                return None, float(class_probability)
                
        except Exception as e:
            logger.error(f"Error recognizing face: {str(e)}")
            return None, 0.0

