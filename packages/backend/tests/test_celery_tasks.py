import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import json

from app.worker.tasks.email import sync_emails, analyze_email_for_tasks, send_email
from app.worker.tasks.ai import analyze_email_with_ai, generate_task_suggestions, summarize_email_thread


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock()
    db.__aenter__ = AsyncMock(return_value=db)
    db.__aexit__ = AsyncMock(return_value=None)
    return db


@pytest.fixture
def mock_email_account():
    """Mock email account"""
    return MagicMock(
        id="account123",
        user_id="user123",
        email="test@example.com",
        provider="google",
        refresh_token="encrypted_token",
        last_sync_token="sync123"
    )


@pytest.fixture
def mock_processed_email():
    """Mock processed email"""
    return MagicMock(
        id="email123",
        subject="Test Email",
        sender="sender@example.com",
        body="This is a test email body",
        received_at=datetime.utcnow()
    )


class TestEmailTasks:
    @patch("app.worker.tasks.email.get_db")
    @patch("app.worker.tasks.email.crud_email")
    @patch("app.worker.tasks.email.OAuthService")
    @patch("app.worker.tasks.email.EmailService")
    def test_sync_emails_success(self, mock_email_service, mock_oauth_service, mock_crud, mock_get_db, mock_db, mock_email_account):
        """Test successful email sync"""
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_crud.get_email_account = AsyncMock(return_value=mock_email_account)
        mock_crud.get_email_by_message_id = AsyncMock(return_value=None)
        mock_crud.create_processed_email = AsyncMock(return_value=MagicMock(id="processed123"))
        mock_crud.update_sync_token = AsyncMock()
        
        mock_oauth_service.return_value.refresh_token = AsyncMock(
            return_value={"access_token": "new_token", "expires_in": 3600}
        )
        
        mock_email_service.return_value.sync_gmail = AsyncMock(
            return_value={
                "messages": [
                    {
                        "id": "msg123",
                        "subject": "Test Email",
                        "from": "sender@example.com",
                        "to": ["recipient@example.com"],
                        "date": "2024-01-01T00:00:00Z",
                        "body": "Test body"
                    }
                ],
                "nextSyncToken": "new_sync_token"
            }
        )
        
        # Execute
        result = sync_emails("user123", "account123")
        
        # Assert
        assert result["status"] == "completed"
        assert result["processed_emails"] == 1
        assert result["sync_token_updated"] == True
        mock_crud.update_sync_token.assert_called_once()
    
    @patch("app.worker.tasks.email.get_db")
    @patch("app.worker.tasks.email.crud_email")
    def test_sync_emails_account_not_found(self, mock_crud, mock_get_db, mock_db):
        """Test email sync with non-existent account"""
        mock_get_db.return_value = mock_db
        mock_crud.get_email_account = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Email account .* not found"):
            sync_emails("user123", "invalid_account")
    
    @patch("app.worker.tasks.email.analyze_email_with_ai")
    def test_analyze_email_for_tasks(self, mock_ai_task):
        """Test email analysis task delegation"""
        mock_ai_task.apply_async.return_value = MagicMock(id="ai_task_123")
        
        result = analyze_email_for_tasks("email123", "user123")
        
        assert result["email_id"] == "email123"
        assert result["ai_task_id"] == "ai_task_123"
        assert result["status"] == "queued_for_ai_analysis"
        mock_ai_task.apply_async.assert_called_once_with(
            args=["email123", "user123"],
            queue="ai"
        )
    
    @patch("app.worker.tasks.email.EmailService")
    def test_send_email_success(self, mock_email_service):
        """Test successful email sending"""
        mock_email_service.return_value.send_email = AsyncMock(
            return_value={"status": "sent", "recipients": ["test@example.com"]}
        )
        
        result = send_email(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test Body",
            user_id="user123"
        )
        
        assert result["status"] == "sent"
        assert result["recipients"] == ["test@example.com"]
        mock_email_service.return_value.send_email.assert_called_once()


