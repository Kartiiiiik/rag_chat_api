import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from app.services.embedding_service import SentenceTransformerService

@pytest.fixture
def mock_sentence_transformer():
    with patch("app.services.embedding_service.SentenceTransformer") as mock:
        yield mock

def test_singleton_pattern(mock_sentence_transformer):
    service1 = SentenceTransformerService()
    service2 = SentenceTransformerService()
    assert service1 is service2

def test_get_embedding_success(mock_sentence_transformer):
    # Setup mock
    mock_model_instance = mock_sentence_transformer.return_value
    expected_embedding = np.array([0.1, 0.2, 0.3])
    mock_model_instance.encode.return_value = expected_embedding
    
    service = SentenceTransformerService()
    # Reset instance to ensure fresh mock usage if needed, but singleton persists. 
    # For testing simpler to just rely on the mock returned by init if not already loaded, 
    # but since singleton, we might need to be careful. 
    # However, patch handles the import.
    
    result = service.get_embedding("test text")
    
    assert result == [0.1, 0.2, 0.3]
    mock_model_instance.encode.assert_called_with("test text", convert_to_tensor=False)

def test_get_embedding_empty_text():
    service = SentenceTransformerService()
    with pytest.raises(ValueError, match="Cannot embed empty text"):
        service.get_embedding("")

def test_get_embeddings_batch_success(mock_sentence_transformer):
    mock_model_instance = mock_sentence_transformer.return_value
    expected_embeddings = np.array([[0.1, 0.1], [0.2, 0.2]])
    mock_model_instance.encode.return_value = expected_embeddings
    
    service = SentenceTransformerService()
    result = service.get_embeddings(["text1", "text2"])
    
    assert result == [[0.1, 0.1], [0.2, 0.2]]
    mock_model_instance.encode.assert_called_with(
        ["text1", "text2"], 
        batch_size=32, 
        convert_to_tensor=False, 
        show_progress_bar=False
    )

def test_get_embeddings_fallback(mock_sentence_transformer):
    mock_model_instance = mock_sentence_transformer.return_value
    
    # Simulate batch failure
    mock_model_instance.encode.side_effect = [
        RuntimeError("Batch failed"), # First call (batch)
        np.array([1.0]),              # Second call (fallback item 1)
        np.array([2.0])               # Third call (fallback item 2)
    ]
    
    service = SentenceTransformerService()
    result = service.get_embeddings(["t1", "t2"])
    
    assert result == [[1.0], [2.0]]
