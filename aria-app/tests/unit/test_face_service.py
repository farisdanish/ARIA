"""Unit tests for FaceService.

All tests mock _ensure_facenet() and _ensure_haar() so the real 500MB FaceNet
model and OpenCV CascadeClassifier are NEVER loaded. Tests run inside an app
context because FaceService.get_faces_db_* use current_app.config.

Tests cover:
- _ensure_facenet: skips re-init when already loaded; returns False on ImportError
- get_embedding: raises RuntimeError when model unavailable; delegates to facenet
- get_face: returns None on zero detections; returns coords on one detection
- extract_face: returns None for missing file or undetectable face
- recognize_face: returns (None, 0.0) when model missing; thresholding logic
- save_face_image: correct path structure; returns None on write failure
"""
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from website.services.face_service import FaceService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def svc(app):
    """A FaceService instance with a live app context."""
    with app.app_context():
        yield FaceService()


@pytest.fixture
def svc_with_facenet(svc):
    """FaceService where facenet is already 'loaded' via a stub."""
    svc.facenet = MagicMock()
    return svc


def _fake_face_pixels():
    """160×160 RGB uint8 image array — smallest valid input for FaceNet."""
    return np.zeros((160, 160, 3), dtype=np.uint8)


# ---------------------------------------------------------------------------
# _ensure_facenet
# ---------------------------------------------------------------------------

class TestEnsureFacenet:
    def test_returns_true_if_already_loaded(self, svc):
        svc.facenet = MagicMock()
        assert svc._ensure_facenet() is True

    def test_skips_reinit_if_already_loaded(self, svc):
        svc.facenet = MagicMock()
        with patch("website.services.face_service.FaceService._ensure_facenet",
                   wraps=svc._ensure_facenet):
            # If facenet is set, FaceNet() constructor must not be called
            with patch("keras_facenet.FaceNet") as mock_fn:
                svc._ensure_facenet()
                mock_fn.assert_not_called()

    def test_returns_false_on_import_error(self, svc):
        svc.facenet = None
        with patch.dict("sys.modules", {"keras_facenet": None}):
            result = svc._ensure_facenet()
            assert result is False


# ---------------------------------------------------------------------------
# get_embedding
# ---------------------------------------------------------------------------

class TestGetEmbedding:
    def test_raises_runtime_error_when_facenet_unavailable(self, svc):
        with patch.object(svc, "_ensure_facenet", return_value=False):
            with pytest.raises(RuntimeError, match="FaceNet model is unavailable"):
                svc.get_embedding(_fake_face_pixels())

    def test_calls_facenet_embeddings(self, svc_with_facenet):
        fake_embedding = np.ones(128, dtype=np.float32)
        svc_with_facenet.facenet.embeddings.return_value = np.array([fake_embedding])

        result = svc_with_facenet.get_embedding(_fake_face_pixels())

        svc_with_facenet.facenet.embeddings.assert_called_once()
        assert result.shape == (128,)


# ---------------------------------------------------------------------------
# get_face
# ---------------------------------------------------------------------------

class TestGetFace:
    def _make_haar_mock(self, detections):
        """Return (mock_cv2, mock_cascade) where cascade.detectMultiScale returns detections."""
        mock_cascade = MagicMock()
        mock_cascade.detectMultiScale.return_value = detections
        mock_cv2 = MagicMock()
        return mock_cv2, mock_cascade

    def test_returns_none_when_no_face_detected(self, svc):
        mock_cv2, mock_cascade = self._make_haar_mock([])
        with patch.object(svc, "_ensure_haar", return_value=(mock_cv2, mock_cascade)):
            image = np.zeros((200, 200, 3), dtype=np.uint8)
            face, x1, x2, y1, y2 = svc.get_face(image)
        assert face is None
        assert (x1, x2, y1, y2) == (0, 0, 0, 0)

    def test_returns_face_when_detected(self, svc):
        # Simulate a face detection at (10, 20, 50, 60) → x,y,w,h
        mock_cv2, mock_cascade = self._make_haar_mock([(10, 20, 50, 60)])
        with patch.object(svc, "_ensure_haar", return_value=(mock_cv2, mock_cascade)):
            image = np.zeros((200, 200, 3), dtype=np.uint8)
            face, x1, x2, y1, y2 = svc.get_face(image)
        assert face is not None
        # x2 = x1 + width = 10 + 50 = 60
        assert x2 == 60
        # y2 = y1 + height = 20 + 60 = 80
        assert y2 == 80


