"""
ローカルLLMサービス
Ollama を使用した無料のAI処理（検証用）
"""
import requests
from typing import Dict, Any, List, Optional
import json


class LocalLLMService:
    """
    Ollama を使用したローカルLLMサービス
    検証環境では無料で AI 機能を試せる
    """
    
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
    async def classify_task(self, task_text: str) -> Dict[str, Any]:
        """
        タスクの分類（カテゴリ、緊急度など）
        ローカル実行なのでコストゼロ
        """
        prompt = f"""
        以下のタスクを分類してください。
        カテゴリ: [開発/設計/テスト/会議/その他]
        緊急度: [高/中/低]
        
        タスク: {task_text}
        
        JSON形式で回答:
        """
        
        try:
            response = await self._generate(prompt, max_tokens=100)
            return self._parse_json_response(response)
        except Exception as e:
            # フォールバック
            return {
                "category": "その他",
                "urgency": "中",
                "error": str(e)
            }
    
    async def extract_keywords(self, text: str) -> List[str]:
        """
        テキストからキーワード抽出
        """
        prompt = f"""
        以下のテキストから重要なキーワードを5つ抽出してください。
        カンマ区切りで回答してください。
        
        テキスト: {text[:500]}
        
        キーワード:
        """
        
        try:
            response = await self._generate(prompt, max_tokens=50)
            keywords = [k.strip() for k in response.split(',')]
            return keywords[:5]
        except Exception:
            return []
    
    async def simple_risk_assessment(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        簡単なリスク評価
        """
        prompt = f"""
        以下のタスク情報からリスクレベルを評価してください。
        
        タイトル: {task_data.get('title', '')}
        期限: {task_data.get('due_date', '未設定')}
        ステータス: {task_data.get('status', '')}
        
        リスクレベル（高/中/低）と理由を簡潔に回答:
        """
        
        try:
            response = await self._generate(prompt, max_tokens=100)
            # シンプルなパース
            if "高" in response:
                level = "high"
            elif "低" in response:
                level = "low"
            else:
                level = "medium"
                
            return {
                "risk_level": level,
                "reason": response[:100]
            }
        except Exception:
            return {"risk_level": "medium", "reason": "評価不可"}
    
    async def _generate(
        self, 
        prompt: str, 
        max_tokens: int = 200,
        temperature: float = 0.7
    ) -> str:
        """
        Ollama API を呼び出して生成
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            raise Exception("Ollama not running. Please start Ollama service.")
        except Exception as e:
            raise Exception(f"Generation error: {str(e)}")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        レスポンスからJSONを抽出してパース
        """
        try:
            # JSON部分を探す
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # パース失敗時のフォールバック
        return {"raw_response": response}
    
    async def is_available(self) -> bool:
        """
        Ollama サービスが利用可能かチェック
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False


class HybridAIService:
    """
    ローカルLLMとクラウドAIのハイブリッドサービス
    簡単なタスクはローカル、複雑なタスクはクラウドで処理
    """
    
    def __init__(self):
        self.local_llm = LocalLLMService()
        self.use_local_first = True  # コスト削減のため優先的にローカル使用
        
    async def process_task(
        self, 
        task_text: str,
        complexity: str = "simple"
    ) -> Dict[str, Any]:
        """
        タスクの複雑度に応じて処理を振り分け
        """
        # 簡単なタスクはローカルで処理
        if complexity == "simple" and await self.local_llm.is_available():
            result = await self.local_llm.classify_task(task_text)
            result["processed_by"] = "local"
            return result
        
        # 複雑なタスクまたはローカル不可の場合はクラウド
        # TODO: クラウドAIサービスの実装
        return {
            "processed_by": "cloud",
            "message": "Cloud AI processing not yet implemented"
        }
    
    async def batch_process_simple_tasks(
        self, 
        tasks: List[str]
    ) -> List[Dict[str, Any]]:
        """
        簡単なタスクをバッチでローカル処理
        """
        results = []
        for task in tasks:
            if await self.local_llm.is_available():
                result = await self.local_llm.classify_task(task)
                results.append(result)
            else:
                results.append({
                    "error": "Local LLM not available",
                    "task": task
                })
        
        return results