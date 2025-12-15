"""
Document classifier using LLMs.

This module provides functionality to classify Spanish labor documents
as either payslips or settlements using OpenAI or Gemini models.
"""

import json
import os
from typing import Dict, Optional, Literal

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

from core.vision_model.document_classifier.models import ClassificationResult


# Document type classification prompt
CLASSIFICATION_PROMPT = """You are a document classifier for Spanish labor documents. Your task is to classify a document as either a regular payslip (nómina) or a termination settlement (finiquito/liquidación).

Based on the text content provided, determine the document type. Return ONLY a JSON object with the following structure:
{
  "document_type": "payslip" or "settlement",
  "confidence": "high" or "medium" or "low",
  "reasoning": "brief explanation of why this classification was chosen"
}

Key indicators for PAYSLIP (nómina):
- Contains "NÓMINA" or "NOMINA" in the title
- Shows monthly/periodic payroll information
- Contains sections like "DEVENGOS" (earnings), "DEDUCCIONES" (deductions), "APORTACIONES EMPRESA" (employer contributions)
- Shows a payroll period (desde/hasta dates)
- Contains salary breakdown with multiple items

Key indicators for SETTLEMENT (finiquito/liquidación):
- Contains "FINIQUITO", "LIQUIDACIÓN", "FECHA CESE", "CAUSA" (termination date/reason)
- Mentions termination of employment ("cesa en la prestación de sus servicios")
- Contains "liquidación de partes proporcionales" (proportional settlement)
- Shows settlement items like vacation pay, extra pay, indemnization
- Typically a one-time document, not periodic

Return ONLY the JSON object, no markdown, no explanations."""


class DocumentClassifier:
    """Classifies documents as payslip or settlement using an LLM."""
    
    def __init__(
        self,
        provider: Literal["openai", "gemini"] = "gemini",
        model: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        project: str = "valeria-test-474315",
        location: str = "europe-southwest1",
    ):
        """
        Initialize the document classifier.
        
        Args:
            provider: LLM provider to use ("openai" or "gemini")
            model: Model name to use
            api_key: API key (for OpenAI) or None (uses env var or Vertex AI)
            project: Google Cloud project ID (for Gemini with Vertex AI)
            location: Google Cloud location (for Gemini with Vertex AI)
        """
        self.provider = provider
        self.model = model
        
        if provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package is required for OpenAI classifier")
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY env var")
            self.client = openai.OpenAI(api_key=self.api_key)
        elif provider == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError("google-genai package is required for Gemini classifier")
            if api_key:
                self.client = genai.Client(api_key=api_key)
            else:
                self._check_gcloud_authentication()
                self.client = genai.Client(
                    vertexai=True,
                    project=project,
                    location=location
                )
        else:
            raise ValueError(f"Unknown provider: {provider}. Must be 'openai' or 'gemini'")
    
    def _check_gcloud_authentication(self) -> None:
        """Verify that Google Cloud authentication is configured."""
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
    
    def classify(self, text_doc: str) -> Dict[str, str]:
        """
        Classify a document based on its text content.
        
        Args:
            text_doc: Extracted text from the document
        
        Returns:
            Dictionary with keys: document_type, confidence, reasoning
        
        Raises:
            ValueError: If classification fails or returns invalid format
        """
        if self.provider == "openai":
            return self._classify_openai(text_doc)
        else:
            return self._classify_gemini(text_doc)
    
    def classify_to_model(self, text_doc: str) -> ClassificationResult:
        """
        Classify a document and return as ClassificationResult model.
        
        Args:
            text_doc: Extracted text from the document
        
        Returns:
            ClassificationResult model instance
        
        Raises:
            ValueError: If classification fails or returns invalid format
        """
        result_dict = self.classify(text_doc)
        return ClassificationResult(**result_dict)
    
    def _classify_openai(self, text_doc: str) -> Dict[str, str]:
        """Classify using OpenAI."""
        messages = [
            {"role": "system", "content": CLASSIFICATION_PROMPT},
            {
                "role": "user",
                "content": f"Classify this document:\n\n{text_doc[:5000]}"  # Limit text length
            },
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            text={"format": {"type": "json_object"}},
            temperature=0.1,  # Low temperature for classification
        )
        
        result_text = response.choices[0].message.content
        try:
            result = json.loads(result_text)
            # Validate structure
            if "document_type" not in result:
                raise ValueError("Classification result missing 'document_type' field")
            if result["document_type"] not in ["payslip", "settlement"]:
                raise ValueError(f"Invalid document_type: {result['document_type']}")
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse classification JSON: {e}") from e
    
    def _classify_gemini(self, text_doc: str) -> Dict[str, str]:
        """Classify using Gemini."""
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=f"Classify this document:\n\n{text_doc[:5000]}")  # Limit text length
                ]
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for classification
            system_instruction=[types.Part.from_text(text=CLASSIFICATION_PROMPT)],
            thinking_config=types.ThinkingConfig(thinking_budget=128),
            response_mime_type="application/json",
        )
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=generate_content_config,
        )
        
        result_text = response.text
        try:
            result = json.loads(result_text)
            # Validate structure
            if "document_type" not in result:
                raise ValueError("Classification result missing 'document_type' field")
            if result["document_type"] not in ["payslip", "settlement"]:
                raise ValueError(f"Invalid document_type: {result['document_type']}")
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse classification JSON: {e}") from e

