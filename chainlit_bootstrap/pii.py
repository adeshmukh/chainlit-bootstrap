"""PII detection and anonymization using Presidio."""

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

# Configure Presidio to use en_core_web_sm explicitly
# This prevents it from downloading en_core_web_lg automatically
try:
    # Create NLP engine provider configuration to use en_core_web_sm
    nlp_configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }

    # Initialize NLP engine provider
    provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
    nlp_engine = provider.create_engine()

    # Initialize Presidio analyzer with the configured NLP engine
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
except Exception as e:
    # Fallback: if model is not found or configuration fails,
    # let Presidio handle it (should not happen if Docker build installed correctly)
    print(f"Warning: Could not configure Presidio with en_core_web_sm: {e}")
    print("Falling back to default Presidio configuration")
    analyzer = AnalyzerEngine()

anonymizer = AnonymizerEngine()


def anonymize_text(text: str) -> str:
    """Detect and anonymize PII in text using Presidio."""
    results = analyzer.analyze(text=text, language="en")
    if results:
        anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
        return anonymized.text
    return text
