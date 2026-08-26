"""
Interceptor to block vision/screenshot requests and suggest parametric queries instead.
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class VisionBlocker:
    """Blocks screenshot requests to encourage parametric/B-Rep queries."""
    
    def __init__(self, allow_screenshots: bool = False):
        self.allow_screenshots = allow_screenshots

    def intercept(self, mcp_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Intercepts fusion_mcp_read calls. If queryType is 'screenshot' and screenshots
        are not allowed, returns a rejection response dict. Otherwise returns None (continue) or modified dict.
        
        Args:
            mcp_request: The MCP request dict.
            
        Returns:
            A rejection response dict if blocked, else None.
        """
        if mcp_request.get('tool') == 'fusion_mcp_read':
            args = mcp_request.get('arguments', {})
            query_type = args.get('queryType', '')
            
            if query_type == 'screenshot' and not self.allow_screenshots:
                logger.warning("Blocked screenshot request. Suggesting alternatives.")
                return {
                    'error': 'Screenshots are disabled in this mode.',
                    'message': 'Please use parametric/B-Rep queries instead.',
                    'suggestions': [
                        {'queryType': 'timeline', 'description': 'Query the Fusion 360 design timeline.'},
                        {'queryType': 'parameters', 'description': 'Query the user and model parameters.'},
                        {'queryType': 'bodies', 'description': 'Query the B-Rep bodies and their properties.'}
                    ],
                    'status': 'blocked'
                }
        return mcp_request

# Default instance for simple functional usage
default_blocker = VisionBlocker()
pre_tool_vision_blocker = default_blocker.intercept
