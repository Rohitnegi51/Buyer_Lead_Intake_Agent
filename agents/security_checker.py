import re
from typing import Tuple
from models.schemas import SecurityResult

class SecurityChecker:
    """
    Checks inquiries for prompt injection, PII requests, or data exfiltration.
    """
    def __init__(self):
        self.injection_patterns = [
            r"ignore all previous instructions",
            r"disregard",
            r"system prompt"
        ]
        self.pii_patterns = [
            r"owner name",
            r"phone number",
            r"contact them directly",
            r"json format"
        ]

    def check_inquiry(self, text: str) -> Tuple[SecurityResult, str]:
        """
        Returns a SecurityResult and a 'sanitized' version of the text.
        """
        text_lower = text.lower()
        flags = []
        is_safe = True

        # Check for prompt injection
        if any(re.search(p, text_lower) for p in self.injection_patterns):
            flags.append("Prompt Injection / Instruction Override Attempt")
            is_safe = False

        # Check for PII data exfiltration
        if any(re.search(p, text_lower) for p in self.pii_patterns):
            flags.append("Unauthorized PII/Data Request")
            is_safe = False

        # Sanitize: we ask the LLM to ignore the injection, but we can also strip out 
        # obvious malicious blocks if they are distinct. For the scope of this case study, 
        # we will rely on Gemini's structured outputs to inherently filter out the malicious 
        # instructions from the requirements, but we flag it here.
        # The returned sanitized text can just be the original text, as Gemini will handle it safely.
        return SecurityResult(is_safe=is_safe, flags=flags), text
