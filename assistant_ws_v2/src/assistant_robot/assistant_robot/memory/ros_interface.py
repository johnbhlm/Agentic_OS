import rclpy
from rclpy.node import Node
from std_msgs.msg import String,Empty
# from assistant_robot_msgs.msg import VLNStatus,VLAStatus
from assistant_robot_msgs.msg import ActionVLN, ActionVLA, ActionStatus,VLNStatus,ResetVLN,VLAStatus,ResetVLA,ResetVLAStatus


class VLAPublisher:
    def __init__(self, node: Node):
        self._node = node
        self._pub = node.create_publisher(ActionVLA, 'vla_actions', 10)

    def publish(self, action: str, action_id: int):
        # print("VLA publish")
        manipulation = action.split(" ")
        # print("manipulation")
        # print(manipulation)
        
        action_ = manipulation[1]
        obj_1 = manipulation[2]
        if action_ in ('open','close'):
            obj_2 = "None"
        else:
            obj_2 = manipulation[-1]

        msg = ActionVLA()
        msg.action_id = action_id
        msg.action = action_
        msg.object_1 = obj_1
        msg.object_2 = obj_2
        self._pub.publish(msg)
        node_name = self._node.get_name()
        # self._node.get_logger().info(
        #     f"[{node_name}] → VLA topic:→ [VLA] action_id = {action_id}, action={action_}, object={obj_1}"
        # )

class VLNPublisher:
    def __init__(self, node: Node):
        self._node = node
        self._pub = node.create_publisher(ActionVLN, 'vln_actions', 10)

    def publish(self, action: str, action_id: int):
        # print("VLN publish")
        # print(action.split(" "))
        object = action.split(" ")[-1]
        # regions=None
        msg = ActionVLN()
        msg.action_id = action_id
        msg.regions = ["room"]
        msg.object = object
        self._pub.publish(msg)
        node_name = self._node.get_name()
        # self._node.get_logger().info(f"[{node_name}] → VLN topic:→ [VLN] action_id = {action_id}, regions = {regions}, object= obj")

class StatusSubscriber:
    def __init__(self, node: Node, callback):
        """
        :param callback: function(Status) where Status has fields action_id:int, success:bool
        """
        self._node = node
        self.node_name = self._node.get_name()
        self._callback = callback
        # node.create_subscription(ActionStatus, 'action_status', self._internal_cb, 10)
        self._sub = node.create_subscription(
            ActionStatus,
            'action_status',
            self._internal_cb,
            10
        )

    def _internal_cb(self, msg: ActionStatus):        
        try:
            self._callback(msg)
            # self._node.get_logger().info(f"[{self.node_name}] Subscription Status topic from VMA/VLN: action_id = {msg.action_id}, success = {msg.success}")
        except Exception as e:
            # print(f"[StatusSubscriber] Invalid status message: '{msg}'")
            print(f"[StatusSubscriber] 回调异常: action_id={msg.action_id}, success={msg.success}, error={e}")
            import traceback
            print(f"[StatusSubscriber] 回调内部异常: {e}")
            traceback.print_exc()


class VLA_StatusSubscriber:
    def __init__(self, node: Node, callback):
        """
        :param callback: function(Status) where Status has fields std_msgs/header, status:uint8---0: not initialized, 1: ready, 2: running
        """
        self._node = node
        self.node_name = self._node.get_name()
        self._callback = callback
        self._sub = node.create_subscription(VLAStatus,'/vla_decision/status',self._internal_cb,10)

    def _internal_cb(self, msg: VLAStatus):        
        try:
            self._callback(msg)
        except Exception as e:
            print(f"[VLA_StatusSubscriber] 回调异常: status={msg.status}, error={e}")
            import traceback
            print(f"[VLA_StatusSubscriber] 回调内部异常: {e}")
            traceback.print_exc()

class VLN_StatusSubscriber:
    def __init__(self, node: Node, callback):
        """
        :param callback: function(Status) where Status has fields std_msgs/header, status:uint8---0: not initialized, 1: ready, 2: running
        """
        self._node = node
        self.node_name = self._node.get_name()
        self._callback = callback
        self._sub = node.create_subscription(VLNStatus,'/vln_decision/status',self._internal_cb,10)

    def _internal_cb(self, msg: VLNStatus):        
        try:
            self._callback(msg)
        except Exception as e:
            print(f"[VLN_StatusSubscriber] 回调异常: status={msg.status}, error={e}")
            import traceback
            print(f"[VLN_StatusSubscriber] 回调内部异常: {e}")
            traceback.print_exc()


#  ******** VLA Reset ********
class VLA_ResetPublisher:
    def __init__(self, node: Node):
        self._node = node
        self._pub = node.create_publisher(ResetVLA, 'vla_reset', 10)

    def publish(self):
        msg = ResetVLA()
        msg.reset = 1
        self._pub.publish(msg)

class VLA_ResetSubscriber:
    def __init__(self, node: Node, callback):
        """
        :param callback: function(Status) where Status has fields std_msgs/header, reset_status:uint8 --- # 0 failed, 1 success
        """
        self._node = node
        self.node_name = self._node.get_name()
        self._callback = callback
        self._sub = node.create_subscription(ResetVLAStatus,'vla_reset_status',self._internal_cb,10)

    def _internal_cb(self, msg: ResetVLAStatus):        
        try:
            self._callback(msg)
        except Exception as e:
            print(f"[VLA_ResetSubscriber] 回调异常: reset_status={msg.reset_status}, error={e}")
            import traceback
            print(f"[VLA_ResetSubscriber] 回调内部异常: {e}")
            traceback.print_exc()

#  ******** VLN Reset ********
class VLN_ResetPublisher:
    def __init__(self, node: Node):
        self._node = node
        self._pub = node.create_publisher(Empty, '/cancel_task_by_manual', 10)

    def publish(self):
        msg = Empty()

        self._pub.publish(msg)

class VLN_ResetSubscriber:
    def __init__(self, node: Node, callback):
        """
        :param callback: function(Status) where Status has fields std_msgs/header, reset_status:uint8 --- # 0 failed, 1 success
        """
        self._node = node
        self.node_name = self._node.get_name()
        self._callback = callback
        self._sub = node.create_subscription(ResetVLN,'/vln/reset',self._internal_cb,10)

    def _internal_cb(self, msg: ResetVLN):        
        try:
            self._callback(msg)
        except Exception as e:
            print(f"[VLN_ResetSubscriber] 回调异常: reset_status={msg.reset_status}, error={e}")
            import traceback
            print(f"[VLN_ResetSubscriber] 回调内部异常: {e}")
            traceback.print_exc()