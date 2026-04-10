"""Unified async LLM client with cost tracking for OpenAI and Anthropic.

Provides a provider-agnostic interface for LLM API calls with automatic
cost tracking, retry logic, and token counting.
"""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

# OpenAI import with graceful fallback
try:
    from openai import AsyncOpenAI
    from openai.types.chat import ChatCompletion
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None
    ChatCompletion = None

# Anthropic import with graceful fallback
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class CostRecord:
    """Cost tracking record for a single API call."""
    extraction_job_id: str
    provider: str
    model: str
    endpoint: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "extraction_job_id": self.extraction_job_id,
            "provider": self.provider,
            "model": self.model,
            "endpoint": self.endpoint,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "timestamp": self.timestamp.isoformat(),
        }


# Pricing per 1M tokens (as of April 2026)
PRICING = {
    "openai": {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    },
    "anthropic": {
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
    },
}


class LLMClient:
    """Unified LLM client with cost tracking.
    
    Supports both OpenAI and Anthropic with automatic provider switching,
    cost calculation, and retry logic.
    
    Example:
        client = LLMClient(provider="openai", model="gpt-4o")
        
        response, cost = await client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            extraction_job_id="job_123",
            endpoint="entity_extraction"
        )
    """
    
    def __init__(
        self,
        provider: Union[str, LLMProvider] = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        cost_tracking_enabled: bool = True,
    ):
        """Initialize LLM client.
        
        Args:
            provider: "openai" or "anthropic"
            model: Model name (uses env var default if not provided)
            api_key: API key (uses env var if not provided)
            timeout: Request timeout in seconds
            max_retries: Max retry attempts for failed requests
            cost_tracking_enabled: Whether to track costs
        """
        self.provider = LLMProvider(provider)
        self.timeout = timeout
        self.max_retries = max_retries
        self.cost_tracking_enabled = cost_tracking_enabled
        self._cost_records: List[CostRecord] = []
        
        # Set model with fallback to env vars
        if model:
            self.model = model
        elif self.provider == LLMProvider.OPENAI:
            self.model = os.getenv("L2_OPENAI_MODEL", "gpt-4o")
        else:
            self.model = os.getenv("L2_ANTHROPIC_MODEL", "claude-3-5-sonnet")
        
        # Initialize provider client
        if self.provider == LLMProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package not installed. Run: pip install openai")
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required (pass api_key or set OPENAI_API_KEY)")
            self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)
            
        elif self.provider == LLMProvider.ANTHROPIC:
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key required (pass api_key or set ANTHROPIC_API_KEY)")
            self._client = AsyncAnthropic(api_key=api_key, timeout=timeout)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        extraction_job_id: str,
        endpoint: str,
        temperature: float = 0.0,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None,
        logprobs: bool = False,
    ) -> tuple[ChatCompletion, Optional[CostRecord]]:
        """Execute chat completion with cost tracking.
        
        Args:
            messages: Chat messages
            extraction_job_id: Job ID for cost attribution
            endpoint: Endpoint name for cost tracking
            temperature: Sampling temperature
            tools: Function calling tools (OpenAI only)
            tool_choice: Force specific tool (OpenAI only)
            logprobs: Request logprobs (OpenAI only)
            
        Returns:
            Tuple of (response, cost_record)
        """
        if self.provider == LLMProvider.OPENAI:
            return await self._openai_completion(
                messages, extraction_job_id, endpoint,
                temperature, tools, tool_choice, logprobs
            )
        else:
            return await self._anthropic_completion(
                messages, extraction_job_id, endpoint, temperature
            )
    
    async def _openai_completion(
        self,
        messages: List[Dict[str, str]],
        extraction_job_id: str,
        endpoint: str,
        temperature: float,
        tools: Optional[List[Dict]],
        tool_choice: Optional[Dict],
        logprobs: bool,
    ) -> tuple[ChatCompletion, Optional[CostRecord]]:
        """Execute OpenAI chat completion."""
        
        for attempt in range(self.max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    tools=tools,
                    tool_choice=tool_choice,
                    logprobs=logprobs if logprobs else None,
                )
                
                # Calculate cost
                cost_record = None
                if self.cost_tracking_enabled:
                    cost_record = self._calculate_cost(
                        extraction_job_id=extraction_job_id,
                        provider="openai",
                        model=self.model,
                        endpoint=endpoint,
                        input_tokens=response.usage.prompt_tokens if response.usage else 0,
                        output_tokens=response.usage.completion_tokens if response.usage else 0,
                    )
                    self._cost_records.append(cost_record)
                
                return response, cost_record
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt  # Exponential backoff
                await asyncio.sleep(wait_time)
        
        raise RuntimeError("Max retries exceeded")
    
    async def _anthropic_completion(
        self,
        messages: List[Dict[str, str]],
        extraction_job_id: str,
        endpoint: str,
        temperature: float,
    ) -> tuple[Any, Optional[CostRecord]]:
        """Execute Anthropic chat completion."""
        
        # Convert messages to Anthropic format
        system_msg = None
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        for attempt in range(self.max_retries):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": anthropic_messages,
                    "temperature": temperature,
                    "max_tokens": 4096,
                }
                if system_msg:
                    kwargs["system"] = system_msg
                
                response = await self._client.messages.create(**kwargs)
                
                # Calculate cost
                cost_record = None
                if self.cost_tracking_enabled:
                    usage = response.usage
                    cost_record = self._calculate_cost(
                        extraction_job_id=extraction_job_id,
                        provider="anthropic",
                        model=self.model,
                        endpoint=endpoint,
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                    )
                    self._cost_records.append(cost_record)
                
                return response, cost_record
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        raise RuntimeError("Max retries exceeded")
    
    def _calculate_cost(
        self,
        extraction_job_id: str,
        provider: str,
        model: str,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
    ) -> CostRecord:
        """Calculate USD cost from token usage."""
        
        # Get pricing for model
        provider_pricing = PRICING.get(provider, {})
        model_pricing = provider_pricing.get(model, {"input": 0, "output": 0})
        
        # Calculate cost per 1M tokens
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
        total_cost = input_cost + output_cost
        
        return CostRecord(
            extraction_job_id=extraction_job_id,
            provider=provider,
            model=model,
            endpoint=endpoint,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=total_cost,
        )
    
    def get_cost_records(self) -> List[CostRecord]:
        """Get all recorded costs."""
        return self._cost_records.copy()
    
    def get_total_cost(self) -> float:
        """Get total cost of all requests."""
        return sum(record.cost_usd for record in self._cost_records)
    
    def clear_cost_records(self) -> None:
        """Clear cost history."""
        self._cost_records.clear()
