import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import json
import base64

from app.services.email_service import EmailService
from app.services.oauth_service import OAuthService
from app.core.config import settings


class TestEmailService:
    @pytest.fixture
    def email_service(self):
        return EmailService()
    
    @patch("app.services.email_service.aiosmtplib.SMTP")
    async def test_send_email_plain_text(self, mock_smtp, email_service):
        """Test sending plain text email"""
        mock_smtp_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
        
        result = await email_service.send_email(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body"
        )
        
        assert result["status"] == "sent"
        assert result["recipients"] == ["recipient@example.com"]
        mock_smtp_instance.login.assert_called_once()
        mock_smtp_instance.send_message.assert_called_once()
    
    @patch("app.services.email_service.aiosmtplib.SMTP")
    async def test_send_email_with_html(self, mock_smtp, email_service):
        """Test sending email with HTML content"""
        mock_smtp_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
        
        result = await email_service.send_email(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
            html="<h1>Test Body</h1>"
        )
        
        assert result["status"] == "sent"
        mock_smtp_instance.send_message.assert_called_once()
        
        # Check that the message has both plain and HTML parts
        sent_message = mock_smtp_instance.send_message.call_args[0][0]
        assert sent_message.get_content_type() == "multipart/alternative"
    
    @patch("app.services.email_service.httpx.AsyncClient")
    async def test_sync_gmail_full_sync(self, mock_httpx, email_service):
        """Test Gmail full sync (no previous sync token)"""
        mock_client = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        # Mock message list response
        mock_client.get.side_effect = [
            # First call: message list
            MagicMock(
                status_code=200,
                json=lambda: {
                    "messages": [{"id": "msg123"}]
                }
            ),
            # Second call: message details
            MagicMock(
                status_code=200,
                json=lambda: {
                    "id": "msg123",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Test Email"},
                            {"name": "From", "value": "sender@example.com"},
                            {"name": "To", "value": "recipient@example.com"},
                            {"name": "Date", "value": "2024-01-01"}
                        ],
                        "body": {
                            "data": base64.urlsafe_b64encode(b"Test body").decode()
                        }
                    },
                    "snippet": "Test snippet"
                }
            ),
            # Third call: profile for history ID
            MagicMock(
                status_code=200,
                json=lambda: {"historyId": "12345"}
            )
        ]
        
        result = await email_service.sync_gmail(access_token="test_token")
        
        assert len(result["messages"]) == 1
        assert result["messages"][0]["id"] == "msg123"
        assert result["messages"][0]["subject"] == "Test Email"
        assert result["messages"][0]["from"] == "sender@example.com"
        assert result["nextSyncToken"] == "12345"
    
    @patch("app.services.email_service.httpx.AsyncClient")
    async def test_sync_gmail_incremental(self, mock_httpx, email_service):
        """Test Gmail incremental sync with sync token"""
        mock_client = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "messages": [],
                "historyId": "12346"
            }
        )
        
        result = await email_service.sync_gmail(
            access_token="test_token",
            last_sync_token="12345"
        )
        
        assert len(result["messages"]) == 0
        assert result["nextSyncToken"] == "12346"
        
        # Verify history API was used
        call_args = mock_client.get.call_args[0][0]
        assert "history" in call_args
    
    @patch("app.services.email_service.httpx.AsyncClient")
    async def test_sync_outlook(self, mock_httpx, email_service):
        """Test Outlook/Office 365 sync"""
        mock_client = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "value": [
                    {
                        "id": "msg456",
                        "subject": "Outlook Test",
                        "from": {
                            "emailAddress": {"address": "sender@outlook.com"}
                        },
                        "toRecipients": [
                            {"emailAddress": {"address": "recipient@outlook.com"}}
                        ],
                        "receivedDateTime": "2024-01-01T00:00:00Z",
                        "body": {"content": "Test body"},
                        "bodyPreview": "Test preview"
                    }
                ],
                "@odata.deltaLink": "https://graph.microsoft.com/delta?token=new"
            }
        )
        
        result = await email_service.sync_outlook(access_token="test_token")
        
        assert len(result["messages"]) == 1
        assert result["messages"][0]["id"] == "msg456"
        assert result["messages"][0]["subject"] == "Outlook Test"
        assert result["messages"][0]["from"] == "sender@outlook.com"
        assert result["deltaLink"] == "https://graph.microsoft.com/delta?token=new"


class TestOAuthService:
    @pytest.fixture
    def oauth_service(self):
        return OAuthService()
    
    def test_token_encryption_decryption(self, oauth_service):
        """Test token encryption and decryption"""
        original_token = "test_refresh_token_12345"
        
        encrypted = oauth_service.encrypt_token(original_token)
        decrypted = oauth_service.decrypt_token(encrypted)
        
        assert encrypted != original_token
        assert decrypted == original_token
    
    @patch("app.services.oauth_service.httpx.AsyncClient")
    async def test_refresh_google_token(self, mock_httpx, oauth_service):
        """Test refreshing Google OAuth token"""
        mock_client = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        mock_client.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "new_access_token",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
        )
        
        # Encrypt a test refresh token
        encrypted_token = oauth_service.encrypt_token("test_refresh_token")
        
        result = await oauth_service.refresh_token(
            refresh_token=encrypted_token,
            provider="google"
        )
        
        assert result["access_token"] == "new_access_token"
        assert result["expires_in"] == 3600
        assert "expires_at" in result
        
        # Verify API call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "oauth2.googleapis.com/token" in call_args[0][0]
        assert call_args[1]["data"]["refresh_token"] == "test_refresh_token"
    
    @patch("app.services.oauth_service.httpx.AsyncClient")
    async def test_refresh_microsoft_token(self, mock_httpx, oauth_service):
        """Test refreshing Microsoft OAuth token"""
        mock_client = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        mock_client.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "new_ms_token",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
        )
        
        encrypted_token = oauth_service.encrypt_token("ms_refresh_token")
        
        result = await oauth_service.refresh_token(
            refresh_token=encrypted_token,
            provider="microsoft"
        )
        
        assert result["access_token"] == "new_ms_token"
        assert "login.microsoftonline.com" in mock_client.post.call_args[0][0]
    
    @patch("app.services.oauth_service.httpx.AsyncClient")
    async def test_exchange_google_code(self, mock_httpx, oauth_service):
        """Test exchanging Google authorization code for tokens"""
        mock_client = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        # Mock token exchange response
        mock_client.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "google_access",
                "refresh_token": "google_refresh",
                "expires_in": 3600
            }
        )
        
        # Mock user info response
        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "email": "user@gmail.com",
                "name": "Test User"
            }
        )
        
        result = await oauth_service.exchange_code(
            code="auth_code_123",
            provider="google",
            redirect_uri="http://localhost:3000/callback"
        )
        
        assert result["access_token"] == "google_access"
        assert result["email"] == "user@gmail.com"
        assert result["name"] == "Test User"
        assert result["provider"] == "google"
        
        # Verify refresh token was encrypted
        assert result["refresh_token"] != "google_refresh"
        decrypted = oauth_service.decrypt_token(result["refresh_token"])
        assert decrypted == "google_refresh"
    
    async def test_unsupported_provider(self, oauth_service):
        """Test error handling for unsupported provider"""
        encrypted_token = oauth_service.encrypt_token("some_token")
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            await oauth_service.refresh_token(
                refresh_token=encrypted_token,
                provider="unsupported"
            )
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            await oauth_service.exchange_code(
                code="code",
                provider="unsupported",
                redirect_uri="http://localhost"
            )