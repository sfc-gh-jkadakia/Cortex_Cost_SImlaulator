"""
Cortex AI Pricing Data
======================
Pricing data sourced from Snowflake Credit Consumption Table.
All prices are in credits per 1 million tokens unless otherwise noted.

Note: Prices may change. Always verify against the official consumption table:
https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf
"""

from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class ModelPricing:
    """Pricing information for a Cortex AI model."""
    model_name: str
    provider: str
    input_credits: float  # Credits per 1M input tokens
    output_credits: float  # Credits per 1M output tokens
    category: str  # small, medium, large, premium
    context_window: int  # Max context window in tokens
    best_for: list[str]  # Recommended use cases
    supports_vision: bool = False
    supports_streaming: bool = True
    available: bool = True  # Whether this model is currently available for COMPLETE


# Model pricing data (Credits per 1M tokens)
# Updated based on Snowflake Credit Consumption Table
# Note: Some models are listed for pricing reference but may not be available in all regions
CORTEX_MODELS = {
    # OpenAI Models (some may have limited regional availability)
    "openai-gpt-5-nano": ModelPricing(
        model_name="openai-gpt-5-nano",
        provider="OpenAI",
        input_credits=0.03,
        output_credits=0.22,
        category="small",
        context_window=128000,
        best_for=["Simple classification", "Basic extraction", "High volume tasks"],
        available=False,  # Limited availability
    ),
    "openai-gpt-5-mini": ModelPricing(
        model_name="openai-gpt-5-mini",
        provider="OpenAI",
        input_credits=0.14,
        output_credits=1.10,
        category="small",
        context_window=128000,
        best_for=["Classification", "Sentiment analysis", "Summarization"],
        available=False,  # Limited availability
    ),
    "openai-gpt-5": ModelPricing(
        model_name="openai-gpt-5",
        provider="OpenAI",
        input_credits=0.69,
        output_credits=5.50,
        category="medium",
        context_window=128000,
        best_for=["Complex reasoning", "Code generation", "Multi-step tasks"],
        supports_vision=True,
        available=False,  # Limited availability
    ),
    "openai-gpt-5-chat": ModelPricing(
        model_name="openai-gpt-5-chat",
        provider="OpenAI",
        input_credits=0.63,
        output_credits=5.00,
        category="medium",
        context_window=128000,
        best_for=["Conversational AI", "Chat applications", "Interactive tasks"],
        available=False,  # Limited availability
    ),
    "openai-gpt-4.1": ModelPricing(
        model_name="openai-gpt-4.1",
        provider="OpenAI",
        input_credits=1.00,
        output_credits=4.00,
        category="medium",
        context_window=128000,
        best_for=["General purpose", "Content generation", "Analysis"],
        supports_vision=True,
        available=True,  # Available in Azure regions
    ),
    "openai-o4-mini": ModelPricing(
        model_name="openai-o4-mini",
        provider="OpenAI",
        input_credits=0.55,
        output_credits=2.20,
        category="medium",
        context_window=128000,
        best_for=["Reasoning tasks", "Math problems", "Logical analysis"],
        available=False,  # Limited availability
    ),
    
    # Anthropic Claude Models
    "claude-4-5-haiku": ModelPricing(
        model_name="claude-4-5-haiku",
        provider="Anthropic",
        input_credits=0.55,
        output_credits=2.75,
        category="small",
        context_window=200000,
        best_for=["Fast responses", "Simple tasks", "Cost-effective"],
        available=False,  # Limited availability
    ),
    "claude-3-5-sonnet": ModelPricing(
        model_name="claude-3-5-sonnet",
        provider="Anthropic",
        input_credits=1.50,
        output_credits=7.50,
        category="large",
        context_window=200000,
        best_for=["Complex analysis", "Long documents", "Nuanced understanding"],
        supports_vision=True,
        available=True,
    ),
    "claude-3-7-sonnet": ModelPricing(
        model_name="claude-3-7-sonnet",
        provider="Anthropic",
        input_credits=1.50,
        output_credits=7.50,
        category="large",
        context_window=200000,
        best_for=["Complex analysis", "Long documents", "Nuanced understanding"],
        supports_vision=True,
        available=False,  # Limited availability
    ),
    "claude-4-sonnet": ModelPricing(
        model_name="claude-4-sonnet",
        provider="Anthropic",
        input_credits=1.50,
        output_credits=7.50,
        category="large",
        context_window=200000,
        best_for=["Complex analysis", "Long documents", "Nuanced understanding"],
        supports_vision=True,
        available=False,  # Limited availability
    ),
    "claude-4-5-sonnet": ModelPricing(
        model_name="claude-4-5-sonnet",
        provider="Anthropic",
        input_credits=1.65,
        output_credits=8.25,
        category="large",
        context_window=200000,
        best_for=["Latest capabilities", "Complex reasoning", "Vision tasks"],
        supports_vision=True,
        available=False,  # Limited availability
    ),
    "claude-4-opus": ModelPricing(
        model_name="claude-4-opus",
        provider="Anthropic",
        input_credits=7.50,
        output_credits=37.50,
        category="premium",
        context_window=200000,
        best_for=["Most complex tasks", "Highest quality", "Research"],
        supports_vision=True,
        available=False,  # Limited availability
    ),
    
    # Meta Llama Models
    "snowflake-llama-3.3-70b": ModelPricing(
        model_name="snowflake-llama-3.3-70b",
        provider="Meta (Snowflake optimized)",
        input_credits=0.29,
        output_credits=0.29,
        category="small",
        context_window=128000,
        best_for=["General tasks", "Cost-effective", "Good quality/price ratio"],
        available=True,
    ),
    "snowflake-llama-3.1-405b": ModelPricing(
        model_name="snowflake-llama-3.1-405b",
        provider="Meta (Snowflake optimized)",
        input_credits=0.96,
        output_credits=0.96,
        category="medium",
        context_window=128000,
        best_for=["Complex reasoning", "Large context", "Open source preference"],
        available=True,
    ),
    "llama3.1-70b": ModelPricing(
        model_name="llama3.1-70b",
        provider="Meta",
        input_credits=0.29,
        output_credits=0.29,
        category="small",
        context_window=128000,
        best_for=["General tasks", "Balanced performance"],
        available=True,
    ),
    "llama3.1-8b": ModelPricing(
        model_name="llama3.1-8b",
        provider="Meta",
        input_credits=0.03,
        output_credits=0.03,
        category="small",
        context_window=128000,
        best_for=["Simple tasks", "Very high volume", "Lowest cost"],
        available=True,
    ),
    
    # Mistral Models
    "mistral-large2": ModelPricing(
        model_name="mistral-large2",
        provider="Mistral AI",
        input_credits=1.00,
        output_credits=3.00,
        category="medium",
        context_window=128000,
        best_for=["European data compliance", "Multilingual", "Code"],
        available=True,
    ),
    "mistral-7b": ModelPricing(
        model_name="mistral-7b",
        provider="Mistral AI",
        input_credits=0.05,
        output_credits=0.05,
        category="small",
        context_window=32000,
        best_for=["Simple tasks", "Very high volume", "Budget-friendly"],
        available=True,
    ),
    "mixtral-8x7b": ModelPricing(
        model_name="mixtral-8x7b",
        provider="Mistral AI",
        input_credits=0.11,
        output_credits=0.11,
        category="small",
        context_window=32000,
        best_for=["Balanced performance", "General tasks", "Cost-effective"],
        available=True,
    ),
    "pixtral-large": ModelPricing(
        model_name="pixtral-large",
        provider="Mistral AI",
        input_credits=1.00,
        output_credits=3.00,
        category="medium",
        context_window=128000,
        best_for=["Vision tasks", "Image analysis", "Multimodal"],
        supports_vision=True,
        available=False,  # Limited availability
    ),
    
    # Snowflake Models
    "snowflake-arctic": ModelPricing(
        model_name="snowflake-arctic",
        provider="Snowflake",
        input_credits=0.84,
        output_credits=0.84,
        category="medium",
        context_window=4096,
        best_for=["Enterprise tasks", "Snowflake native", "SQL generation"],
        available=True,
    ),
    
    # DeepSeek Models
    "deepseek-r1": ModelPricing(
        model_name="deepseek-r1",
        provider="DeepSeek",
        input_credits=0.55,
        output_credits=2.19,
        category="medium",
        context_window=64000,
        best_for=["Reasoning", "Math", "Coding"],
        available=True,
    ),
}


