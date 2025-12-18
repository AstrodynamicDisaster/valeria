from abc import ABC, abstractmethod
import base64
import json
import os
from typing import Dict, Optional, Tuple

from json_repair import repair_json

from core.vision_model.payslips.payslip_models import PayslipData
from core.vision_model.payslips.prompt import system_prompt

try:
    from google import genai
    from google.genai import types
    from google.auth import default as gcloud_default
    from google.auth.exceptions import DefaultCredentialsError

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    gcloud_default = None
    DefaultCredentialsError = Exception

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class BasePayslipParser(ABC):
    """
    Abstract base class for payslip parsers using vision models.

    All parsers should implement the `parse` method which takes PDF bytes
    and optional extracted text, and returns a JSON string.
    """

    def __init__(self, system_prompt: str):
        """
        Initialize the parser with a system prompt.

        Args:
            system_prompt: The system prompt to use for extraction
        """
        self.system_prompt = system_prompt

    @abstractmethod
    def parse(self, pdf_bytes: bytes, text_pdf: str = "") -> str:
        """
        Parse a payslip PDF and return JSON string.

        Args:
            pdf_bytes: Raw bytes of the PDF file
            text_pdf: Optional extracted text from the PDF (for context)

        Returns:
            JSON string with extracted payslip data
        """
        pass

    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string by removing markdown code blocks."""
        return json_str.strip().replace("```json", "").replace("```", "").strip()

    def _repair_and_parse_json(self, json_str: str) -> Dict:
        """
        Repair and parse JSON string, handling errors.
        """
        try:
            cleaned = self._clean_json_string(json_str)
            repaired = repair_json(cleaned, skip_json_loads=True, ensure_ascii=False)
            return json.loads(repaired)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e

    def parse_to_dict(self, pdf_bytes: bytes, text_pdf: str = "") -> Dict:
        """
        Parse a payslip PDF and return as dictionary.

        Args:
            pdf_bytes: Raw bytes of the PDF file
            text_pdf: Optional extracted text from the PDF (for context)

        Returns:
            Dictionary with extracted payslip data

        Raises:
            ValueError: If JSON parsing fails
        """
        json_str = self.parse(pdf_bytes, text_pdf)
        return self._repair_and_parse_json(json_str)

    def parse_with_usage(
        self, pdf_bytes: bytes, text_pdf: str = ""
    ) -> Tuple[Dict, Dict]:
        """
        Parse a payslip PDF and return dictionary with usage information.

        Args:
            pdf_bytes: Raw bytes of the PDF file
            text_pdf: Optional extracted text from the PDF (for context)

        Returns:
            Tuple of (data_dict, usage_info)
            - data_dict: Dictionary with extracted payslip data
            - usage_info: Dictionary with usage metrics (tokens, etc.)

        Raises:
            ValueError: If JSON parsing fails
        """
        json_str, usage_info = self.parse_with_usage_info(pdf_bytes, text_pdf)
        data_dict = self._repair_and_parse_json(json_str)
        return data_dict, usage_info

    @abstractmethod
    def parse_with_usage_info(
        self, pdf_bytes: bytes, text_pdf: str = ""
    ) -> Tuple[str, Dict]:
        """
        Parse a payslip PDF and return JSON string with usage information.

        Args:
            pdf_bytes: Raw bytes of the PDF file
            text_pdf: Optional extracted text from the PDF (for context)

        Returns:
            Tuple of (json_str, usage_info)
            - json_str: JSON string with extracted payslip data
            - usage_info: Dictionary with usage metrics (input_tokens, output_tokens, etc.)
        """
        pass

    def parse_to_model(self, pdf_bytes: bytes, text_pdf: str = "") -> PayslipData:
        """
        Parse a payslip PDF and return as PayslipData model.

        Args:
            pdf_bytes: Raw bytes of the PDF file
            text_pdf: Optional extracted text from the PDF (for context)

        Returns:
            PayslipData model instance with extracted payslip data

        Raises:
            ValueError: If JSON parsing or model validation fails
        """
        data_dict = self.parse_to_dict(pdf_bytes, text_pdf)
        payslip_data = PayslipData(**data_dict)
        payslip_data.verify_and_correct_aportacion_empresa_total()
        return payslip_data


class OpenAIPayslipParser(BasePayslipParser):
    """Payslip parser using OpenAI's vision models."""

    def __init__(
        self, system_prompt: str, model: str = "gpt-5.1", api_key: Optional[str] = None
    ):

        if not OPENAI_AVAILABLE:
            raise ImportError("openai package is required for OpenAIPayslipParser")

        super().__init__(system_prompt)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key must be provided or set in OPENAI_API_KEY env var"
            )

        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)

    def parse(self, pdf_bytes: bytes, text_pdf: str = "") -> str:
        """Parse payslip using OpenAI API."""
        json_str, _ = self.parse_with_usage_info(pdf_bytes, text_pdf)
        return json_str

    def parse_with_usage_info(
        self, pdf_bytes: bytes, text_pdf: str = ""
    ) -> Tuple[str, Dict]:
        """Parse payslip using OpenAI API and return usage information."""
        base64_string = base64.b64encode(pdf_bytes).decode("utf-8")

        # Build user message parts
        user_parts = [
            {
                "type": "input_text",
                "text": "I have this payslip in PDF, can you process it?",
            },
            {
                "type": "input_text",
                "text": f"This is the text of the payslip in raw (for you to help): ```{text_pdf}```",
            },
            {
                "type": "input_file",
                "filename": "payslip.pdf",
                "file_data": f"data:application/pdf;base64,{base64_string}",
            },
        ]

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_parts},
        ]

        # Use responses.parse for structured output
        response = self.client.responses.parse(
            model=self.model,
            text={"format": {"type": "json_object"}},
            input=messages,
        )

        json_str = response.output[0].content[0].text

        # Extract usage information from response.usage
        # OpenAI responses.parse returns usage with input_tokens, output_tokens, total_tokens
        usage_info = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

        if hasattr(response, "usage") and response.usage is not None:
            usage = response.usage

            # Extract input_tokens (OpenAI uses input_tokens, not prompt_tokens)
            if hasattr(usage, "input_tokens"):
                usage_info["input_tokens"] = usage.input_tokens

            # Extract output_tokens (OpenAI uses output_tokens, not completion_tokens)
            if hasattr(usage, "output_tokens"):
                usage_info["output_tokens"] = usage.output_tokens

            # Extract total_tokens
            if hasattr(usage, "total_tokens"):
                usage_info["total_tokens"] = usage.total_tokens

            # If total is missing, calculate it
            if usage_info["total_tokens"] == 0 and (
                usage_info["input_tokens"] > 0 or usage_info["output_tokens"] > 0
            ):
                usage_info["total_tokens"] = (
                    usage_info["input_tokens"] + usage_info["output_tokens"]
                )

        return json_str, usage_info


