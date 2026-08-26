import time
import logging
from typing import List, Dict, Any, Callable

logger = logging.getLogger(__name__)

class HookRunner:
    """
    Production-grade hook runner for Fusion 360 MCP client.
    Manages execution of pre- and post-hooks, handles timing/metrics,
    and supports integration with MCP clients.
    """

    def __init__(self):
        self.pre_hooks: List[Any] = []
        self.post_hooks: List[Any] = []
        self.metrics: List[Dict[str, Any]] = []

    def add_pre_hook(self, hook: Any):
        """Add a pre-execution hook (must have a process(tool_name, args) method)."""
        self.pre_hooks.append(hook)

    def add_post_hook(self, hook: Any):
        """Add a post-execution hook (must have a process(tool_name, result) method)."""
        self.post_hooks.append(hook)

    def execute(self, tool_name: str, arguments: Dict[str, Any], executor: Callable[[str, Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes a tool call, running all pre-hooks before and post-hooks after,
        and logs performance metrics.
        """
        start_time = time.time()
        
        # 1. Pre-hooks
        processed_args = dict(arguments)
        for hook in self.pre_hooks:
            try:
                processed_args = hook.process(tool_name, processed_args)
            except Exception as e:
                logger.error(f"Pre-hook {hook.__class__.__name__} failed: {e}")

        # 2. Execution
        exec_start = time.time()
        try:
            result = executor(tool_name, processed_args)
        except Exception as e:
            result = {"status": "error", "error": str(e)}
        exec_duration = time.time() - exec_start

        # 3. Post-hooks
        processed_result = dict(result) if isinstance(result, dict) else result
        for hook in self.post_hooks:
            try:
                processed_result = hook.process(tool_name, processed_result)
            except Exception as e:
                logger.error(f"Post-hook {hook.__class__.__name__} failed: {e}")

        total_duration = time.time() - start_time
        
        # 4. Metrics
        self.metrics.append({
            "tool_name": tool_name,
            "exec_duration_ms": round(exec_duration * 1000, 2),
            "total_duration_ms": round(total_duration * 1000, 2),
            "status": processed_result.get("status", "unknown") if isinstance(processed_result, dict) else "unknown"
        })
        
        logger.debug(f"Tool {tool_name} executed in {total_duration*1000:.2f}ms")
        
        return processed_result

    def get_metrics(self) -> List[Dict[str, Any]]:
        """Retrieve execution metrics."""
        return self.metrics

# Example usage pattern (usually orchestrated by mcp_client.py):
# runner = HookRunner()
# runner.add_pre_hook(PreToolUnitInterceptor())
# runner.add_post_hook(PostToolErrorExtractor())
# result = runner.execute("fusion_mcp_execute", {"code": "..."}, my_mcp_client.call_tool)
