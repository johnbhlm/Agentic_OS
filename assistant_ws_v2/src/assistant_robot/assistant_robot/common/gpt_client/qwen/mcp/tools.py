# =========================
# 模拟业务工具（多个）
# =========================

def get_user_profile(user_id: int):
    return {"user_id": user_id, "name": "Alice", "vip": True}

def get_user_orders(user_id: int):
    return {"orders": [{"id": 1, "amount": 199}, {"id": 2, "amount": 299}]}

def get_user_payments(user_id: int):
    return {"payments": [{"id": "p1", "status": "success"}]}

def refund_order(order_id: int):
    return {"order_id": order_id, "status": "refunded"}

def get_user_address(user_id: int):
    return {"address": "Beijing"}

def get_user_logs(user_id: int):
    return {"logs": ["login", "pay", "logout"]}


ALL_TOOLS = {
    "get_user_profile": get_user_profile,
    "get_user_orders": get_user_orders,
    "get_user_payments": get_user_payments,
    "refund_order": refund_order,
    "get_user_address": get_user_address,
    "get_user_logs": get_user_logs,
}
# tools.py

# =========================
# 模拟业务工具（多个）
# =========================

def get_user_profile(user_id: int):
    return {"user_id": user_id, "name": "Alice", "vip": True}

def get_user_orders(user_id: int):
    return {"orders": [{"id": 1, "amount": 199}, {"id": 2, "amount": 299}]}

def get_user_payments(user_id: int):
    return {"payments": [{"id": "p1", "status": "success"}]}

def refund_order(order_id: int):
    return {"order_id": order_id, "status": "refunded"}

def get_user_address(user_id: int):
    return {"address": "Beijing"}

def get_user_logs(user_id: int):
    return {"logs": ["login", "pay", "logout"]}


ALL_TOOLS = {
    "get_user_profile": get_user_profile,
    "get_user_orders": get_user_orders,
    "get_user_payments": get_user_payments,
    "refund_order": refund_order,
    "get_user_address": get_user_address,
    "get_user_logs": get_user_logs,
}
