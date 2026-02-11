import os
import requests

# 🚫 强制关闭所有代理
for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "FTP_PROXY", "ftp_proxy"]:
    os.environ.pop(key, None)
os.environ["NO_PROXY"] = "*"

# 🧩 禁用 requests 对系统代理的信任
session = requests.Session()
session.trust_env = False

from openai import OpenAI
from react_base_mode import react_agent
from react_optim_mode import run
from metrics import Metrics

from mcp_server import MCPToolServer
from react_base_mode import run_react_mcp
from react_optim_mode import run_router_mcp

def build_client():
    return OpenAI(
        api_key="sk-b2d24ce815fb46cf9aba319e7a5b43a1",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

if __name__== "__main__":
    client = build_client()
    
    query = "查询用户1的订单和支付情况，如有问题帮我退款"

    # # ========= 优化前 =========
    # react_metrics = Metrics("ReAct + MCP (优化前)")
    # result = react_agent(query, client, react_metrics)

    # print("\n=== Final Result (ReAct) ===")
    # print(result)

    # react_metrics.summary()


    # # ========= 优化后 =========
    # optim_metrics = Metrics("Optimized + MCP (优化后)")
    # run(query, client, optim_metrics)

    # optim_metrics.summary()


    for tool_count in [6, 60, 600]:
        print(f"\n\n===== MCP TOOL COUNT = {tool_count} =====")

        mcp = MCPToolServer(tool_count)

        # ReAct + MCP
        react_metrics = Metrics(f"ReAct+MCP-{tool_count}")
        run_react_mcp(
            client, query, mcp, react_metrics,
            f"react_mcp_{tool_count}"
        )
        react_metrics.summary()

        # Optimized + MCP
        opt_metrics = Metrics(f"Optimized+MCP-{tool_count}")
        run_router_mcp(
            client, query, mcp, opt_metrics,
            f"router_mcp_{tool_count}"
        )
        opt_metrics.summary()

    # # 1.工具路由
    # selected_tools = tool_router(query)

    # # 2.执行计划
    # plan = planner(query, selected_tools)

    # # 3.程序化执行
    # data = execute(plan)

    # # 4.最终回答
    # answer = final_answer(query, data)

    # print(answer)