class TestAITasks:
    @patch("app.worker.tasks.ai.get_db")
    @patch("app.worker.tasks.ai.crud_email")
    @patch("app.worker.tasks.ai.crud_task")
    @patch("app.worker.tasks.ai.BedrockClient")
    def test_analyze_email_with_ai_creates_task(self, mock_bedrock, mock_crud_task, mock_crud_email, mock_get_db, mock_db, mock_processed_email):
        """Test AI email analysis that creates a task"""
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_crud_email.get_processed_email = AsyncMock(return_value=mock_processed_email)
        mock_crud_email.update_email_analysis = AsyncMock()
        
        mock_bedrock.return_value.invoke_model = AsyncMock(
            return_value=json.dumps({
                "is_task": True,
                "tasks": [{
                    "title": "Follow up on test email",
                    "description": "Need to respond to the test email",
                    "priority": "high",
                    "due_date": None,
                    "tags": ["email", "followup"]
                }],
                "summary": "Test email requiring action",
                "sentiment": "neutral",
                "key_points": ["Action required"]
            })
        )
        
        mock_crud_task.create_task = AsyncMock(
            return_value=MagicMock(id="task123")
        )
        
        # Execute
        result = analyze_email_with_ai("email123", "user123")
        
        # Assert
        assert result["is_task"] == True
        assert result["tasks_created"] == 1
        assert result["task_ids"] == ["task123"]
        assert result["summary"] == "Test email requiring action"
        mock_crud_email.update_email_analysis.assert_called_once()
        mock_crud_task.create_task.assert_called_once()
    
    @patch("app.worker.tasks.ai.get_db")
    @patch("app.worker.tasks.ai.crud_email")
    @patch("app.worker.tasks.ai.BedrockClient")
    def test_analyze_email_with_ai_no_task(self, mock_bedrock, mock_crud_email, mock_get_db, mock_db, mock_processed_email):
        """Test AI email analysis that doesn't create a task"""
        mock_get_db.return_value = mock_db
        mock_crud_email.get_processed_email = AsyncMock(return_value=mock_processed_email)
        mock_crud_email.update_email_analysis = AsyncMock()
        
        mock_bedrock.return_value.invoke_model = AsyncMock(
            return_value=json.dumps({
                "is_task": False,
                "tasks": [],
                "summary": "Informational email only",
                "sentiment": "positive",
                "key_points": ["No action needed"]
            })
        )
        
        result = analyze_email_with_ai("email123", "user123")
        
        assert result["is_task"] == False
        assert result["tasks_created"] == 0
        assert result["task_ids"] == []
    
    @patch("app.worker.tasks.ai.get_db")
    @patch("app.worker.tasks.ai.crud_task")
    @patch("app.worker.tasks.ai.BedrockClient")
    def test_generate_task_suggestions(self, mock_bedrock, mock_crud_task, mock_get_db, mock_db):
        """Test task suggestion generation"""
        mock_get_db.return_value = mock_db
        mock_task = MagicMock(
            id="task123",
            title="Test Task",
            description="Test Description",
            priority="medium",
            status="pending"
        )
        mock_crud_task.get_task = AsyncMock(return_value=mock_task)
        mock_crud_task.create_ai_support = AsyncMock(
            return_value=MagicMock(id="support123")
        )
        
        mock_bedrock.return_value.invoke_model = AsyncMock(
            return_value=json.dumps({
                "action_plan": ["Step 1", "Step 2"],
                "blockers": ["Potential blocker"],
                "resources": ["Resource 1"],
                "time_estimate": "2 hours",
                "references": []
            })
        )
        
        result = generate_task_suggestions("task123", "Additional context")
        
        assert result["task_id"] == "task123"
        assert result["ai_support_id"] == "support123"
        assert "action_plan" in result["suggestions"]
        mock_crud_task.create_ai_support.assert_called_once()
    
    @patch("app.worker.tasks.ai.get_db")
    @patch("app.worker.tasks.ai.crud_email")
    @patch("app.worker.tasks.ai.BedrockClient")
    def test_summarize_email_thread(self, mock_bedrock, mock_crud_email, mock_get_db, mock_db):
        """Test email thread summarization"""
        mock_get_db.return_value = mock_db
        
        # Mock emails
        mock_emails = [
            MagicMock(
                sender="user1@example.com",
                received_at=datetime(2024, 1, 1, 10, 0),
                subject="Thread Start",
                body="Initial message"
            ),
            MagicMock(
                sender="user2@example.com",
                received_at=datetime(2024, 1, 1, 11, 0),
                subject="Re: Thread Start",
                body="Reply message"
            )
        ]
        
        mock_crud_email.get_processed_email = AsyncMock(side_effect=mock_emails)
        
        mock_bedrock.return_value.invoke_model = AsyncMock(
            return_value=json.dumps({
                "executive_summary": "Discussion about project timeline",
                "decisions": ["Agreed on deadline"],
                "action_items": ["Complete task by Friday"],
                "participants": ["user1", "user2"],
                "next_steps": ["Review progress"]
            })
        )
        
        result = summarize_email_thread(["email1", "email2"])
        
        assert result["thread_size"] == 2
        assert "executive_summary" in result["summary"]
        assert result["summary"]["executive_summary"] == "Discussion about project timeline"