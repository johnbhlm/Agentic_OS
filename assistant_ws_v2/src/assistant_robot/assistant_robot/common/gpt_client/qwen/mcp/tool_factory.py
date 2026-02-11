def make_fake_tools(n: int):
    """
    生成 n 个假的 MCP Tool 描述（不真的执行）
    """
    tools = []
    for i in range(n):
        tools.append({
            "name": f"tool_{i}",
            "desc": f"这是第 {i} 个业务工具，用于处理某类业务操作"
        })
    return tools