# Task-specific function pricing (Credits per 1M tokens)
FUNCTION_PRICING = {
    "AI_SENTIMENT": 1.60,
    "AI_AGG": 1.60,
    "AI_CLASSIFY": 1.39,
    "AI_EXTRACT": 5.00,
    "AI_FILTER": 1.39,
    "AI_REDACT": 0.63,
    "AI_SUMMARIZE_AGG": 1.60,
    "AI_TRANSCRIBE": 1.30,
    "AI_TRANSLATE": 1.50,
    "SENTIMENT": 0.08,  # Legacy function
    "SUMMARIZE": 0.10,  # Legacy function
    "EXTRACT_ANSWER": 0.08,  # Legacy function
    "TRANSLATE": 1.50,  # Legacy function
    "GUARD": 0.25,  # Cortex Guard
}


# Embedding model pricing
EMBEDDING_PRICING = {
    "snowflake-arctic-embed-l": 0.05,  # Credits per 1M tokens
    "snowflake-arctic-embed-m": 0.03,
    "e5-base-v2": 0.03,
    "voyage-multilingual-2": 0.10,
}


# Other service pricing
OTHER_SERVICE_PRICING = {
    "cortex_analyst": {"rate": 67, "unit": "credits per 1,000 messages"},
    "cortex_search_serving": {"rate": 6.3, "unit": "credits per GB/month indexed"},
    "ai_parse_document_layout": {"rate": 3.33, "unit": "credits per 1,000 pages"},
    "ai_parse_document_ocr": {"rate": 0.5, "unit": "credits per 1,000 pages"},
    "document_ai": {"rate": 8, "unit": "credits per hour compute"},
}


