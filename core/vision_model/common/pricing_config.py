"""
Pricing configuration for AI models.

Update these values with the latest pricing from provider websites.
Prices are per 1,000 tokens unless otherwise noted.
"""

# OpenAI Pricing (per 1,000 tokens)
# Update these values from: https://openai.com/api/pricing/
# Note: Prices are per 1,000 tokens (convert from per 1M: divide by 1000)
OPENAI_PRICING = {
    "gpt-5.2": {
        "input": 0.00175,  # $1.75 per 1M tokens = $0.00175 per 1K tokens
        "cached_input": 0.000175,  # $0.175 per 1M tokens = $0.000175 per 1K tokens
        "output": 0.014,  # $14.00 per 1M tokens = $0.014 per 1K tokens
    },
    "gpt-5.1": {
        "input": 0.00125,  # $1.25 per 1M tokens = $0.00125 per 1K tokens
        "cached_input": 0.000125,  # $0.125 per 1M tokens = $0.000125 per 1K tokens
        "output": 0.01,  # $10.00 per 1M tokens = $0.01 per 1K tokens
    },
    "gpt-5": {
        "input": 0.00125,  # $1.25 per 1M tokens = $0.00125 per 1K tokens
        "cached_input": 0.000125,  # $0.125 per 1M tokens = $0.000125 per 1K tokens
        "output": 0.01,  # $10.00 per 1M tokens = $0.01 per 1K tokens
    },
    "gpt-5-mini": {
        "input": 0.00025,  # $0.25 per 1M tokens = $0.00025 per 1K tokens
        "cached_input": 0.000025,  # $0.025 per 1M tokens = $0.000025 per 1K tokens
        "output": 0.002,  # $2.00 per 1M tokens = $0.002 per 1K tokens
    },
}

# Google Gemini Pricing (per 1,000 tokens)
# Update these values from: https://ai.google.dev/pricing
# Note: Prices are per 1,000 tokens (convert from per 1M: divide by 1000)
# For prompts ≤ 200k tokens (standard pricing)
GEMINI_PRICING = {
    "gemini-2.5-pro": {
        "input": 0.00125,  # $1.25 per 1M tokens = $0.00125 per 1K tokens (prompts ≤ 200k)
        "output": 0.01,  # $10.00 per 1M tokens = $0.01 per 1K tokens (output includes thinking tokens)
    },
    "gemini-2.5-flash": {
        "input": 0.0003,  # $0.30 per 1M tokens = $0.0003 per 1K tokens (prompts ≤ 200k)
        "output": 0.0025,  # $2.50 per 1M tokens = $0.0025 per 1K tokens (output includes thinking tokens)
    },
    "gemini-3-pro-preview": {
        "input": 0.002,  # $2.00 per 1M tokens = $0.002 per 1K tokens (prompts ≤ 200k)
        "output": 0.012,  # $12.00 per 1M tokens = $0.012 per 1K tokens (output includes thinking tokens)
    },
    "gemini-3-flash-preview": {
        "input": 0.0005,  # $0.50 per 1M tokens = $0.0005 per 1K tokens
        "output": 0.003,  # $3.00 per 1M tokens = $0.003 per 1K tokens
    },
}


def get_openai_pricing(model: str) -> dict:
    """Get pricing for OpenAI model."""
    return OPENAI_PRICING.get(model, {"input": 0.0, "output": 0.0})


def get_gemini_pricing(model: str) -> dict:
    """Get pricing for Gemini model."""
    return GEMINI_PRICING.get(model, {"input": 0.0, "output": 0.0})


def calculate_cost(input_tokens: int, output_tokens: int, input_price: float, output_price: float) -> float:
    """
    Calculate cost based on token counts and pricing.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        input_price: Price per 1,000 input tokens
        output_price: Price per 1,000 output tokens
    
    Returns:
        Total cost in USD
    """
    input_cost = (input_tokens / 1000.0) * input_price
    output_cost = (output_tokens / 1000.0) * output_price
    return input_cost + output_cost