def _is_gemini_3_model(model: str) -> bool:
    """Check if the model is a Gemini 3 model."""
    return model.startswith("gemini-3")


class GeminiPayslipParser(BasePayslipParser):
    """
    Payslip parser using Google's Gemini vision models.

    Uses Google GenAI API with Gemini models that support
    vision and structured output.
    """

    def __init__(
        self,
        system_prompt: str,
        project: str = "valeria-test-474315",
        location: str = "europe-southwest1",
        model: str = "gemini-2.5-pro",
        temperature: float = 0.25,
        top_p: float = 0.95,
        max_output_tokens: int = 65535,
        thinking_budget: int = 350,
        api_key: Optional[str] = None,
    ):
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-genai package is required for GeminiPayslipParser"
            )

        super().__init__(system_prompt)
        self.project = project
        # Force location to "global" for gemini-3 models
        self.location = "global" if _is_gemini_3_model(model) else location
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens
        self.thinking_budget = thinking_budget

        # Initialize client
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            # Check Google Cloud authentication
            self._check_gcloud_authentication()
            self.client = genai.Client(
                vertexai=True, project=project, location=self.location
            )

    def _check_gcloud_authentication(self) -> None:
        """
        Verify that Google Cloud authentication is configured.
        Raises RuntimeError: If Google Cloud credentials are not found
        """
        if gcloud_default is None:
            raise RuntimeError(
                "Google Cloud authentication check requires google-auth package. "
                "Install it with: pip install google-auth"
            )

        try:
            credentials, project = gcloud_default()
            if not credentials:
                raise RuntimeError(
                    "Google Cloud credentials not found. "
                    "Please authenticate using: gcloud auth application-default login"
                )
        except DefaultCredentialsError as e:
            raise RuntimeError(
                f"Google Cloud authentication failed: {e}. "
                "Please authenticate using: gcloud auth application-default login"
            ) from e

    def _get_safety_settings(self):
        """Get Gemini safety settings (all disabled for document processing)."""
        if not GEMINI_AVAILABLE:
            return []
        return [
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
            ),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ]

    def parse(self, pdf_bytes: bytes, text_pdf: str = "") -> str:
        """Parse payslip using Gemini API."""
        json_str, _ = self.parse_with_usage_info(pdf_bytes, text_pdf)
        return json_str

    def parse_with_usage_info(
        self, pdf_bytes: bytes, text_pdf: str = ""
    ) -> Tuple[str, Dict]:
        """Parse payslip using Gemini API and return usage information."""
        pdf_part = types.Part.from_bytes(
            data=pdf_bytes,
            mime_type="application/pdf",
        )

        # print(f"Text PDF: {text_pdf}")

        # Build content
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text="I have this payslip in PDF, can you process it?"
                    ),
                    # types.Part.from_text(
                    #     text=f"This is the text of the payslip in raw (for you to help): ```{text_pdf}```"
                    # ),
                    pdf_part,
                ],
            ),
        ]

        # Configure thinking config based on model version
        if _is_gemini_3_model(self.model):
            thinking_config = types.ThinkingConfig(thinking_level="LOW")
        else:
            thinking_config = types.ThinkingConfig(thinking_budget=self.thinking_budget)
        
        # Configure generation
        generate_content_config = types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            max_output_tokens=self.max_output_tokens,
            safety_settings=self._get_safety_settings(),
            system_instruction=[types.Part.from_text(text=self.system_prompt)],
            thinking_config=thinking_config,
            response_mime_type="application/json",
            response_schema=PayslipData.model_json_schema(),
        )

        # Generate content (non-streaming)
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=generate_content_config,
        )
        
        result = response.text or ""
        usage_metadata = response.usage_metadata if hasattr(response, "usage_metadata") else None

        # Extract usage information from usage_metadata
        # Gemini returns usage_metadata with prompt_token_count, candidates_token_count, total_token_count
        usage_info = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

        if usage_metadata:
            # Extract prompt_token_count (input tokens)
            if hasattr(usage_metadata, "prompt_token_count"):
                usage_info["input_tokens"] = usage_metadata.prompt_token_count

            # Extract candidates_token_count (output tokens)
            if hasattr(usage_metadata, "candidates_token_count"):
                usage_info["output_tokens"] = usage_metadata.candidates_token_count

            # Extract total_token_count
            if hasattr(usage_metadata, "total_token_count"):
                usage_info["total_tokens"] = usage_metadata.total_token_count

            # If total is missing, calculate it
            if usage_info["total_tokens"] == 0 and (
                usage_info["input_tokens"] > 0 or usage_info["output_tokens"] > 0
            ):
                usage_info["total_tokens"] = (
                    usage_info["input_tokens"] + usage_info["output_tokens"]
                )

        # Clean up markdown code blocks
        json_str = self._clean_json_string(result)
        return json_str, usage_info


# Convenience functions to create parsers with default prompts
def create_openai_parser(
    api_key: Optional[str] = None,
    model: str = "gpt-5.1",
) -> OpenAIPayslipParser:
    """
    Create an OpenAI parser with default prompts.

    Args:
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        model: Model name to use

    Returns:
        Configured OpenAIPayslipParser instance
    """
    return OpenAIPayslipParser(
        system_prompt=system_prompt, api_key=api_key, model=model
    )


def create_gemini_parser(
    project: str = "valeria-test-474315",
    location: str = "europe-southwest1",
    model: str = "gemini-2.5-pro",
) -> GeminiPayslipParser:
    """
    Create a Gemini parser with default prompts.

    Args:
        project: Google Cloud project ID
        location: Google Cloud location
        api_key: Optional API key (uses vertexai=True if not provided)
        model: Model name to use

    Returns:
        Configured GeminiPayslipParser instance
    """
    return GeminiPayslipParser(
        system_prompt=system_prompt, project=project, location=location, model=model
    )
