"""
OpenAI API サービス
GPT-5-mini対応のコスト効率的なGPT API統合
"""
import os
from typing import List, Dict, Any, Optional
import json
import openai
from openai import OpenAI
from datetime import datetime
from .user_usage_tracker import UserUsageTracker

class OpenAIService:
    """
    OpenAI GPT APIを使用したタスク分析サービス
    """
    
    def __init__(self, db_session=None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")  # GPT-5-miniをデフォルトに
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
        self.verbosity = os.getenv("OPENAI_VERBOSITY", "low")
        self.reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT", "low")
        self.usage_tracker = UserUsageTracker(db_session) if db_session else None
        
    async def analyze_email_threads(
        self,
        email_threads: Dict[str, List[Dict]],
        existing_tasks: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        メールスレッドをバッチ分析してタスク化
        """
        # プロンプトの構築
        system_prompt = """
        あなたはプロジェクト管理を支援するAIアシスタントです。
        メール内容を分析して、以下を判定してください：
        1. 新規タスクとして作成すべきか
        2. 既存タスクの進捗更新が必要か
        3. タスクのステータス（todo/progress/done）
        
        重要な判定基準：
        - 「着手」「開始」「始めました」などの表現 → status: "progress"
        - 「完了」「終了」「できました」などの表現 → status: "done"
        - それ以外の新規依頼や質問 → status: "todo"
        """
        
        # スレッドごとの分析データ準備
        threads_data = []
        for thread_id, thread_emails in email_threads.items():
            # 既存タスクの検索
            existing_task = self._find_related_task(thread_emails, existing_tasks)
            
            threads_data.append({
                "thread_id": thread_id,
                "has_existing_task": existing_task is not None,
                "existing_task_title": existing_task.title if existing_task else None,
                "existing_task_status": existing_task.status if existing_task else None,
                "existing_task_id": str(existing_task.id) if existing_task else None,
                "emails_content": self._summarize_thread(thread_emails)
            })
        
        # ユーザープロンプトの作成
        user_prompt = f"""
        以下のメールスレッドを分析してください。
        
        {json.dumps(threads_data, ensure_ascii=False, indent=2)}
        
        各スレッドについて以下のJSON形式で回答してください：
        [
            {{
                "thread_id": "スレッドID",
                "action": "create" または "update" または "none",
                "title": "タスクタイトル（createの場合）",
                "description": "タスク説明（createの場合）",
                "status": "todo" または "progress" または "done",
                "priority": "high" または "medium" または "low",
                "task_id": "既存タスクID（updateの場合）",
                "summary": "状況の要約"
            }}
        ]
        """
        
        try:
            # GPT-5シリーズのAPIパラメータを構築
            api_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "response_format": {"type": "json_object"}
            }
            
            # GPT-5シリーズ固有のパラメータを追加
            if self.model.startswith("gpt-5"):
                api_params["verbosity"] = self.verbosity
                api_params["reasoning_effort"] = self.reasoning_effort
            
            # OpenAI API呼び出し
            response = self.client.chat.completions.create(**api_params)
            
            # ユーザー別使用量記録
            if self.usage_tracker:
                usage = response.usage
                # Note: user_id は呼び出し元から渡される必要がある
                # この部分は後でリファクタリングが必要
            
            # レスポンスの解析
            result_text = response.choices[0].message.content
            results = json.loads(result_text).get("results", [])
            
            # 結果の整形
            formatted_results = []
            for result in results:
                thread_id = result["thread_id"]
                thread_emails = email_threads.get(thread_id, [])
                
                if result["action"] == "create":
                    formatted_results.append({
                        "action": "create",
                        "task_data": {
                            "title": result["title"],
                            "description": result.get("description", ""),
                            "status": result.get("status", "todo"),
                            "priority": result.get("priority", "medium"),
                            "created_by": "ai",
                            "email_summary": self._create_email_summary(thread_emails),
                            "source_email_id": thread_emails[0].get("id") if thread_emails else None,
                            "source_email_link": self._generate_email_link(thread_emails[0]) if thread_emails else None
                        },
                        "source_emails": thread_emails
                    })
                elif result["action"] == "update":
                    formatted_results.append({
                        "action": "update",
                        "task_id": result["task_id"],
                        "updates": {
                            "status": result.get("status"),
                            "summary": result.get("summary", ""),
                            "updated_by": "ai",
                            "email_summary": self._create_email_summary(thread_emails)
                        },
                        "source_emails": thread_emails
                    })
            
            return formatted_results
            
        except Exception as e:
            error_message = str(e)
            print(f"OpenAI API error: {error_message}")
            
            # クレジット不足エラーのチェック
            if "insufficient_quota" in error_message.lower() or "exceeded your current quota" in error_message.lower():
                raise Exception("OPENAI_INSUFFICIENT_CREDITS")
            elif "rate_limit_exceeded" in error_message.lower():
                raise Exception("OPENAI_RATE_LIMIT")
            else:
                raise Exception(f"OPENAI_ERROR: {error_message}")
    
    async def investigate_task(self, task_data: Dict[str, Any]) -> str:
        """
        タスクに関する詳細調査
        """
        system_prompt = """
        あなたはプロジェクト管理の専門家です。
        与えられたタスクについて、実装方法、解決策、推奨アプローチを提案してください。
        技術的な内容の場合は、具体的なコード例やツールの提案も含めてください。
        """
        
        user_prompt = f"""
        以下のタスクについて調査・分析してください：
        
        タイトル: {task_data.get('title', '')}
        説明: {task_data.get('description', '')}
        メール要約: {task_data.get('email_summary', '')}
        
        以下の観点で分析してください：
        1. 実装・解決方法
        2. 必要なリソースやツール
        3. 推定作業時間
        4. 潜在的なリスクや注意点
        5. 推奨される次のステップ
        """
        
        try:
            # GPT-5シリーズのAPIパラメータを構築
            api_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,  # 創造性重視のため高め
                "max_tokens": self.max_tokens
            }
            
            # GPT-5シリーズ固有のパラメータを追加
            if self.model.startswith("gpt-5"):
                api_params["verbosity"] = self.verbosity
                api_params["reasoning_effort"] = self.reasoning_effort
            
            response = self.client.chat.completions.create(**api_params)
            
            # ユーザー別使用量記録
            if self.usage_tracker:
                usage = response.usage
                # Note: user_id は呼び出し元から渡される必要がある
                # この部分は後でリファクタリングが必要
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_message = str(e)
            
            # クレジット不足エラーのチェック
            if "insufficient_quota" in error_message.lower() or "exceeded your current quota" in error_message.lower():
                raise Exception("OPENAI_INSUFFICIENT_CREDITS")
            elif "rate_limit_exceeded" in error_message.lower():
                raise Exception("OPENAI_RATE_LIMIT")
            else:
                return f"調査中にエラーが発生しました: {error_message}"
    
    def _find_related_task(self, thread_emails: List[Dict], existing_tasks: List[Any]) -> Optional[Any]:
        """既存タスクとの関連を検索"""
        if not thread_emails or not existing_tasks:
            return None
        
        # 簡易的なマッチング（実装は要調整）
        first_email = thread_emails[0]
        subject = first_email.get("subject", "").lower()
        
        for task in existing_tasks:
            if task.source_email_id and str(task.source_email_id) in [e.get("id") for e in thread_emails]:
                return task
            if subject and subject in task.title.lower():
                return task
        
        return None
    
    def _summarize_thread(self, thread_emails: List[Dict]) -> str:
        """スレッドの要約作成"""
        summary = []
        for email in thread_emails[:5]:  # 最新5件まで
            summary.append(f"From: {email.get('from', 'Unknown')}")
            summary.append(f"Subject: {email.get('subject', 'No subject')}")
            summary.append(f"Body: {email.get('body', '')[:200]}...")
            summary.append("---")
        return "\n".join(summary)
    
    def _create_email_summary(self, thread_emails: List[Dict]) -> str:
        """メール要約の作成"""
        if not thread_emails:
            return ""
        
        summary = f"関連メール {len(thread_emails)} 件\n\n"
        for i, email in enumerate(thread_emails[:3], 1):
            date = email.get('date', 'Unknown date')
            sender = email.get('from', 'Unknown sender')
            subject = email.get('subject', 'No subject')
            summary += f"{i}. {date} - {sender}\n   {subject}\n"
        
        if len(thread_emails) > 3:
            summary += f"\n... 他 {len(thread_emails) - 3} 件"
        
        return summary
    
    def _generate_email_link(self, email: Dict) -> str:
        """メールリンクの生成"""
        provider = email.get("provider", "gmail")
        email_id = email.get("id", "")
        
        if provider == "gmail":
            return f"https://mail.google.com/mail/u/0/#inbox/{email_id}"
        elif provider == "outlook":
            return f"https://outlook.live.com/mail/0/inbox/id/{email_id}"
        else:
            return ""


class OpenAICostTracker:
    """
    OpenAI API使用量とコストの追跡
    """
    
    # GPT-3.5-turbo の料金（2024年1月時点）
    PRICING = {
        "gpt-3.5-turbo": {
            "input": 0.0005,  # per 1K tokens
            "output": 0.0015   # per 1K tokens
        },
        "gpt-4": {
            "input": 0.03,     # per 1K tokens
            "output": 0.06     # per 1K tokens
        }
    }
    
    def __init__(self):
        self.usage_log = []
    
    def log_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        purpose: str
    ):
        """使用量のログ記録"""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "purpose": purpose
        }
        
        self.usage_log.append(entry)
        return cost
    
    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """コスト計算"""
        pricing = self.PRICING.get(model, self.PRICING["gpt-3.5-turbo"])
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return round(input_cost + output_cost, 4)
    
    def get_monthly_usage(self) -> Dict[str, Any]:
        """月間使用量の取得"""
        total_cost = sum(entry["cost"] for entry in self.usage_log)
        total_input = sum(entry["input_tokens"] for entry in self.usage_log)
        total_output = sum(entry["output_tokens"] for entry in self.usage_log)
        
        return {
            "total_cost_usd": total_cost,
            "total_cost_jpy": round(total_cost * 150, 2),  # 概算レート
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "request_count": len(self.usage_log),
            "average_cost_per_request": round(total_cost / len(self.usage_log), 4) if self.usage_log else 0
        }