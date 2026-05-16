"""Fixture: triggers pack-ai-app rules."""

import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

client = Anthropic()

SYSTEM_PROMPT = """
You are a senior assistant. Your role is to help the user with their task.
Follow these rules carefully:
1. Always be helpful and concise. Never use jargon when plain language works.
2. Do not hallucinate or make up information. If you do not know, say so explicitly.
3. Cite sources where possible. Reference the document, section, and line number.
4. Use structured output when the user asks for it. JSON is preferred over prose.
5. Be polite but professional. Avoid filler phrases and apology spirals.
6. When asked to write code, follow the project's conventions about style and naming.
7. Verify your assumptions before proceeding. Ask clarifying questions when ambiguous.
8. Provide examples when explaining concepts. Concrete beats abstract.
9. Keep responses focused on the user's actual question, not adjacent topics.
10. Track context budget: when context approaches the model limit, summarize earlier turns.
11. When the user asks for a tradeoff, present at least two options and recommend one.
12. Do not narrate your internal deliberation. Output decisions, not thinking.
13. Default to writing no comments in code unless the WHY is non-obvious.
14. If a file path is referenced, use markdown link syntax for navigability.
15. Match response length to task: a simple question gets a direct answer.
"""  # over 800 chars; no cache_control in this file


def chat(user_prompt: str) -> str:
    logger.info(f"received prompt: {user_prompt}")  # logs raw prompt — PII risk

    response = client.messages.create(
        model="claude-opus-4-7",  # hardcoded model ID
        # missing max_tokens
        messages=[
            {"role": "user", "content": user_prompt},
        ],
        system=SYSTEM_PROMPT,
    )
    return response.content[0].text
