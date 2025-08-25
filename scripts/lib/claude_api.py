"""
Claude AI API Integration

This module handles all interactions with the Claude AI API:
- API calls with proper error handling
- Response processing and content extraction
- Prompt construction and formatting
"""

import warnings
from typing import Optional

# Import anthropic only when needed (not when skipping API)
anthropic = None

# Suppress deprecation warnings for the Claude API
warnings.filterwarnings("ignore", category=DeprecationWarning)


def call_claude_api(prompt_content: str, questionnaire_content: str, 
                   policy_instructions_content: str, policy_content: str, 
                   api_key: str) -> str:
    """
    Call Claude Sonnet 4 API to generate JSON instructions.
    
    Args:
        prompt_content: Main AI prompt content
        questionnaire_content: Processed questionnaire data
        policy_instructions_content: Policy-specific processing instructions
        policy_content: Policy document content
        api_key: Claude API key
        
    Returns:
        Raw response text from Claude
        
    Raises:
        ImportError: If anthropic package is not available
        Exception: If API call fails
    """
    # Import anthropic here when actually needed
    global anthropic
    if anthropic is None:
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package is required for API calls. Install it with: pip install anthropic")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Construct the full prompt with the new JSON workflow
    full_prompt = _build_full_prompt(
        prompt_content, 
        questionnaire_content, 
        policy_instructions_content, 
        policy_content
    )

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Claude Sonnet model
            max_tokens=4000,
            temperature=0.1,  # Low temperature for consistent, accurate output
            messages=[{
                "role": "user",
                "content": full_prompt
            }]
        )
        
        return message.content[0].text
    
    except Exception as e:
        raise Exception(f"Claude API call failed: {e}")


def _build_full_prompt(prompt_content: str, questionnaire_content: str,
                      policy_instructions_content: str, policy_content: str) -> str:
    """
    Build the complete prompt for Claude API.
    
    Args:
        prompt_content: Main AI prompt content
        questionnaire_content: Processed questionnaire data
        policy_instructions_content: Policy-specific processing instructions
        policy_content: Policy document content
        
    Returns:
        Complete formatted prompt
    """
    return f"""
{prompt_content}

---

## PROCESSING INSTRUCTIONS (Policy Document Specific Rules):
{policy_instructions_content}

---

## INPUT DATA FOR PROCESSING

### QUESTIONNAIRE RESPONSES (CSV FORMAT):
```csv
{questionnaire_content}
```

### POLICY DOCUMENT CONTENT (FOR REFERENCE):
```
{policy_content[:2000]}...
[Document truncated for API efficiency - full content will be processed by automation system]
```

---

Please analyze the questionnaire data and generate the complete JSON file for automated policy customization according to the processing instructions above.

CRITICAL: Your response must include a properly formatted JSON structure that follows the exact format specified in the processing instructions.
"""
