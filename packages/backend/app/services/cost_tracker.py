"""
コスト追跡とアラート機能
GPT-5-mini の料金監視
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
from pathlib import Path


class OpenAICostTracker:
    """
    OpenAI API使用量とコストの追跡（GPT-5対応）
    """
    
    # GPT-5 シリーズの料金（2025年8月時点）
    PRICING = {
        "gpt-5": {
            "input": 1.25,   # per 1M tokens
            "output": 10.00  # per 1M tokens
        },
        "gpt-5-mini": {
            "input": 0.25,   # per 1M tokens
            "output": 2.00   # per 1M tokens
        },
        "gpt-5-nano": {
            "input": 0.05,   # per 1M tokens
            "output": 0.40   # per 1M tokens
        },
        "gpt-5-chat-latest": {
            "input": 1.25,   # per 1M tokens
            "output": 10.00  # per 1M tokens
        },
        "gpt-4o": {
            "input": 2.5,    # per 1M tokens
            "output": 10.0   # per 1M tokens
        },
        "gpt-3.5-turbo": {
            "input": 0.5,    # per 1M tokens
            "output": 1.5    # per 1M tokens
        }
    }
    
    def __init__(self):
        self.usage_log_file = Path("openai_usage.json")
        self.usage_log = self._load_usage_log()
        self.daily_limit = float(os.getenv("OPENAI_DAILY_LIMIT_USD", "10.0"))
        self.monthly_limit = float(os.getenv("OPENAI_MONTHLY_LIMIT_USD", "100.0"))
    
    def _load_usage_log(self) -> list:
        """使用量ログの読み込み"""
        if self.usage_log_file.exists():
            try:
                with open(self.usage_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_usage_log(self):
        """使用量ログの保存"""
        try:
            with open(self.usage_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_log, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"使用量ログの保存に失敗: {e}")
    
    def log_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        purpose: str,
        verbosity: Optional[str] = None,
        reasoning_effort: Optional[str] = None
    ) -> float:
        """使用量のログ記録"""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "cost_jpy": round(cost * 150, 2),  # 概算レート
            "purpose": purpose,
            "verbosity": verbosity,
            "reasoning_effort": reasoning_effort
        }
        
        self.usage_log.append(entry)
        self._save_usage_log()
        
        # コスト制限チェック
        self._check_cost_limits()
        
        return cost
    
    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """コスト計算（GPT-5対応）"""
        # モデル名の正規化
        if model.startswith("gpt-5-mini"):
            pricing_model = "gpt-5-mini"
        elif model.startswith("gpt-5-nano"):
            pricing_model = "gpt-5-nano" 
        elif model.startswith("gpt-5-chat"):
            pricing_model = "gpt-5-chat-latest"
        elif model.startswith("gpt-5"):
            pricing_model = "gpt-5"
        else:
            pricing_model = model
        
        pricing = self.PRICING.get(pricing_model, self.PRICING["gpt-5-mini"])
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)
    
    def get_daily_usage(self) -> Dict[str, Any]:
        """日次使用量の取得"""
        today = datetime.now().date()
        today_entries = [
            entry for entry in self.usage_log
            if datetime.fromisoformat(entry["timestamp"]).date() == today
        ]
        
        total_cost = sum(entry["cost_usd"] for entry in today_entries)
        total_input = sum(entry["input_tokens"] for entry in today_entries)
        total_output = sum(entry["output_tokens"] for entry in today_entries)
        
        return {
            "date": today.isoformat(),
            "total_cost_usd": round(total_cost, 4),
            "total_cost_jpy": round(total_cost * 150, 2),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "request_count": len(today_entries),
            "daily_limit_usd": self.daily_limit,
            "limit_usage_percent": round((total_cost / self.daily_limit) * 100, 2) if self.daily_limit > 0 else 0,
            "requests": today_entries[-10:]  # 最新10件
        }
    
    def get_monthly_usage(self) -> Dict[str, Any]:
        """月間使用量の取得"""
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        month_entries = [
            entry for entry in self.usage_log
            if datetime.fromisoformat(entry["timestamp"]) >= month_start
        ]
        
        total_cost = sum(entry["cost_usd"] for entry in month_entries)
        total_input = sum(entry["input_tokens"] for entry in month_entries)
        total_output = sum(entry["output_tokens"] for entry in month_entries)
        
        # モデル別統計
        model_stats = {}
        for entry in month_entries:
            model = entry["model"]
            if model not in model_stats:
                model_stats[model] = {
                    "requests": 0,
                    "cost_usd": 0,
                    "input_tokens": 0,
                    "output_tokens": 0
                }
            model_stats[model]["requests"] += 1
            model_stats[model]["cost_usd"] += entry["cost_usd"]
            model_stats[model]["input_tokens"] += entry["input_tokens"]
            model_stats[model]["output_tokens"] += entry["output_tokens"]
        
        return {
            "month": now.strftime("%Y-%m"),
            "total_cost_usd": round(total_cost, 4),
            "total_cost_jpy": round(total_cost * 150, 2),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "request_count": len(month_entries),
            "monthly_limit_usd": self.monthly_limit,
            "limit_usage_percent": round((total_cost / self.monthly_limit) * 100, 2) if self.monthly_limit > 0 else 0,
            "average_cost_per_request": round(total_cost / len(month_entries), 6) if month_entries else 0,
            "model_breakdown": model_stats
        }
    
    def _check_cost_limits(self):
        """コスト制限のチェックとアラート"""
        daily_usage = self.get_daily_usage()
        monthly_usage = self.get_monthly_usage()
        
        # 日次制限チェック
        if daily_usage["limit_usage_percent"] >= 90:
            self._send_cost_alert("daily", daily_usage)
        
        # 月次制限チェック
        if monthly_usage["limit_usage_percent"] >= 80:
            self._send_cost_alert("monthly", monthly_usage)
    
    def _send_cost_alert(self, period: str, usage_data: Dict[str, Any]):
        """コストアラートの送信（ログ出力）"""
        print(f"⚠️  OpenAI コストアラート ({period})")
        print(f"使用率: {usage_data['limit_usage_percent']:.1f}%")
        print(f"コスト: ${usage_data[f'total_cost_usd']:.4f}")
        print(f"制限: ${usage_data[f'{period}_limit_usd']:.2f}")
    
    def get_cost_estimate(
        self,
        model: str,
        input_tokens: int,
        max_output_tokens: int = 4000
    ) -> Dict[str, Any]:
        """コスト見積もり"""
        min_cost = self.calculate_cost(model, input_tokens, 100)  # 最小出力
        max_cost = self.calculate_cost(model, input_tokens, max_output_tokens)  # 最大出力
        avg_cost = self.calculate_cost(model, input_tokens, max_output_tokens // 2)  # 平均出力
        
        return {
            "model": model,
            "input_tokens": input_tokens,
            "max_output_tokens": max_output_tokens,
            "cost_range": {
                "min_usd": round(min_cost, 6),
                "avg_usd": round(avg_cost, 6),
                "max_usd": round(max_cost, 6),
                "min_jpy": round(min_cost * 150, 2),
                "avg_jpy": round(avg_cost * 150, 2),
                "max_jpy": round(max_cost * 150, 2)
            }
        }


# グローバルインスタンス
cost_tracker = OpenAICostTracker()