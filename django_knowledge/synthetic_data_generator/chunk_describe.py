from pydantic import BaseModel, Field
from typing import List
import litellm
from loguru import logger


class CodeDescriptions(BaseModel):
    """Pydantic model for LLM response describing code functionality"""

    descriptions: List[str] = Field(
        description="List of descriptions of what this code does - focus on the main functionality, purpose, and key operations. Keep each description concise and informative. Avoid generic phrases like 'This code...' and instead focus on what the code actually does.",
        min_items=1,
        max_items=50,
    )


def generate_chunk_descriptions(code_content: str, model: str) -> CodeDescriptions:
    """Generate descriptions for a code chunk using LLM
    
    Args:
        code_content: The code content to analyze
        model: The LLM model to use for generation
        
    Returns:
        CodeDescriptions object containing the generated descriptions
        
    Raises:
        Exception: If the LLM call fails
    """
    prompt = f"""Analyze the following code chunk and generate a list of descriptions of what this code does. Focus on the main functionality and purpose.

Code:
```python
{code_content}
```

Provide concise descriptions of what this code accomplishes. Each description should be a clear, informative statement about the code's functionality.
"""

    try:
        resp = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes code and provides clear descriptions of its functionality.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1000,
            response_format=CodeDescriptions,
        )
        return CodeDescriptions.model_validate_json(resp.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise