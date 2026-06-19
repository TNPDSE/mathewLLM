import json
import logging
from typing import List
import re
from anthropic import AnthropicFoundry
from pydantic import BaseModel, ValidationError
from app.utils import settings


# =====================================================
# Azure Claude Configuration
# =====================================================
ENDPOINT = settings.ENDPOINT
API_KEY = settings.API_KEY
DEPLOYMENT_NAME = settings.DEPLOYMENT_NAME
AUDIT_FILE = settings.AUDIT_FILE

client = AnthropicFoundry(
    api_key=API_KEY,
    base_url=ENDPOINT
)


# =====================================================
# Logging
# =====================================================

logging.basicConfig(
    filename="audit_qa.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =====================================================
# Response Models
# =====================================================

class Reference(BaseModel):
    audit_id: str
    question_number: int
    question: str


class AuditResponse(BaseModel):
    LLM_answer: str
    svg_string: str
    status: str
    reference: List[Reference]


# =====================================================
# Load Audit Once
# =====================================================



LAST_INTERACTION = {
    "question": None,
    "response": None
}

with open(AUDIT_FILE, "r", encoding="utf-8") as f:
    AUDIT_DATA = json.load(f)

# Compact JSON for token efficiency
AUDIT_TEXT = json.dumps(
    AUDIT_DATA,
    separators=(",", ":")
)

logger.info(
    json.dumps(
        {
            "event": "audit_loaded",
            "audit_records": len(AUDIT_DATA),
            "audit_characters": len(AUDIT_TEXT)
        }
    )
)

def clean_json_response(text: str) -> str:
    text = text.strip()

    # Remove ```json
    text = re.sub(r"^```json\s*", "", text)

    # Remove ```
    text = re.sub(r"\s*```$", "", text)

    return text.strip()

def is_valid_svg(svg: str) -> bool:

    svg = svg.strip()

    return (
        svg.startswith("<svg")
        and svg.endswith("</svg>")
    )

def clean_svg(svg_text: str) -> str:

    if not svg_text:
        return ""

    svg_text = svg_text.strip()

    svg_text = re.sub(
        r"^```(?:svg|xml)?\s*",
        "",
        svg_text,
        flags=re.IGNORECASE
    )

    svg_text = re.sub(
        r"\s*```$",
        "",
        svg_text
    )

    return svg_text.strip()

# =====================================================
# Prompt Builder
# =====================================================

def build_prompt(user_question: str) -> str:

    previous_context = ""

    if (
        LAST_INTERACTION["question"] is not None
        and LAST_INTERACTION["response"] is not None
    ):
        previous_context = f"""

    PREVIOUS USER QUESTION:
    {LAST_INTERACTION['question']}

    PREVIOUS ASSISTANT RESPONSE:
    {json.dumps(LAST_INTERACTION['response'])}
    """

    return f"""
You are an Audit QA Assistant.
Answer ONLY using the audit data provided below.

AUDIT DATA:
{AUDIT_TEXT}

PREVIOUS INTERACTION:
{previous_context}

USER QUESTION:
{user_question}


Result Schema:

{{
  "LLM_answer": "string",
  "svg_string": "string",
  "status": "success",
  "reference": [
    {{
      "audit_id": "string",
      "question_number": 0,
      "question": "string"
    }}
  ]
}}

Rules:

1. Use only information present in the audit.
2. Never make up information.
3. Every answer must include all audit questions used.
4. Populate reference using:
   - audit_id
   - question number
   - question text

5. If information is unavailable return EXACTLY:
{{
  "LLM_answer": "No information found in the audit.",
  "svg_string": "",
  "status": "not_found",
  "reference": []
}}

6. svg_string must be empty unless the user explicitly requests:
   - chart
   - graph
   - plot
   - trend
   - visualization

7. If chart/graph requested:
   - Generate SVG only
   - Put SVG markup inside svg_string
   - Do not use markdown
   - Do not use base64

8. If svg_string is populated:
    - svg_string must contain ONLY raw SVG markup.
    - Do not wrap SVG in markdown code fences.
    - Do not use ```svg or ```xml.
    - svg_string must start with <svg and end with </svg>.
    - The root svg element must include:
    - width="100%"
    - height="400"
    - a valid viewBox
    - Use readable labels and ensure text does not overlap.
    - Use a modern professional visual style suitable for business dashboards.
 
9. Response MUST contain JSON only. Do NOT wrap the JSON in markdown.
Do NOT use:
```json
...

10. Do not output any text outside JSON.
"""


# =====================================================
# Claude Call
# =====================================================

def ask_audit_question(user_question: str) -> dict:

    prompt = build_prompt(user_question)

    try:

        response = client.messages.create(
            model=DEPLOYMENT_NAME,
            max_tokens=7000,
            timeout= 300,
            temperature=0.0,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_text = response.content[0].text

        input_tokens = getattr(
            response.usage,
            "input_tokens",
            0
        )

        output_tokens = getattr(
            response.usage,
            "output_tokens",
            0
        )

        total_tokens = input_tokens + output_tokens

        logger.info(
            json.dumps(
                {
                    "question": user_question,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "status": "success"
                }
            )
        )

        try:

            cleaned_response = clean_json_response(response_text)
            parsed = json.loads(cleaned_response)

        except Exception:

            logger.error(
                json.dumps(
                    {
                        "question": user_question,
                        "status": "invalid_json",
                        "raw_response": response_text
                    }
                )
            )

            return {
                "LLM_answer": "Model returned invalid JSON.",
                "svg_string": "",
                "status": "error",
                "reference": []
            }

        try:

            validated = AuditResponse.model_validate(parsed)
            result = validated.model_dump()
            LAST_INTERACTION["question"] = user_question
            result["svg_string"] = clean_svg(result["svg_string"])
            if result["svg_string"] and not is_valid_svg(result["svg_string"]):
                logger.error(f"Invalid SVG generated: {result['svg_string'][:500]}")
                result["svg_string"] = ""
            LAST_INTERACTION["response"] = result

            return result
        except ValidationError as e:

            logger.error(
                json.dumps(
                    {
                        "question": user_question,
                        "status": "schema_validation_failed",
                        "error": str(e),
                        "response": parsed
                    }
                )
            )

            return {
                "LLM_answer": "Response schema validation failed.",
                "svg_string": "",
                "status": "error",
                "reference": []
            }

    except Exception as e:

        logger.exception("Claude request failed")

        return {
            "LLM_answer": str(e),
            "svg_string": "",
            "status": "error",
            "reference": []
        }