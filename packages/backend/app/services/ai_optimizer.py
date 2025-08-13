"""
AI最適化サービス
コスト効率を重視したAI機能の実装
"""
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib
import json
from functools import lru_cache
import asyncio
import re

from app.core.config import settings
from app.models.task import Task
from app.services.cache_service import CacheService


class EmailAnalyzer:
    """メール分析とタスク化サービス"""
    
    def __init__(self):
        self.cache = CacheService()
        
    async def analyze_emails_batch(
        self, 
        emails: List[Dict[str, Any]],
        existing_tasks: List[Task]
    ) -> List[Dict[str, Any]]:
        """
        メールをバッチで分析してタスク化
        同じ要件の会話スレッドは1つのタスクとして判定
        新規タスク作成と進捗更新を1回のAPIコールで判定
        """
        # メールをスレッドでグループ化
        email_threads = self._group_by_thread(emails)
        
        # すべてのスレッドを一括分析（コスト削減）
        analysis_results = await self._batch_analyze_all_threads(
            email_threads, 
            existing_tasks
        )
        
        return analysis_results
    
    def _group_by_thread(self, emails: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        メールをスレッド（会話）でグループ化
        Subject の Re:, Fwd: を除去して同一判定
        """
        threads = {}
        
        for email in emails:
            # スレッドIDの生成（件名から Re:, Fwd: を除去）
            subject = email.get("subject", "")
            clean_subject = re.sub(r'^(Re:|Fwd:|FW:)\s*', '', subject, flags=re.IGNORECASE)
            clean_subject = clean_subject.strip()
            
            # In-Reply-To ヘッダーがあればそれを優先
            thread_id = email.get("in_reply_to") or hashlib.md5(clean_subject.encode()).hexdigest()
            
            if thread_id not in threads:
                threads[thread_id] = []
            threads[thread_id].append(email)
        
        return threads
    
    def _find_related_task(
        self, 
        thread_emails: List[Dict],
        existing_tasks: List[Task]
    ) -> Optional[Task]:
        """
        スレッドメールに関連する既存タスクを検索
        """
        # 最初のメールの件名でマッチング
        if not thread_emails:
            return None
            
        first_email = thread_emails[0]
        subject = first_email.get("subject", "")
        clean_subject = re.sub(r'^(Re:|Fwd:|FW:)\s*', '', subject, flags=re.IGNORECASE).strip()
        
        for task in existing_tasks:
            # タスクのソースメールIDでマッチング
            if task.source_email_id in [e.get("id") for e in thread_emails]:
                return task
            
            # 件名の類似度でマッチング（80%以上の一致）
            if self._calculate_similarity(clean_subject, task.title) > 0.8:
                return task
        
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """文字列の類似度計算（簡易版）"""
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # 完全一致
        if text1_lower == text2_lower:
            return 1.0
        
        # 部分一致
        if text1_lower in text2_lower or text2_lower in text1_lower:
            return 0.8
        
        # 単語の重複率
        words1 = set(text1_lower.split())
        words2 = set(text2_lower.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _batch_analyze_all_threads(
        self,
        email_threads: Dict[str, List],
        existing_tasks: List[Task]
    ) -> List[Dict[str, Any]]:
        """
        すべてのメールスレッドを一括分析
        1回のAPIコールで新規タスク判定と進捗更新を実行
        """
        # 分析用データの準備
        threads_data = []
        for thread_id, thread_emails in email_threads.items():
            existing_task = self._find_related_task(thread_emails, existing_tasks)
            threads_data.append({
                "thread_id": thread_id,
                "emails": thread_emails,
                "existing_task": existing_task,
                "content": self._combine_thread_content(thread_emails)[:1500]
            })
        
        # 統合プロンプトの作成
        prompt = self._create_batch_analysis_prompt(threads_data)
        
        # 1回のAI APIコールですべて処理（コスト削減）
        # TODO: 実際のAI APIコール実装
        analysis_results = await self._call_ai_api(prompt)
        
        # 結果を整形
        formatted_results = []
        for thread_result in analysis_results:
            thread_id = thread_result["thread_id"]
            thread_emails = email_threads[thread_id]
            
            if thread_result.get("action") == "update":
                formatted_results.append({
                    "action": "update",
                    "task_id": thread_result["task_id"],
                    "updates": {
                        "new_status": thread_result.get("new_status"),
                        "progress_percentage": thread_result.get("progress_percentage"),
                        "summary": thread_result.get("summary"),
                        "updated_by": "ai",
                        "email_summary": self._summarize_thread(thread_emails)
                    },
                    "source_emails": thread_emails
                })
            elif thread_result.get("action") == "create":
                formatted_results.append({
                    "action": "create",
                    "task_data": {
                        "title": thread_result.get("title"),
                        "description": thread_result.get("description"),
                        "priority": thread_result.get("priority", "medium"),
                        "due_date": thread_result.get("due_date"),
                        "created_by": "ai",
                        "email_summary": self._summarize_thread(thread_emails),
                        "source_email_id": thread_emails[0].get("id"),
                        "source_email_link": self._generate_email_link(thread_emails[0])
                    },
                    "source_emails": thread_emails
                })
        
        return formatted_results
    
    def _create_batch_analysis_prompt(self, threads_data: List[Dict]) -> str:
        """
        バッチ分析用の統合プロンプトを作成
        """
        prompt = """
        以下の複数のメールスレッドを分析し、それぞれについてタスク化と進捗更新を判定してください。
        
        各スレッドについて以下を判定:
        1. 既存タスクがある場合: 進捗状況の更新が必要か
        2. 既存タスクがない場合: 新規タスクとして作成すべきか
        
        JSON配列形式で回答してください。
        
        スレッド情報:
        """
        
        for i, thread_data in enumerate(threads_data):
            prompt += f"\n\n--- スレッド {i+1} (ID: {thread_data['thread_id']}) ---\n"
            
            if thread_data["existing_task"]:
                prompt += f"既存タスク: {thread_data['existing_task'].title}\n"
                prompt += f"現在のステータス: {thread_data['existing_task'].status}\n"
                prompt += "判定タイプ: 進捗更新\n"
            else:
                prompt += "既存タスク: なし\n"
                prompt += "判定タイプ: 新規タスク作成\n"
            
            prompt += f"メール内容:\n{thread_data['content']}\n"
        
        prompt += """
        
        回答フォーマット:
        [
            {
                "thread_id": "スレッドID",
                "action": "create" or "update" or "none",
                // createの場合:
                "title": "タスクタイトル",
                "description": "説明",
                "priority": "high/medium/low",
                "due_date": "ISO形式またはnull",
                // updateの場合:
                "task_id": "既存タスクID",
                "new_status": "pending/in_progress/completed/null",
                "progress_percentage": 0-100またはnull,
                "summary": "進捗の要約"
            },
            ...
        ]
        """
        
        return prompt
    
    async def _call_ai_api(self, prompt: str) -> List[Dict]:
        """
        AI APIを呼び出し（実際の実装が必要）
        """
        # TODO: AWS Bedrock等の実際のAPIコール実装
        # ここではモックレスポンス
        return [
            {
                "thread_id": "mock_thread_1",
                "action": "create",
                "title": "メール同期機能の改善",
                "description": "重複判定ロジックの実装",
                "priority": "medium",
                "due_date": None
            }
        ]
    
    def _combine_thread_content(self, thread_emails: List[Dict]) -> str:
        """スレッドのメール内容を結合"""
        contents = []
        for email in sorted(thread_emails, key=lambda x: x.get("date", "")):
            contents.append(f"From: {email.get('from', '')}")
            contents.append(f"Subject: {email.get('subject', '')}")
            contents.append(f"Body: {email.get('body', '')[:500]}")
            contents.append("---")
        
        return "\n".join(contents)
    
    def _summarize_email(self, email: Dict) -> str:
        """メールの要約を生成"""
        # 簡易的な要約（実際はAIで生成）
        body = email.get("body", "")
        if len(body) > 200:
            return body[:197] + "..."
        return body
    
    def _summarize_thread(self, thread_emails: List[Dict]) -> str:
        """スレッド全体の要約を生成"""
        # 簡易的な要約（実際はAIで生成）
        summary_parts = []
        for email in thread_emails[:3]:  # 最初の3通のみ
            summary_parts.append(f"- {email.get('from', 'Unknown')}: {email.get('subject', '')}")
        
        if len(thread_emails) > 3:
            summary_parts.append(f"... 他 {len(thread_emails) - 3} 件のメール")
        
        return "\n".join(summary_parts)
    
    def _generate_email_link(self, email: Dict) -> str:
        """メールへのリンクを生成"""
        provider = email.get("provider", "gmail")
        email_id = email.get("id", "")
        
        if provider == "gmail":
            return f"https://mail.google.com/mail/u/0/#inbox/{email_id}"
        elif provider == "outlook":
            return f"https://outlook.live.com/mail/0/inbox/id/{email_id}"
        else:
            return ""


class AIOptimizer:
    """コスト最適化されたAI処理サービス"""
    
    def __init__(self):
        self.cache = CacheService()
        self.batch_size = 10  # バッチ処理のサイズ
        self.cache_ttl = 86400  # キャッシュ有効期限（1日）
        
    async def batch_analyze_tasks(
        self, 
        tasks: List[Task],
        analysis_type: str = "risk"
    ) -> Dict[str, Any]:
        """
        複数タスクをバッチで分析（コスト削減）
        10タスクを1回のAPIコールで処理
        """
        # キャッシュキーの生成
        cache_key = self._generate_cache_key(tasks, analysis_type)
        
        # キャッシュチェック
        if cached := await self.cache.get(cache_key):
            return json.loads(cached)
        
        # バッチ処理用のプロンプト作成
        batches = [
            tasks[i:i + self.batch_size] 
            for i in range(0, len(tasks), self.batch_size)
        ]
        
        results = []
        for batch in batches:
            # 1回のAPIコールで複数タスクを処理
            batch_result = await self._analyze_batch(batch, analysis_type)
            results.extend(batch_result)
            
            # レート制限対策
            await asyncio.sleep(0.5)
        
        # 結果をキャッシュ
        await self.cache.set(
            cache_key, 
            json.dumps(results), 
            expire=self.cache_ttl
        )
        
        return results
    
    async def smart_task_prioritization(
        self, 
        tasks: List[Task]
    ) -> List[Dict[str, Any]]:
        """
        スマートな優先度判定（ルールベース + AI）
        簡単な判定はルールベース、複雑な場合のみAI使用
        """
        prioritized = []
        tasks_for_ai = []
        
        for task in tasks:
            # Step 1: ルールベースで判定
            if rule_priority := self._rule_based_priority(task):
                prioritized.append({
                    "task_id": task.id,
                    "priority": rule_priority,
                    "method": "rule_based"
                })
            else:
                # AIが必要なタスクをバッファ
                tasks_for_ai.append(task)
        
        # Step 2: AI判定が必要なタスクをバッチ処理
        if tasks_for_ai:
            ai_results = await self.batch_analyze_tasks(
                tasks_for_ai, 
                "priority"
            )
            prioritized.extend(ai_results)
        
        return prioritized
    
    def _rule_based_priority(self, task: Task) -> Optional[str]:
        """ルールベースの優先度判定"""
        # 期限切れ
        if task.due_date and task.due_date < datetime.now():
            return "critical"
        
        # 24時間以内
        if task.due_date and task.due_date < datetime.now() + timedelta(days=1):
            return "high"
        
        # ブロッカータスク
        if "blocker" in task.title.lower() or "urgent" in task.title.lower():
            return "high"
        
        # 明確な判定ができない場合はNone
        return None
    
    async def extract_meeting_actions(
        self, 
        meeting_text: str,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        議事録からアクションアイテムを抽出
        同じテキストは再処理しない（キャッシュ活用）
        """
        if use_cache:
            text_hash = hashlib.md5(meeting_text.encode()).hexdigest()
            cache_key = f"meeting_actions:{text_hash}"
            
            if cached := await self.cache.get(cache_key):
                return json.loads(cached)
        
        # プロンプトの最適化（トークン数削減）
        condensed_text = self._condense_text(meeting_text, max_chars=2000)
        
        # AI処理（実際の実装では適切なAIサービスを呼び出し）
        actions = await self._extract_actions_from_text(condensed_text)
        
        # キャッシュ保存
        if use_cache:
            await self.cache.set(
                cache_key,
                json.dumps(actions),
                expire=self.cache_ttl * 7  # 議事録は7日間キャッシュ
            )
        
        return actions
    
    async def generate_weekly_summary(
        self,
        user_id: str,
        week_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        週次サマリーの生成（週1回実行でコスト削減）
        """
        # データの前処理と集約
        summary_data = {
            "completed_tasks": len(week_data.get("completed", [])),
            "new_tasks": len(week_data.get("created", [])),
            "overdue_tasks": len(week_data.get("overdue", [])),
            "key_decisions": week_data.get("decisions", []),
            "risks": week_data.get("risks", [])
        }
        
        # テンプレートベースの基本サマリー作成
        basic_summary = self._create_basic_summary(summary_data)
        
        # 重要な洞察のみAIで生成
        if self._needs_ai_insights(summary_data):
            insights = await self._generate_ai_insights(summary_data)
            basic_summary["ai_insights"] = insights
        
        return basic_summary
    
    def _generate_cache_key(
        self, 
        tasks: List[Task], 
        analysis_type: str
    ) -> str:
        """キャッシュキーの生成"""
        task_ids = sorted([str(t.id) for t in tasks])
        key_string = f"{analysis_type}:{':'.join(task_ids)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _condense_text(self, text: str, max_chars: int) -> str:
        """テキストの圧縮（トークン削減）"""
        if len(text) <= max_chars:
            return text
        
        # 重要な部分を抽出
        lines = text.split('\n')
        important_lines = [
            line for line in lines
            if any(keyword in line.lower() 
                  for keyword in ['action', 'todo', 'next', 'decide', 'assign'])
        ]
        
        condensed = '\n'.join(important_lines[:20])
        return condensed[:max_chars]
    
    def _needs_ai_insights(self, data: Dict[str, Any]) -> bool:
        """AI分析が必要かどうかの判定"""
        # リスクが多い、または遅延タスクが多い場合のみAI分析
        return (
            len(data.get("risks", [])) > 3 or
            data.get("overdue_tasks", 0) > 5
        )
    
    def _create_basic_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """テンプレートベースの基本サマリー作成"""
        return {
            "week_overview": {
                "completed": data["completed_tasks"],
                "created": data["new_tasks"],
                "overdue": data["overdue_tasks"]
            },
            "status": "on_track" if data["overdue_tasks"] < 3 else "at_risk",
            "generated_at": datetime.now().isoformat()
        }
    
    async def _analyze_batch(
        self, 
        batch: List[Task], 
        analysis_type: str
    ) -> List[Dict[str, Any]]:
        """バッチ分析の実装（実際のAI呼び出し部分）"""
        # TODO: 実際のAIサービス呼び出しを実装
        # ここではモックデータを返す
        return [
            {
                "task_id": task.id,
                "analysis_type": analysis_type,
                "result": "mock_result",
                "confidence": 0.85
            }
            for task in batch
        ]
    
    async def _extract_actions_from_text(
        self, 
        text: str
    ) -> List[Dict[str, Any]]:
        """テキストからアクション抽出（実際のAI呼び出し部分）"""
        # TODO: 実際のAIサービス呼び出しを実装
        return [
            {
                "action": "Sample action item",
                "assignee": "TBD",
                "due_date": None,
                "priority": "medium"
            }
        ]
    
    async def _generate_ai_insights(
        self, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI洞察の生成（実際のAI呼び出し部分）"""
        # TODO: 実際のAIサービス呼び出しを実装
        return {
            "risk_assessment": "Medium risk due to overdue tasks",
            "recommendations": ["Focus on critical path items"],
            "predicted_completion": "On track with minor delays"
        }


class CostMonitor:
    """AI使用コストのモニタリング"""
    
    def __init__(self):
        self.daily_limit = 30  # $30/day
        self.monthly_limit = 70  # $70/month
        
    async def check_budget(self, estimated_cost: float) -> bool:
        """予算チェック"""
        current_usage = await self._get_current_usage()
        return (current_usage + estimated_cost) < self.daily_limit
    
    async def log_usage(
        self, 
        tokens_in: int, 
        tokens_out: int,
        model: str = "claude-3-haiku"
    ):
        """使用量のロギング"""
        cost = self._calculate_cost(tokens_in, tokens_out, model)
        # TODO: データベースに記録
        return cost
    
    def _calculate_cost(
        self, 
        tokens_in: int, 
        tokens_out: int,
        model: str
    ) -> float:
        """コスト計算"""
        rates = {
            "claude-3-haiku": {
                "input": 0.00025,  # per 1K tokens
                "output": 0.00125  # per 1K tokens
            }
        }
        
        rate = rates.get(model, rates["claude-3-haiku"])
        cost = (tokens_in / 1000 * rate["input"] + 
                tokens_out / 1000 * rate["output"])
        return cost
    
    async def _get_current_usage(self) -> float:
        """現在の使用量取得"""
        # TODO: データベースから取得
        return 0.0