# ---------------------------------------------------------------------------
# extract_face
# ---------------------------------------------------------------------------

class TestExtractFace:
    def test_returns_none_for_missing_file(self, svc):
        with patch.object(svc, "_cv2") as mock_cv2_fn:
            mock_cv2 = MagicMock()
            mock_cv2.imread.return_value = None  # simulate missing file
            mock_cv2_fn.return_value = mock_cv2
            result = svc.extract_face("/nonexistent/file.jpg")
        assert result is None

    def test_returns_none_when_no_face_in_image(self, svc):
        fake_image = np.zeros((200, 200, 3), dtype=np.uint8)
        mock_cascade = MagicMock()
        mock_cascade.detectMultiScale.return_value = []  # no faces

        with patch.object(svc, "_cv2") as mock_cv2_fn:
            mock_cv2 = MagicMock()
            mock_cv2.imread.return_value = fake_image
            mock_cv2_fn.return_value = mock_cv2
            with patch.object(svc, "_ensure_haar", return_value=(mock_cv2, mock_cascade)):
                result = svc.extract_face("/some/image.jpg")
        assert result is None


# ---------------------------------------------------------------------------
# recognize_face
# ---------------------------------------------------------------------------

class TestRecognizeFace:
    def test_returns_none_when_model_not_loaded(self, svc, app):
        with app.app_context():
            # model is None and load_trained_model returns False
            with patch.object(svc, "load_trained_model", return_value=False):
                identity, confidence = svc.recognize_face(_fake_face_pixels())
            assert identity is None
            assert confidence == 0.0

    def test_returns_none_when_confidence_below_threshold(self, svc, app):
        with app.app_context():
            svc.facenet = MagicMock()
            svc.facenet.embeddings.return_value = np.array([np.ones(128)])
            svc.model = MagicMock()
            svc.label_encoder = MagicMock()
            svc.normalizer = MagicMock()

            # Confidence below default threshold (0.85)
            svc.model.predict.return_value = np.array([0])
            svc.model.predict_proba.return_value = np.array([[0.5]])
            svc.normalizer.transform.return_value = np.array([np.ones(128)])
            svc.label_encoder.inverse_transform.return_value = np.array(["stud1"])

            identity, confidence = svc.recognize_face(_fake_face_pixels(), confidence_threshold=0.85)
            assert identity is None
            assert abs(confidence - 0.5) < 1e-5

    def test_returns_identity_when_confidence_above_threshold(self, svc, app):
        with app.app_context():
            svc.facenet = MagicMock()
            svc.facenet.embeddings.return_value = np.array([np.ones(128)])
            svc.model = MagicMock()
            svc.label_encoder = MagicMock()
            svc.normalizer = MagicMock()

            svc.model.predict.return_value = np.array([0])
            svc.model.predict_proba.return_value = np.array([[0.95]])
            svc.normalizer.transform.return_value = np.array([np.ones(128)])
            svc.label_encoder.inverse_transform.return_value = np.array(["stud1"])

            identity, confidence = svc.recognize_face(_fake_face_pixels(), confidence_threshold=0.85)
            assert identity == "stud1"
            assert abs(confidence - 0.95) < 1e-5


# ---------------------------------------------------------------------------
# save_face_image
# ---------------------------------------------------------------------------

class TestSaveFaceImage:
    def test_returns_relative_path_on_success(self, svc, app, tmp_path):
        with app.app_context():
            app.config["FACES_DB_PATH"] = tmp_path

            with patch.object(svc, "_cv2") as mock_cv2_fn:
                mock_cv2 = MagicMock()
                mock_cv2.imwrite.return_value = True
                mock_cv2_fn.return_value = mock_cv2

                result = svc.save_face_image("stud1", _fake_face_pixels(), 0, is_training=True)

            assert result is not None
            assert "stud1" in result
            assert result.startswith("train/")

    def test_returns_none_on_write_failure(self, svc, app, tmp_path):
        with app.app_context():
            app.config["FACES_DB_PATH"] = tmp_path

            with patch.object(svc, "_cv2") as mock_cv2_fn:
                mock_cv2 = MagicMock()
                mock_cv2.imwrite.side_effect = OSError("disk full")
                mock_cv2_fn.return_value = mock_cv2

                result = svc.save_face_image("stud1", _fake_face_pixels(), 0, is_training=True)

            assert result is None
