import time

class Metrics:
    def __init__(self, name):
        self.name = name
        self.records = []

    def record(self, step_name, resp, latency_ms):
        usage = resp.usage
        self.records.append({
            "step": step_name,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "latency_ms": latency_ms,
        })

    def summary(self):
        print(f"\n========== {self.name} Metrics Summary ==========")

        total_prompt = 0
        total_completion = 0
        total_latency = 0

        for r in self.records:
            total_prompt += r["prompt_tokens"]
            total_completion += r["completion_tokens"]
            total_latency += r["latency_ms"]

            print(
                f"[{r['step']}] "
                f"prompt={r['prompt_tokens']} | "
                f"completion={r['completion_tokens']} | "
                f"total={r['total_tokens']} | "
                f"latency={r['latency_ms']:.2f} ms"
            )

        print("-----------------------------------------------")
        print(f"TOTAL prompt_tokens     : {total_prompt}")
        print(f"TOTAL completion_tokens : {total_completion}")
        print(f"TOTAL tokens            : {total_prompt + total_completion}")
        print(f"TOTAL latency (ms)      : {total_latency:.2f}")
        print("===============================================\n")
