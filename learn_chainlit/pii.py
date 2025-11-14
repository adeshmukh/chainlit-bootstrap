"""PII detection and anonymization using Presidio."""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Initialize Presidio engines
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


def anonymize_text(text: str) -> str:
    """Detect and anonymize PII in text using Presidio."""
    results = analyzer.analyze(text=text, language="en")
    if results:
        anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
        return anonymized.text
    return text
