"""PII detection and anonymization using Presidio."""

from __future__ import annotations

import os
from typing import Final

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine


def _env_var_enabled(value: str | None) -> bool:
    """Return True if the provided environment variable value is truthy."""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


ENABLE_PRESIDIO_PII_CLEANING: Final[bool] = _env_var_enabled(
    os.getenv("ENABLE_PRESIDIO_PII_CLEANING")
)


def _build_analyzer() -> AnalyzerEngine | None:
    """Create an AnalyzerEngine configured for en_core_web_sm."""
    if not ENABLE_PRESIDIO_PII_CLEANING:
        return None

    # Configure Presidio to use en_core_web_sm explicitly.
    # This prevents it from downloading en_core_web_lg automatically.
    try:
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
        nlp_engine = provider.create_engine()
        return AnalyzerEngine(nlp_engine=nlp_engine)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: Could not configure Presidio with en_core_web_sm: {exc}")
        print("Falling back to default Presidio configuration")
        return AnalyzerEngine()


analyzer: AnalyzerEngine | None = _build_analyzer()
anonymizer: AnonymizerEngine | None = (
    AnonymizerEngine() if ENABLE_PRESIDIO_PII_CLEANING else None
)


def anonymize_text(text: str) -> str:
    """Detect and anonymize PII in text using Presidio if enabled."""
    if not ENABLE_PRESIDIO_PII_CLEANING:
        return text
    if not text:
        return text
    if analyzer is None or anonymizer is None:
        return text

    results = analyzer.analyze(text=text, language="en")
    if not results:
        return text

    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text
