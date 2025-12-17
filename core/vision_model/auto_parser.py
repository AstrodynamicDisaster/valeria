"""
Auto parser that automatically classifies documents and routes to appropriate parser.

This module provides a unified interface for parsing both payslips and settlement documents.
It first classifies the document type using an LLM, then routes to the appropriate parser.
"""

from typing import Dict, Optional, Tuple, Union, Literal

from core.vision_model.payslips.payslip_parsers import (
    create_openai_parser,
    create_gemini_parser,
    OpenAIPayslipParser,
    GeminiPayslipParser,
)
from core.vision_model.payslips.payslip_models import PayslipData

from core.vision_model.settlements.settlement_parsers import (
    create_openai_settlement_parser,
    create_gemini_settlement_parser,
    OpenAISettlementParser,
    GeminiSettlementParser,
)
from core.vision_model.settlements.settlement_models import SettlementData

from core.vision_model.document_classifier import DocumentClassifier


class UnsupportedDocumentTypeError(Exception):
    """Raised when a document is classified as an unsupported type (e.g., 'other')."""
    pass


class AutoParser:
    """
    Auto parser that automatically classifies documents and routes to appropriate parser.
    
    This parser first classifies the document type, then uses the appropriate
    specialized parser (PayslipParser or SettlementParser) to extract data.
    """
    
    def __init__(
        self,
        classification_provider: Literal["openai", "gemini"] = "gemini",
        classification_model: str = "gemini-2.5-pro",
        parsing_provider: Optional[Literal["openai", "gemini"]] = None,
        parsing_model: Optional[str] = None,
        api_key: Optional[str] = None,
        project: str = "valeria-test-474315",
        location: str = "europe-southwest1",
    ):
        """
        Initialize the auto parser.
        
        Args:
            classification_provider: LLM provider for document classification
            classification_model: Model name for classification
            parsing_provider: LLM provider for parsing (defaults to classification_provider)
            parsing_model: Model name for parsing (defaults to classification_model)
            api_key: API key (for OpenAI) or None (uses env var or Vertex AI)
            project: Google Cloud project ID (for Gemini with Vertex AI)
            location: Google Cloud location (for Gemini with Vertex AI)
        """
        # Initialize classifier
        self.classifier = DocumentClassifier(
            provider=classification_provider,
            model=classification_model,
            api_key=api_key,
            project=project,
            location=location,
        )
        
        # Use same provider/model for parsing if not specified
        self.parsing_provider = parsing_provider or classification_provider
        self.parsing_model = parsing_model or classification_model
        self.api_key = api_key
        self.project = project
        self.location = location
        
        # Lazy initialization of parsers
        self._payslip_parser: Optional[Union[OpenAIPayslipParser, GeminiPayslipParser]] = None
        self._settlement_parser: Optional[Union[OpenAISettlementParser, GeminiSettlementParser]] = None
    
    def _get_payslip_parser(self) -> Union[OpenAIPayslipParser, GeminiPayslipParser]:
        """Get or create the payslip parser."""
        if self._payslip_parser is None:
            if self.parsing_provider == "openai":
                self._payslip_parser = create_openai_parser(
                    api_key=self.api_key,
                    model=self.parsing_model
                )
            else:
                self._payslip_parser = create_gemini_parser(
                    project=self.project,
                    location=self.location,
                    model=self.parsing_model
                )
        return self._payslip_parser
    
    def _get_settlement_parser(self) -> Union[OpenAISettlementParser, GeminiSettlementParser]:
        """Get or create the settlement parser."""
        if self._settlement_parser is None:
            if self.parsing_provider == "openai":
                self._settlement_parser = create_openai_settlement_parser(
                    api_key=self.api_key,
                    model=self.parsing_model
                )
            else:
                self._settlement_parser = create_gemini_settlement_parser(
                    project=self.project,
                    location=self.location,
                    model=self.parsing_model
                )
        return self._settlement_parser
    
    def parse(
        self,
        pdf_bytes: bytes,
        text_doc: str = "",
    ) -> Tuple[Union[PayslipData, SettlementData], Dict[str, str]]:
        """
        Parse a document by first classifying it, then using the appropriate parser.
        
        Args:
            pdf_bytes: Raw bytes of the PDF file
            text_doc: Extracted text from the PDF (used for classification)
        
        Returns:
            Tuple of (parsed_data, classification_info)
            - parsed_data: Either PayslipData or SettlementData
            - classification_info: Dictionary with document_type, confidence, reasoning
        
        Raises:
            ValueError: If classification or parsing fails
        """
        # Step 1: Classify the document
        if not text_doc:
            # If no text provided, we could extract it here, but for now require it
            raise ValueError("text_doc is required for document classification")
        
        classification_info = self.classifier.classify(text_doc)
        document_type = classification_info["document_type"]
        
        # Step 2: Route to appropriate parser
        if document_type == "payslip":
            parser = self._get_payslip_parser()
            parsed_data = parser.parse_to_model(pdf_bytes, text_doc)
        elif document_type == "settlement":
            parser = self._get_settlement_parser()
            parsed_data = parser.parse_to_model(pdf_bytes, text_doc)
        else:  # other
            raise UnsupportedDocumentTypeError(
                f"Document classified as '{document_type}'. Skipping processing. "
                f"Reasoning: {classification_info.get('reasoning', 'N/A')}"
            )
        
        return parsed_data, classification_info
    
    def parse_to_dict(
        self,
        pdf_bytes: bytes,
        text_doc: str = "",
    ) -> Tuple[Dict, Dict[str, str]]:
        """
        Parse a document and return as dictionary with classification info.
        
        Args:
            pdf_bytes: Raw bytes of the PDF file
            text_doc: Extracted text from the PDF (used for classification)
        
        Returns:
            Tuple of (parsed_dict, classification_info)
            - parsed_dict: Dictionary with extracted data
            - classification_info: Dictionary with document_type, confidence, reasoning
        """
        parsed_data, classification_info = self.parse(pdf_bytes, text_doc)
        return parsed_data.model_dump(), classification_info
    
    def parse_with_usage(
        self,
        pdf_bytes: bytes,
        text_doc: str = "",
    ) -> Tuple[Union[PayslipData, SettlementData], Dict[str, str], Dict]:
        """
        Parse a document and return with usage information.
        
        Args:
            pdf_bytes: Raw bytes of the PDF file
            text_doc: Extracted text from the PDF (used for classification)
        
        Returns:
            Tuple of (parsed_data, classification_info, usage_info)
            - parsed_data: Either PayslipData or SettlementData
            - classification_info: Dictionary with document_type, confidence, reasoning
            - usage_info: Dictionary with usage metrics (tokens, etc.) - only for parsing, not classification
        """
        # Classify first
        if not text_doc:
            raise ValueError("text_doc is required for document classification")
        
        classification_info = self.classifier.classify(text_doc)
        document_type = classification_info["document_type"]
        
        # Parse with usage info
        if document_type == "payslip":
            parser = self._get_payslip_parser()
            data_dict, usage_info = parser.parse_with_usage(pdf_bytes, text_doc)
            parsed_data = PayslipData(**data_dict)
            parsed_data.verify_and_correct_aportacion_empresa_total()
        elif document_type == "settlement":
            parser = self._get_settlement_parser()
            data_dict, usage_info = parser.parse_with_usage(pdf_bytes, text_doc)
            parsed_data = SettlementData(**data_dict)
            parsed_data.verify_and_correct_total()
        else:  # other
            raise UnsupportedDocumentTypeError(
                f"Document classified as '{document_type}'. Skipping processing. "
                f"Reasoning: {classification_info.get('reasoning', 'N/A')}"
            )
        
        return parsed_data, classification_info, usage_info


# Convenience function
def create_auto_parser(
    provider: Literal["openai", "gemini"] = "gemini",
    model: str = "gemini-2.5-pro",
    api_key: Optional[str] = None,
    project: str = "valeria-test-474315",
    location: str = "europe-southwest1",
) -> AutoParser:
    """
    Create an auto parser with default settings.
    
    Args:
        provider: LLM provider to use for both classification and parsing
        model: Model name to use
        api_key: API key (for OpenAI) or None (uses env var or Vertex AI)
        project: Google Cloud project ID (for Gemini with Vertex AI)
        location: Google Cloud location (for Gemini with Vertex AI)
    
    Returns:
        Configured AutoParser instance
    """
    return AutoParser(
        classification_provider=provider,
        classification_model=model,
        parsing_provider=provider,
        parsing_model=model,
        api_key=api_key,
        project=project,
        location=location,
    )

