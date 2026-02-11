from tools import ALL_TOOLS
from mcp_tools import TOOL_SCHEMAS

# class MCPToolServer:
#     def list_tools(self):
#         return TOOL_SCHEMAS

#     def call_tool(self, name: str, arguments: dict):
#         if name not in ALL_TOOLS:
#             raise ValueError(f"Tool not found: {name}")

#         # ✅ 参数校验（MCP 的关键价值之一）
#         schema = TOOL_SCHEMAS[name]["input_schema"]
#         for field in schema["required"]:
#             if field not in arguments:
#                 raise ValueError(f"Missing required field: {field}")

#         fn = ALL_TOOLS[name]
#         return fn(**arguments)

import time

class MCPToolServer:
    """
    模拟 MCP Tool Server
    """

    def __init__(self, tool_count: int):
        self.tool_count = tool_count

    def list_tools(self):
        """
        MCP 标准能力：列出所有工具 schema
        """
        return [
            {
                "name": f"tool_{i}",
                "description": f"第 {i} 个业务工具，用于处理某类用户相关操作",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer"}
                    },
                    "required": ["user_id"]
                }
            }
            for i in range(self.tool_count)
        ]

    def call_tool(self, name: str, arguments: dict):
        """
        模拟工具执行（不消耗 LLM token）
        """
        time.sleep(0.005)  # 模拟 I/O
        return {
            "tool": name,
            "result": f"success for user {arguments.get('user_id')}"
        }

