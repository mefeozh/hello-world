import json
import urllib.request
import urllib.error
import logging
import time
from typing import Dict, Any, Optional
from .hook_runner import HookRunner
from . import create_default_runner

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Production-grade HTTP client for communicating with the Autodesk Fusion 360 MCP server.
    Implements JSON-RPC 2.0 with session lifecycle management and session ID header tracking.
    """
    
    def __init__(self, endpoint: str = "http://127.0.0.1:27182/mcp", hook_runner: Optional[HookRunner] = None):
        self.endpoint = endpoint
        self.hook_runner = hook_runner or create_default_runner()
        self._request_id = 1
        self.session_id: Optional[str] = None
        
    def _send_rpc(self, method: str, params: Optional[Dict[str, Any]] = None, is_notification: bool = False) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "method": method
        }
        
        if params is not None:
            payload["params"] = params
            
        if not is_notification:
            payload["id"] = self._request_id
            self._request_id += 1
            
        data = json.dumps(payload).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        if self.session_id:
            headers['Mcp-Session-Id'] = self.session_id

        req = urllib.request.Request(
            self.endpoint,
            data=data,
            headers=headers
        )
        
        retries = 3
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    # Capture session ID header if returned
                    resp_headers = response.info()
                    if 'Mcp-Session-Id' in resp_headers:
                        self.session_id = resp_headers['Mcp-Session-Id']
                    elif 'mcp-session-id' in resp_headers:
                        self.session_id = resp_headers['mcp-session-id']

                    if is_notification:
                        return {"status": "success"}
                    resp_body = response.read().decode('utf-8')
                    if not resp_body:
                        return {"status": "error", "error": "Empty response from server"}
                    resp_data = json.loads(resp_body)
                    if "error" in resp_data:
                        return {"status": "error", "error": resp_data["error"]}
                    return {"status": "success", "result": resp_data.get("result")}
            except urllib.error.URLError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}/{retries}): {e}")
                time.sleep(1)
            except Exception as e:
                return {"status": "error", "error": str(e)}
                
        return {"status": "error", "error": "Failed to connect to MCP server after retries"}

    def initialize_session(self) -> Dict[str, Any]:
        """Initialize the MCP session and send notifications/initialized."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "fusion360-mcp-framework", "version": "1.0.0"}
        }
        res = self._send_rpc("initialize", params)
        if res.get("status") == "success":
            self._send_rpc("notifications/initialized", is_notification=True)
        return res

    def _execute_tool_raw(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Raw tool execution bypassing hooks, used internally by HookRunner."""
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        res = self._send_rpc("tools/call", params)
        if res.get("status") == "success" and "result" in res:
            tool_res = res["result"]
            content = tool_res.get("content", [])
            output_text = "\n".join([c.get("text", "") for c in content if c.get("type") == "text"])
            
            try:
                parsed_output = json.loads(output_text)
                return {"status": "success", "output": parsed_output}
            except:
                return {"status": "success", "output": output_text, "isError": tool_res.get("isError", False)}
        return res

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool with pre/post hooks applied."""
        return self.hook_runner.execute(tool_name, arguments, self._execute_tool_raw)

    def execute_script(self, code: str) -> Dict[str, Any]:
        """Helper to run a Python script in Fusion 360 using fusion_mcp_execute script payload."""
        return self.call_tool("fusion_mcp_execute", {
            "featureType": "script",
            "object": {
                "script": code
            }
        })

    def read_state(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """Helper to read state from Fusion 360."""
        args = {"queryType": query_type}
        args.update(kwargs)
        return self.call_tool("fusion_mcp_read", args)
