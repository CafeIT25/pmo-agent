import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    return MagicMock(id="user123", email="test@example.com")


class TestEmailEndpoints:
    @patch("app.api.v1.endpoints.email.get_current_user")
    @patch("app.api.v1.endpoints.email.sync_emails")
    async def test_start_email_sync(self, mock_sync_emails, mock_get_user, client, auth_headers, mock_current_user):
        """Test starting email sync"""
        mock_get_user.return_value = mock_current_user
        mock_sync_emails.delay.return_value = MagicMock(id="job123")
        
        response = await client.post(
            "/api/v1/email/sync",
            json={"account_id": "account123"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job123"
        mock_sync_emails.delay.assert_called_once_with(
            user_id="user123",
            account_id="account123"
        )
    
    @patch("app.api.v1.endpoints.email.get_current_user")
    @patch("app.api.v1.endpoints.email.AsyncResult")
    async def test_get_sync_job_status_pending(self, mock_async_result, mock_get_user, client, auth_headers, mock_current_user):
        """Test getting sync job status - pending"""
        mock_get_user.return_value = mock_current_user
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mock_async_result.return_value = mock_result
        
        response = await client.get(
            "/api/v1/email/sync/job123",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "job123"
        assert data["status"] == "pending"
        assert data["processed_emails"] == 0
    
    @patch("app.api.v1.endpoints.email.get_current_user")
    @patch("app.api.v1.endpoints.email.AsyncResult")
    async def test_get_sync_job_status_success(self, mock_async_result, mock_get_user, client, auth_headers, mock_current_user):
        """Test getting sync job status - success"""
        mock_get_user.return_value = mock_current_user
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "account_id": "account123",
            "processed_emails": 10,
            "total_emails": 10
        }
        mock_async_result.return_value = mock_result
        
        response = await client.get(
            "/api/v1/email/sync/job123",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["processed_emails"] == 10
        assert data["total_emails"] == 10
    
    @patch("app.api.v1.endpoints.email.get_current_user")
    @patch("app.api.v1.endpoints.email.AsyncResult")
    async def test_get_sync_job_status_failure(self, mock_async_result, mock_get_user, client, auth_headers, mock_current_user):
        """Test getting sync job status - failure"""
        mock_get_user.return_value = mock_current_user
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.info = Exception("Sync failed")
        mock_async_result.return_value = mock_result
        
        response = await client.get(
            "/api/v1/email/sync/job123",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "Sync failed" in data["error_message"]


class TestAIEndpoints:
    @patch("app.api.v1.endpoints.ai.get_current_user")
    @patch("app.api.v1.endpoints.ai.generate_task_suggestions")
    async def test_request_task_suggestions(self, mock_generate, mock_get_user, client, auth_headers, mock_current_user):
        """Test requesting task suggestions"""
        mock_get_user.return_value = mock_current_user
        mock_generate.delay.return_value = MagicMock(id="ai_job123")
        
        response = await client.post(
            "/api/v1/ai/task-suggestions",
            json={
                "task_id": "task123",
                "context": "Need help with this task"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "ai_job123"
        assert data["status"] == "queued"
        mock_generate.delay.assert_called_once_with(
            task_id="task123",
            context="Need help with this task"
        )
    
    @patch("app.api.v1.endpoints.ai.get_current_user")
    @patch("app.api.v1.endpoints.ai.summarize_email_thread")
    async def test_request_email_thread_summary(self, mock_summarize, mock_get_user, client, auth_headers, mock_current_user):
        """Test requesting email thread summary"""
        mock_get_user.return_value = mock_current_user
        mock_summarize.delay.return_value = MagicMock(id="ai_job456")
        
        response = await client.post(
            "/api/v1/ai/email-thread-summary",
            json={
                "email_ids": ["email1", "email2", "email3"]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "ai_job456"
        mock_summarize.delay.assert_called_once_with(
            email_ids=["email1", "email2", "email3"]
        )
    
    @patch("app.api.v1.endpoints.ai.get_current_user")
    @patch("app.api.v1.endpoints.ai.AsyncResult")
    async def test_get_ai_job_status(self, mock_async_result, mock_get_user, client, auth_headers, mock_current_user):
        """Test getting AI job status"""
        mock_get_user.return_value = mock_current_user
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "suggestions": {
                "action_plan": ["Step 1", "Step 2"],
                "time_estimate": "2 hours"
            }
        }
        mock_async_result.return_value = mock_result
        
        response = await client.get(
            "/api/v1/ai/job/ai_job123",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "ai_job123"
        assert data["status"] == "completed"
        assert data["result"]["suggestions"]["action_plan"] == ["Step 1", "Step 2"]


class TestOAuthEndpoints:
    async def test_google_authorize(self, client):
        """Test Google OAuth authorization redirect"""
        response = await client.get(
            "/api/v1/oauth/google/authorize",
            params={"redirect_uri": "http://localhost:3000/auth/callback"},
            follow_redirects=False
        )
        
        assert response.status_code == 307
        location = response.headers["location"]
        assert "accounts.google.com" in location
        assert "client_id=" in location
        assert "redirect_uri=http://localhost:3000/auth/callback" in location
        assert "scope=" in location
        assert "gmail.readonly" in location
    
    async def test_microsoft_authorize(self, client):
        """Test Microsoft OAuth authorization redirect"""
        response = await client.get(
            "/api/v1/oauth/microsoft/authorize",
            params={"redirect_uri": "http://localhost:3000/auth/callback"},
            follow_redirects=False
        )
        
        assert response.status_code == 307
        location = response.headers["location"]
        assert "login.microsoftonline.com" in location
        assert "client_id=" in location
        assert "redirect_uri=http://localhost:3000/auth/callback" in location
        assert "scope=" in location
        assert "Mail.Read" in location
    
    @patch("app.api.v1.endpoints.oauth.OAuthService")
    @patch("app.api.v1.endpoints.oauth.get_db")
    @patch("app.api.v1.endpoints.oauth.crud_user")
    @patch("app.api.v1.endpoints.oauth.crud_email")
    async def test_google_callback_new_user(self, mock_crud_email, mock_crud_user, mock_get_db, mock_oauth_service, client):
        """Test Google OAuth callback for new user"""
        # Mock OAuth service
        mock_oauth_service.return_value.exchange_code = AsyncMock(
            return_value={
                "access_token": "access123",
                "refresh_token": "refresh123",
                "expires_in": 3600,
                "email": "newuser@example.com",
                "name": "New User",
                "provider": "google"
            }
        )
        
        # Mock user operations
        mock_crud_user.get_by_email = AsyncMock(return_value=None)
        mock_new_user = MagicMock(id="user123", email="newuser@example.com")
        mock_crud_user.create = AsyncMock(return_value=mock_new_user)
        
        # Mock email account creation
        mock_crud_email.create_email_account = AsyncMock(
            return_value=MagicMock(id="account123")
        )
        
        response = await client.get(
            "/api/v1/oauth/google/callback",
            params={
                "code": "auth_code_123",
                "redirect_uri": "http://localhost:3000/auth/callback"
            },
            follow_redirects=False
        )
        
        assert response.status_code == 307
        location = response.headers["location"]
        assert "http://localhost:3000/auth/callback" in location
        assert "token=" in location
        assert "email=newuser@example.com" in location
        
        # Verify user was created
        mock_crud_user.create.assert_called_once()
        mock_crud_email.create_email_account.assert_called_once()