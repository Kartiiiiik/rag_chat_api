import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import sys
import os

# Add backend to sys.path to allow importing app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.dependencies import get_db

client = TestClient(app)

@pytest.fixture
def mock_db():
    mock = MagicMock()
    # Mock query response for existing document check
    mock.query.return_value.filter_by.return_value.first.return_value = None
    
    # Simulate refresh setting the ID
    def side_effect_refresh(instance):
        instance.id = 1
        instance.created_at = "2024-01-01T00:00:00" # Mock date if needed
        
    mock.refresh.side_effect = side_effect_refresh
    return mock

@pytest.fixture
def override_dependencies(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}

@pytest.fixture
    # Mock the embedding service
    mock_service = MagicMock()
    # Mocking single embedding
    mock_service.get_embedding.return_value = [0.1] * 384
    # Mocking batch embeddings
    mock_service.get_embeddings.side_effect = lambda texts, **kwargs: [[0.1] * 384] * len(texts)
    
    # Patch get_embedding_service in router_documents
    monkeypatch.setattr("app.api.v1.router_documents.get_embedding_service", lambda: mock_service)
    
    # Also patch in rag_service if it's used there (though this test might only cover upload)
    monkeypatch.setattr("app.services.rag_service.get_embedding_service", lambda: mock_service)
    
    return mock_service

def test_upload_document_success(override_dependencies, mock_embedding_service, mock_db):
    filename = "test_doc.txt"
    content = b"This is a dummy test content for verifying the fix."
    files = {"file": (filename, content, "text/plain")}
    
    response = client.post("/documents/upload", files=files)
    
    # If we get 200, the await error is gone
    assert response.status_code == 200, f"Upload failed with status {response.status_code}: {response.json()}"
    data = response.json()
    assert data["filename"] == filename
    assert "id" in data
