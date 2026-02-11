import json
import inspect
import time
from tools import ALL_TOOLS
from mcp_server import MCPToolServer

# =================== 工具注册表（带参数 schema） ===================
TOOL_REGISTRY = [
    {
        "name": "get_user_profile",
        "desc": "获取用户基本信息",
        "args_schema": {"user_id": "int"}
    },
    {
        "name": "get_user_orders",
        "desc": "查询用户订单",
        "args_schema": {"user_id": "int"}
    },
    {
        "name": "get_user_payments",
        "desc": "查询支付记录",
        "args_schema": {"user_id": "int"}
    },
    {
        "name": "refund_order",
        "desc": "对指定订单进行退款",
        "args_schema": {"order_id": "int"}
    },
    {
        "name": "get_user_address",
        "desc": "获取用户地址",
        "args_schema": {"user_id": "int"}
    },
    {
        "name": "get_user_logs",
        "desc": "查询用户日志",
        "args_schema": {"user_id": "int"}
    },
]



def tool_router(query: str,client,metrics):
    prompt = f"""
        你是一个工具路由器。

        下面是工具列表（仅用于选择，不要调用）：
        {json.dumps(
            [{"name": t["name"], "desc": t["desc"]} for t in TOOL_REGISTRY],
            ensure_ascii=False
        )}

        用户问题：
        {query}

        请返回最相关的工具名称 JSON 数组，例如：
        ["get_user_orders", "get_user_payments"]
        """

    start = time.perf_counter()
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    latency = (time.perf_counter() - start) * 1000
    metrics.record("router", resp, latency)

    print("---------- tool_router：最相关的工具名称 ----------\n")
    print(resp.choices[0].message.content)
    print("---------------------------------\n")

    return json.loads(resp.choices[0].message.content)


def planner(query: str, selected_tools: list,client,metrics):
    tools_meta = [
        t for t in TOOL_REGISTRY if t["name"] in selected_tools
    ]

    prompt = f"""
        用户问题：
        {query}

        可用工具（注意参数定义）：
        {json.dumps(tools_meta, ensure_ascii=False)}

        ⚠️ 规则：
        1. 只能使用上面的工具
        2. 只能使用 args_schema 中定义的参数
        3. 不要编造不存在的参数
        4. 输出必须是 JSON 数组

        请生成执行计划：
        [
        {{
            "tool": "tool_name",
            "args": {{ "param": value }}
        }}
        ]
        """
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    latency = (time.perf_counter() - start) * 1000
    metrics.record("planner", resp, latency)

    print("---------- planner 生成执行计划----------\n")
    print(resp.choices[0].message.content)
    print("---------------------------------\n")

    return json.loads(resp.choices[0].message.content)


def execute(plan: list):
    mcp = MCPToolServer()
    results = {}

    for step in plan:
        # tool_name = step["tool"]
        # args = step.get("args", {})

        # fn = ALL_TOOLS[tool_name]

        # # ✅ 参数安全过滤（防 hallucination）
        # sig = inspect.signature(fn)
        # safe_args = {
        #     k: v for k, v in args.items()
        #     if k in sig.parameters
        # }

        # results[tool_name] = fn(**safe_args)

        # MCP 
        results[step["tool"]] = mcp.call_tool(
            name=step["tool"],
            arguments=step["args"]
        )

    print("---------- execute 执行结果----------\n")
    print(results)
    print("---------------------------------\n")

    return results


def final_answer(query: str, data: dict,client,metrics):
    prompt = f"""
        用户问题：
        {query}

        你已经获得以下最终业务数据：
        {json.dumps(data, ensure_ascii=False)}

        请基于这些数据给出最终回答。
        """
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    latency = (time.perf_counter() - start) * 1000
    metrics.record("final", resp, latency)

    print("---------- final_answer 最终回答----------\n")
    print(resp.choices[0].message.content)
    print("---------------------------------\n")

    return resp.choices[0].message.content

def run(query:str,client,metrics):
    selected_tools = tool_router(query,client,metrics)

    # 2.执行计划
    plan = planner(query, selected_tools,client,metrics)

    # 3.程序化执行
    data = execute(plan)

    # 4.最终回答
    answer = final_answer(query, data,client,metrics)

    print(answer)




def build_router_prompt(query: str, tools: list):
    # 注意：这里只传 name + desc，不传 schema 细节
    compact_tools = [
        {"name": t["name"], "desc": t["description"]}
        for t in tools
    ]

    return f"""
        你是 MCP 工具路由器。

        可用工具：
        {compact_tools}

        用户问题：
        {query}

        请返回最相关的 3 个工具名称（JSON 数组）。
        """


def run_router_mcp(client, query, mcp, metrics, label):
    tools = mcp.list_tools()

    start = time.perf_counter()
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=[{
            "role": "user",
            "content": build_router_prompt(query, tools)
        }],
        temperature=0,
    )
    latency = (time.perf_counter() - start) * 1000
    metrics.record(label, resp, latency)
