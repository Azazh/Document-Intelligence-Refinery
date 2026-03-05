from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class BaseExtractor(ABC):
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules

    @abstractmethod
    def extract(self, pdf_path: str) -> Tuple[Dict[str, Any], float]:
        """
        Extract content from a PDF and return (result, confidence).
        Result must be normalized to ExtractedDocument/LDU schema.
        """
        pass