def get_models_dataframe() -> pd.DataFrame:
    """Return all models as a pandas DataFrame for display."""
    data = []
    for model_name, pricing in CORTEX_MODELS.items():
        data.append({
            "Model": model_name,
            "Provider": pricing.provider,
            "Input (credits/1M)": pricing.input_credits,
            "Output (credits/1M)": pricing.output_credits,
            "Category": pricing.category,
            "Context Window": f"{pricing.context_window:,}",
            "Vision": "✓" if pricing.supports_vision else "",
            "Available": "✓" if pricing.available else "Limited",
            "Best For": ", ".join(pricing.best_for[:2]),
        })
    return pd.DataFrame(data)


def get_available_models() -> list[str]:
    """Get list of models that are currently available for COMPLETE function."""
    return [name for name, pricing in CORTEX_MODELS.items() if pricing.available]


def get_model_by_category(category: str) -> list[ModelPricing]:
    """Get all models in a specific category."""
    return [m for m in CORTEX_MODELS.values() if m.category == category]


def get_cheapest_models(n: int = 5) -> list[ModelPricing]:
    """Get the n cheapest models by input token cost."""
    sorted_models = sorted(CORTEX_MODELS.values(), key=lambda m: m.input_credits)
    return sorted_models[:n]


def get_models_for_task(task_type: str) -> list[ModelPricing]:
    """Get recommended models for a specific task type."""
    task_keywords = {
        "classification": ["classification", "classify", "categorize"],
        "sentiment": ["sentiment", "emotion", "tone"],
        "summarization": ["summary", "summarize", "condense"],
        "extraction": ["extract", "parse", "identify"],
        "translation": ["translate", "language", "multilingual"],
        "code": ["code", "programming", "sql"],
        "reasoning": ["reasoning", "logic", "math", "complex"],
        "vision": ["image", "vision", "visual", "picture"],
        "chat": ["chat", "conversation", "interactive"],
    }
    
    task_lower = task_type.lower()
    matching_models = []
    
    for model in CORTEX_MODELS.values():
        for use_case in model.best_for:
            if any(keyword in use_case.lower() or keyword in task_lower 
                   for keywords in task_keywords.values() 
                   for keyword in keywords 
                   if keyword in task_lower):
                matching_models.append(model)
                break
    
    # If no specific matches, return cheapest models
    if not matching_models:
        return get_cheapest_models(5)
    
    # Sort by input cost
    return sorted(matching_models, key=lambda m: m.input_credits)


def calculate_cost(
    model_name: str,
    input_tokens: int,
    output_tokens: int = 0,
    credit_price_usd: float = 3.0
) -> dict:
    """
    Calculate the cost for a given number of tokens.
    
    Args:
        model_name: Name of the Cortex model
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens (for generative functions)
        credit_price_usd: Price per credit in USD (varies by edition/contract)
    
    Returns:
        dict with credits and USD cost breakdown
    """
    if model_name not in CORTEX_MODELS:
        raise ValueError(f"Unknown model: {model_name}")
    
    pricing = CORTEX_MODELS[model_name]
    
    input_credits = (input_tokens / 1_000_000) * pricing.input_credits
    output_credits = (output_tokens / 1_000_000) * pricing.output_credits
    total_credits = input_credits + output_credits
    
    return {
        "model": model_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_credits": round(input_credits, 4),
        "output_credits": round(output_credits, 4),
        "total_credits": round(total_credits, 4),
        "input_cost_usd": round(input_credits * credit_price_usd, 2),
        "output_cost_usd": round(output_credits * credit_price_usd, 2),
        "total_cost_usd": round(total_credits * credit_price_usd, 2),
    }


def estimate_tokens_from_text(text: str) -> int:
    """
    Rough estimate of tokens from text.
    Rule of thumb: 1 token ≈ 4 characters or ~0.75 words.
    For accurate counts, use AI_COUNT_TOKENS in Snowflake.
    """
    return max(1, len(text) // 4)


def compare_models(
    models: list[str],
    input_tokens: int,
    output_tokens: int = 0,
    credit_price_usd: float = 3.0
) -> pd.DataFrame:
    """Compare costs across multiple models."""
    results = []
    for model in models:
        if model in CORTEX_MODELS:
            cost = calculate_cost(model, input_tokens, output_tokens, credit_price_usd)
            results.append(cost)
    return pd.DataFrame(results)
