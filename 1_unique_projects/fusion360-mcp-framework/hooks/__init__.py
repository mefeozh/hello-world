from .pre_tool_unit_interceptor import PreToolUnitInterceptor, UnitMode
from .post_tool_error_extractor import PostToolErrorExtractor, Severity
from .hook_runner import HookRunner

__version__ = "1.0.0"
__all__ = [
    "PreToolUnitInterceptor", 
    "UnitMode",
    "PostToolErrorExtractor", 
    "Severity",
    "HookRunner", 
    "MCPClient",
    "create_default_runner"
]

def create_default_runner() -> HookRunner:
    """
    Factory function to create a configured HookRunner with the standard
    unit interceptor and error extractor applied.
    """
    runner = HookRunner()
    runner.add_pre_hook(PreToolUnitInterceptor())
    runner.add_post_hook(PostToolErrorExtractor())
    return runner

# Import MCPClient after create_default_runner is defined to avoid circular dependency
from .mcp_client import MCPClient
