"""
Context Window Manager for Chat Interface
Prevents token waste by managing conversation context intelligently
"""

import tiktoken
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages conversation context and token limits"""
    
    # Model context limits (in tokens)
    MODEL_LIMITS = {
        "claude-3-7-sonnet-20250219": 200000,
        "claude-3-5-sonnet-20240620": 200000,
        "claude-3-opus-20240229": 200000,
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4": 8192,
        "gpt-3.5-turbo": 16385,
        "gemini-pro": 32768,
    }
    
    # Warning and truncation thresholds
    WARNING_THRESHOLD = 0.75  # Warn at 75%
    TRUNCATION_THRESHOLD = 0.85  # Auto-truncate at 85%
    
    def __init__(self, model: str = "claude-3-7-sonnet-20250219"):
        self.model = model
        self.context_limit = self.MODEL_LIMITS.get(model, 100000)
        
        # Try to load appropriate tokenizer
        try:
            if "gpt" in model.lower():
                self.encoder = tiktoken.encoding_for_model("gpt-4")
            elif "claude" in model.lower():
                # Claude uses similar tokenization to GPT
                self.encoder = tiktoken.encoding_for_model("gpt-4")
            else:
                # Fallback to gpt-4 encoding
                self.encoder = tiktoken.encoding_for_model("gpt-4")
        except Exception as e:
            logger.warning(f"Failed to load tokenizer: {e}, using cl100k_base")
            self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4
    
    def count_messages_tokens(self, messages: List[Dict]) -> int:
        """Count total tokens in message list"""
        total = 0
        for msg in messages:
            # Count role and content
            total += self.count_tokens(msg.get("role", ""))
            total += self.count_tokens(msg.get("content", ""))
            # Add overhead for message formatting (~4 tokens per message)
            total += 4
        return total
    
    def check_limit(self, current_tokens: int) -> Dict:
        """Check if approaching or exceeding limits"""
        usage_percent = current_tokens / self.context_limit
        
        status = {
            "current_tokens": current_tokens,
            "limit": self.context_limit,
            "usage_percent": usage_percent,
            "remaining": self.context_limit - current_tokens,
            "status": "ok"
        }
        
        if usage_percent >= self.TRUNCATION_THRESHOLD:
            status["status"] = "critical"
            status["action"] = "truncate"
            status["message"] = f"Context usage at {usage_percent*100:.1f}%. Auto-truncation needed."
        elif usage_percent >= self.WARNING_THRESHOLD:
            status["status"] = "warning"
            status["action"] = "warn"
            status["message"] = f"Context usage at {usage_percent*100:.1f}%. Consider starting new conversation."
        
        return status
    
    def truncate_messages(
        self, 
        messages: List[Dict], 
        target_tokens: Optional[int] = None,
        strategy: str = "sliding_window"
    ) -> Tuple[List[Dict], Dict]:
        """
        Truncate messages to fit within token limit
        
        Strategies:
        - sliding_window: Keep most recent messages
        - important_first: Keep system messages + recent messages
        - summarize: Summarize old messages (requires LLM)
        """
        if target_tokens is None:
            target_tokens = int(self.context_limit * 0.75)  # Target 75% usage
        
        if strategy == "sliding_window":
            return self._truncate_sliding_window(messages, target_tokens)
        elif strategy == "important_first":
            return self._truncate_important_first(messages, target_tokens)
        else:
            return self._truncate_sliding_window(messages, target_tokens)
    
    def _truncate_sliding_window(
        self, 
        messages: List[Dict], 
        target_tokens: int
    ) -> Tuple[List[Dict], Dict]:
        """Keep most recent messages that fit in target"""
        truncated = []
        current_tokens = 0
        messages_removed = 0
        
        # Always keep system messages
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        other_messages = [msg for msg in messages if msg.get("role") != "system"]
        
        # Add system messages first
        for msg in system_messages:
            msg_tokens = self.count_tokens(msg.get("content", "")) + 4
            if current_tokens + msg_tokens <= target_tokens:
                truncated.append(msg)
                current_tokens += msg_tokens
        
        # Add recent messages in reverse order
        for msg in reversed(other_messages):
            msg_tokens = self.count_tokens(msg.get("content", "")) + 4
            if current_tokens + msg_tokens <= target_tokens:
                truncated.insert(len(system_messages), msg)
                current_tokens += msg_tokens
            else:
                messages_removed += 1
        
        metadata = {
            "strategy": "sliding_window",
            "original_count": len(messages),
            "truncated_count": len(truncated),
            "messages_removed": messages_removed,
            "tokens_before": self.count_messages_tokens(messages),
            "tokens_after": current_tokens,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Truncated {messages_removed} messages using sliding window")
        return truncated, metadata
    
    def _truncate_important_first(
        self, 
        messages: List[Dict], 
        target_tokens: int
    ) -> Tuple[List[Dict], Dict]:
        """Keep important messages (system, first user, recent)"""
        truncated = []
        current_tokens = 0
        messages_removed = 0
        
        # Priority 1: System messages
        system_msgs = [msg for msg in messages if msg.get("role") == "system"]
        for msg in system_msgs:
            msg_tokens = self.count_tokens(msg.get("content", "")) + 4
            if current_tokens + msg_tokens <= target_tokens:
                truncated.append(msg)
                current_tokens += msg_tokens
        
        # Priority 2: First user message (context)
        non_system = [msg for msg in messages if msg.get("role") != "system"]
        if non_system:
            first_msg = non_system[0]
            msg_tokens = self.count_tokens(first_msg.get("content", "")) + 4
            if current_tokens + msg_tokens <= target_tokens:
                truncated.append(first_msg)
                current_tokens += msg_tokens
            remaining_msgs = non_system[1:]
        else:
            remaining_msgs = []
        
        # Priority 3: Recent messages
        for msg in reversed(remaining_msgs):
            msg_tokens = self.count_tokens(msg.get("content", "")) + 4
            if current_tokens + msg_tokens <= target_tokens:
                # Insert before last position
                insert_pos = len(truncated)
                truncated.insert(insert_pos, msg)
                current_tokens += msg_tokens
            else:
                messages_removed += 1
        
        metadata = {
            "strategy": "important_first",
            "original_count": len(messages),
            "truncated_count": len(truncated),
            "messages_removed": messages_removed,
            "tokens_before": self.count_messages_tokens(messages),
            "tokens_after": current_tokens,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Truncated {messages_removed} messages keeping important ones")
        return truncated, metadata
    
    def format_context_status(self, status: Dict) -> str:
        """Format status for display"""
        percent = status["usage_percent"] * 100
        
        if status["status"] == "critical":
            return f"⚠️ Context limit critical ({percent:.1f}% used). Messages will be auto-truncated."
        elif status["status"] == "warning":
            return f"⚡ Context usage high ({percent:.1f}%). Consider starting a new conversation soon."
        else:
            return f"✅ Context healthy ({percent:.1f}% used)"
    
    def estimate_tokens_for_response(self, prompt_tokens: int) -> int:
        """Estimate tokens needed for response"""
        # Conservative estimate: response might be 2x prompt size
        return prompt_tokens * 2
    
    def can_add_message(self, current_tokens: int, new_message: str) -> Tuple[bool, str]:
        """Check if new message can be added"""
        new_tokens = self.count_tokens(new_message)
        estimated_response = self.estimate_tokens_for_response(new_tokens)
        total_needed = current_tokens + new_tokens + estimated_response
        
        if total_needed > self.context_limit:
            return False, f"Adding this message would exceed context limit (need {total_needed}, limit {self.context_limit})"
        elif total_needed > self.context_limit * self.TRUNCATION_THRESHOLD:
            return True, f"Warning: This will trigger truncation (usage: {(total_needed/self.context_limit)*100:.1f}%)"
        else:
            return True, "OK"


def get_context_manager(model: str = "claude-3-7-sonnet-20250219") -> ContextManager:
    """Factory function to get context manager"""
    return ContextManager(model)
