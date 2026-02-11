import time
from tools import ALL_TOOLS
from mcp_server import MCPToolServer


# ========= 优化前 =========

REACT_PROMPT = """
    你是一个智能 Agent。
    你可以使用以下工具（名称 + 说明）：
    1. get_user_profile(user_id): 获取用户基本信息
    2. get_user_orders(user_id): 查询用户订单
    3. get_user_payments(user_id): 查询支付记录
    4. refund_order(order_id): 退款订单
    5. get_user_address(user_id):获取用户地址
    6. get_user_logs(user_id): 查询用户日志

    用户问题：
    {query}

    请严格按照 ReAct 格式：
    Thought → Action → Observation → Thought … → Final Answer
    """


def react_agent(query: str,client,metrics):
    mcp = MCPToolServer()
    messages = [{"role": "user", "content": REACT_PROMPT.format(query=query)}]

    # ===== 第 1 轮 =====
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        temperature=0,
    )
    latency = (time.perf_counter() - start) * 1000
    metrics.record("react_round_1", resp, latency)

    assistant_msg = resp.choices[0].message
    messages.append(assistant_msg)

    print("\n--- LLM Response 1 ---")
    print(assistant_msg.content)
    print("-"*20+'\n')

    # 假设模型决定调用 get_user_orders（真实系统需解析 Action）
    # observation = ALL_TOOLS["get_user_orders"](user_id=1)

    # ===== 模拟解析 Action（示例：固定调用）=====
    # 实际工程中应解析 Action JSON
    observation = mcp.call_tool(
        name="get_user_orders",
        arguments={"user_id": 1}
    )
    # 工具结果回流到上下文（问题根源）
    messages.append({
        "role": "assistant",
        "content": str(observation)
    })


    # ===== 第 2 轮 （模型读全部历史）=====
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        temperature=0,
    )
    latency = (time.perf_counter() - start) * 1000
    metrics.record("react_round_2", resp, latency)

    assistant_msg = resp.choices[0].message
    # messages.append(assistant_msg)

    print("\n--- LLM Response 2 ---")
    print(assistant_msg.content)
    print("-"*20+'\n')

    return assistant_msg.content



def build_react_prompt(query: str, tools: list):
    tool_desc = "\n".join(
        f"- {t['name']}: {t['description']}"
        for t in tools
    )

    return f"""
        你是一个智能 Agent。
        你可以使用以下工具：
        {tool_desc}

        用户问题：
        {query}

        请严格按照 ReAct 格式：
        Thought → Action → Observation → Thought → Final Answer
        """

def run_react_mcp(client, query, mcp, metrics, label):
    tools = mcp.list_tools()

    messages = [{
        "role": "user",
        "content": build_react_prompt(query, tools)
    }]

    start = time.perf_counter()
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        temperature=0,
    )
    latency = (time.perf_counter() - start) * 1000
    metrics.record(label, resp, latency)

    start = time.perf_counter()
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        temperature=0,
    )
    latency = (time.perf_counter() - start) * 1000
    metrics.record(label, resp, latency)