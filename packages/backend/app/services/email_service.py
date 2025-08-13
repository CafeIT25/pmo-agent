import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
import httpx
import base64
import re
import hashlib
from datetime import datetime

from app.core.config import settings


class EmailService:
    """Email service for sending and receiving emails"""
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email via SMTP
        
        Args:
            to: List of recipient emails
            subject: Email subject
            body: Plain text body
            html: Optional HTML body
            
        Returns:
            Dict with send status
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        message["To"] = ", ".join(to)
        
        # Add plain text part
        text_part = MIMEText(body, "plain")
        message.attach(text_part)
        
        # Add HTML part if provided
        if html:
            html_part = MIMEText(html, "html")
            message.attach(html_part)
        
        # Send email
        async with aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=settings.SMTP_TLS
        ) as smtp:
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            await smtp.send_message(message)
        
        return {
            "status": "sent",
            "recipients": to,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def sync_gmail(
        self,
        access_token: str,
        last_sync_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync emails from Gmail
        
        Args:
            access_token: OAuth access token
            last_sync_token: Previous sync token for incremental sync
            
        Returns:
            Dict with emails and next sync token
        """
        async with httpx.AsyncClient() as client:
            # Build query
            params = {
                "maxResults": 50,
                "includeSpamTrash": False
            }
            
            if last_sync_token:
                # Use history API for incremental sync
                url = "https://gmail.googleapis.com/gmail/v1/users/me/history"
                params["startHistoryId"] = last_sync_token
            else:
                # Full sync
                url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
                params["q"] = "is:unread"
            
            # Get message list
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            # Get full message details
            messages = []
            message_ids = data.get("messages", [])
            
            for msg in message_ids:
                msg_response = await client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                    params={"format": "full"},
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                msg_response.raise_for_status()
                msg_data = msg_response.json()
                
                # Parse message
                parsed = self._parse_gmail_message(msg_data)
                messages.append(parsed)
            
            # Get next sync token
            if "historyId" in data:
                next_token = data["historyId"]
            else:
                # Get current history ID for next sync
                profile_response = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/profile",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                profile_response.raise_for_status()
                next_token = profile_response.json()["historyId"]
            
            return {
                "messages": messages,
                "nextSyncToken": str(next_token)
            }
    
    async def sync_outlook(
        self,
        access_token: str,
        last_sync_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync emails from Outlook/Office 365
        
        Args:
            access_token: OAuth access token
            last_sync_token: Previous delta link for incremental sync
            
        Returns:
            Dict with emails and next delta link
        """
        async with httpx.AsyncClient() as client:
            # Use delta query for incremental sync
            if last_sync_token:
                url = last_sync_token
            else:
                url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages/delta"
                url += "?$select=id,subject,from,toRecipients,body,receivedDateTime"
            
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse messages
            messages = []
            for msg in data.get("value", []):
                parsed = self._parse_outlook_message(msg)
                messages.append(parsed)
            
            # Get next delta link
            next_link = data.get("@odata.deltaLink", data.get("@odata.nextLink"))
            
            return {
                "messages": messages,
                "deltaLink": next_link
            }
    
    def _parse_gmail_message(self, msg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message format"""
        headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
        
        # Extract body
        body = ""
        if "parts" in msg_data["payload"]:
            for part in msg_data["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break
        elif msg_data["payload"].get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode("utf-8")
        
        # スレッド情報を抽出
        message_id = headers.get("Message-ID", "")
        in_reply_to = headers.get("In-Reply-To", "")
        references = headers.get("References", "")
        
        # スレッドIDの生成
        # 1. In-Reply-To がある場合は、それが属するスレッドのID
        # 2. なければ、件名ベースでスレッドIDを生成
        subject = headers.get("Subject", "")
        clean_subject = re.sub(r'^(Re:|Fwd:|FW:)\s*', '', subject, flags=re.IGNORECASE).strip()
        
        if in_reply_to:
            # 返信メールの場合、親メールのMessage-IDをスレッドIDとする
            thread_id = in_reply_to.strip("<>")
        elif references:
            # References の最初のメッセージIDをスレッドIDとする
            first_ref = references.split()[0] if references else ""
            thread_id = first_ref.strip("<>")
        else:
            # 新規スレッドの場合、Message-IDをスレッドIDとする
            thread_id = message_id.strip("<>") if message_id else hashlib.md5(clean_subject.encode()).hexdigest()
        
        return {
            "id": msg_data["id"],
            "subject": subject,
            "from": headers.get("From", ""),
            "to": headers.get("To", "").split(","),
            "date": headers.get("Date", ""),
            "body": body,
            "snippet": msg_data.get("snippet", ""),
            "thread_id": thread_id,
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "references": references
        }
    
    def _parse_outlook_message(self, msg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Outlook message format"""
        
        # スレッド情報を抽出
        message_id = msg_data.get("internetMessageId", "")
        # Outlookでは conversationId がスレッドIDとして使える
        conversation_id = msg_data.get("conversationId", "")
        
        # OutlookのinternetMessageHeaders から In-Reply-To と References を取得
        headers = {}
        if "internetMessageHeaders" in msg_data:
            for header in msg_data["internetMessageHeaders"]:
                headers[header["name"]] = header["value"]
        
        in_reply_to = headers.get("In-Reply-To", "")
        references = headers.get("References", "")
        
        # スレッドIDの決定
        # Outlookの場合は conversationId を優先
        if conversation_id:
            thread_id = conversation_id
        elif in_reply_to:
            thread_id = in_reply_to.strip("<>")
        else:
            # 件名ベースでスレッドIDを生成
            subject = msg_data.get("subject", "")
            clean_subject = re.sub(r'^(Re:|Fwd:|FW:)\s*', '', subject, flags=re.IGNORECASE).strip()
            thread_id = message_id.strip("<>") if message_id else hashlib.md5(clean_subject.encode()).hexdigest()
        
        return {
            "id": msg_data["id"],
            "subject": msg_data.get("subject", ""),
            "from": msg_data.get("from", {}).get("emailAddress", {}).get("address", ""),
            "to": [r["emailAddress"]["address"] for r in msg_data.get("toRecipients", [])],
            "date": msg_data.get("receivedDateTime", ""),
            "body": msg_data.get("body", {}).get("content", ""),
            "snippet": msg_data.get("bodyPreview", ""),
            "thread_id": thread_id,
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "references": references
        }