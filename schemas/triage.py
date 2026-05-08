# schemas/triage.py

"""Schema for classification of triage"""

# Standard Imports
from dataclasses import dataclass
# Third Party Imports
# Local Imports

@dataclass
class TriageResult:
    urgency: str
    department: str
    recommendation: str
    confidence: str
    matched_result: list[str]
