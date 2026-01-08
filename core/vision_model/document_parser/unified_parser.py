import base64
import json
import logging
import time
import os
from typing import Dict, List, Optional, Tuple, Union, Literal

from core.vision_model.document_parser.models import UnifiedExtractionResponse
from core.vision_model.document_parser.prompt import unified_system_prompt
from json_repair import repair_json

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class UnifiedParser:
    """
    Unified parser that can extract multiple logical documents (payslips or settlements) 
    from a single PDF.
    """
    
    def __init__(
        self,
        provider: Literal["openai", "gemini"] = "gemini",
        model: str = "gemini-3-flash-preview",
        api_key: Optional[str] = None,
        project: str = "valeria-test-474315",
        location: str = "europe-southwest1",
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.project = project
        self.location = "global" if model.startswith("gemini-3") else location
        
        if self.provider == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError("google-genai package is required for Gemini unified parsing")
            
            if api_key:
                self.client = genai.Client(api_key=api_key)
            else:
                self.client = genai.Client(
                    vertexai=True, project=self.project, location=self.location
                )
        elif self.provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=self.api_key or os.getenv("OPENAI_API_KEY"))

    def _clean_json_string(self, json_str: str) -> str:
        return json_str.strip().replace("```json", "").replace("```", "").strip()

    def parse_with_usage(
        self, 
        pdf_bytes: bytes, 
        text_pdf: str = ""
    ) -> Tuple[UnifiedExtractionResponse, Dict]:
        """
        Extracts multiple logical documents from PDF.
        """
        if self.provider == "gemini":
            return self._parse_gemini(pdf_bytes, text_pdf)
        else:
            return self._parse_openai(pdf_bytes, text_pdf)

    def _parse_gemini(self, pdf_bytes: bytes, text_pdf: str) -> Tuple[UnifiedExtractionResponse, Dict]:
        pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="Please extract all logical documents from this PDF."),
                    types.Part.from_text(text=f"Raw text for reference: ```{text_pdf}```"),
                    pdf_part
                ]
            )
        ]

        generate_config = types.GenerateContentConfig(
            temperature=0.1,
            system_instruction=[types.Part.from_text(text=unified_system_prompt)],
            response_mime_type="application/json",
            response_schema=UnifiedExtractionResponse.model_json_schema(),
            thinking_config=types.ThinkingConfig(thinking_level="low"),
        )

        if self.model.startswith("gemini-3"):
            generate_config.thinking_config = types.ThinkingConfig(thinking_level="low")

        start_time = time.time()
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=generate_config,
        )
        elapsed = time.time() - start_time

        result_text = self._clean_json_string(response.text or "{}")
        try:
            data_dict = json.loads(repair_json(result_text))
            parsed_response = UnifiedExtractionResponse(**data_dict)
        except Exception as e:
            logging.error(f"Failed to parse UnifiedExtractionResponse: {e}")
            raise ValueError(f"Invalid LLM response for Unified parser: {e}")

        usage = response.usage_metadata
        usage_info = {
            "input_tokens": usage.prompt_token_count if usage else 0,
            "output_tokens": usage.candidates_token_count if usage else 0,
            "total_tokens": usage.total_token_count if usage else 0,
            "parsing_time_seconds": elapsed
        }

        return parsed_response, usage_info

    def _parse_openai(self, pdf_bytes: bytes, text_pdf: str) -> Tuple[UnifiedExtractionResponse, Dict]:
        # Implementation for OpenAI if needed
        raise NotImplementedError("OpenAI unified parsing not yet implemented in this class")

def create_unified_parser(
    provider: str = "gemini",
    model: str = "gemini-3-flash-preview",
    api_key: Optional[str] = None
) -> UnifiedParser:
    return UnifiedParser(provider=provider, model=model, api_key=api_key)
