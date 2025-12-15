"""
Document classifier module.

Provides functionality to classify Spanish labor documents
as either payslips or settlements.
"""

from core.vision_model.document_classifier.classifier import (
    DocumentClassifier,
    CLASSIFICATION_PROMPT,
)

from core.vision_model.document_classifier.models import (
    ClassificationResult,
)

__all__ = [
    "DocumentClassifier",
    "ClassificationResult",
    "CLASSIFICATION_PROMPT",
]

