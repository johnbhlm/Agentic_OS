from typing import Dict, Any

# ===== Tool Schemas =====
TOOL_SCHEMAS = {
    "get_user_profile": {
        "description": "获取用户基本信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        }
    },
    "get_user_orders": {
        "description": "查询用户订单",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        }
    },
    "get_user_payments": {
        "description": "查询用户支付记录",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        }
    },
    "refund_order": {
        "description": "对指定订单执行退款操作",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer"}
            },
            "required": ["order_id"]
        }
    },
    "get_user_address": {
        "description": "获取用户地址信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        }
    },
    "get_user_logs": {
        "description": "获取用户行为日志（仅限分析）",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        }
    }
}
