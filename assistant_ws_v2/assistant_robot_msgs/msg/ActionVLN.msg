# 发布给 VLN 的动作消息
int32 action_id        # 步骤序号
string[] regions       # 目标路径，比如 ["coffee-table","dining-table"]
string object          # （可选）针对 pick/place 动作的对象