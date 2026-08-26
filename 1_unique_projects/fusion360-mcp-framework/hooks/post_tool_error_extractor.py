import re
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class Severity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

class PostToolErrorExtractor:
    """
    Production-grade extractor to parse Fusion 360 errors and API responses
    into structured error reports with actionable fix suggestions.
    """

    # Common Fusion 360 error patterns mapping to human readable advice
    ERROR_CATALOG = {
        r"Profile is not valid": "The sketch profile is not closed or contains self-intersecting lines. Check sketch geometry.",
        r"Failed to create": "Geometry conflict: The requested operation could not be computed. Check if dimensions cause self-intersection or zero-thickness geometry.",
        r"The input is not valid": "Parameter type mismatch or missing required input for the feature.",
        r"Cannot find": "Reference entity deleted or not found. Ensure the referenced BRepFace, Edge, or Sketch exists.",
        r"Sketch profile cannot be used": "Overlapping profiles or open loops detected in the sketch.",
        r"Boolean operation failed": "Bodies do not intersect, or the target body is missing/invalid for Cut/Join operation."
    }

    # Map internal health states to readable strings
    HEALTH_STATES = {
        "0": "Error - Feature computation failed",
        "1": "Warning - Feature computed with warnings",
        "2": "Healthy - Feature computed successfully",
        "3": "Suppressed - Feature is suppressed"
    }

    def process(self, tool_name: str, result: dict) -> dict:
        if not isinstance(result, dict):
            return result

        status = result.get("status", "")
        error_msg = result.get("error", "")
        output = result.get("output", "")
        
        extracted_issues = []

        # Analyze errors
        if status == "error" or error_msg:
            full_text = f"{error_msg}\n{output}"
            for pattern, suggestion in self.ERROR_CATALOG.items():
                if re.search(pattern, full_text, re.IGNORECASE):
                    extracted_issues.append({
                        "severity": Severity.ERROR.value,
                        "pattern_matched": pattern,
                        "suggestion": suggestion,
                        "raw_context": error_msg or "See output for details"
                    })
            
            # If no specific pattern matched but it's an error
            if not extracted_issues:
                extracted_issues.append({
                    "severity": Severity.ERROR.value,
                    "suggestion": "An unknown runtime error occurred in Fusion 360 API.",
                    "raw_context": error_msg
                })

        # Inject structured findings back into the result
        if extracted_issues:
            result["structured_errors"] = extracted_issues
            logger.warning(f"Extracted {len(extracted_issues)} errors from response.")

        return result
