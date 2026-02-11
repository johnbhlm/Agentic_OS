import time
import threading
import rclpy
from rclpy.node import Node
from assistant_robot_msgs.msg import ActionVLA, ActionStatus

class FakeVLANode(Node):
    def __init__(self):
        super().__init__('fake_vla')
        self.test_status=False
        self.subscription = self.create_subscription(
            ActionVLA,
            'vla_actions',
            self._vla_callback,
            10
        )
        self.publisher = self.create_publisher(ActionStatus, 'action_status', 10)
        self.get_logger().info("🦾 Fake VLA Node ready and listening...")

    def _vla_callback(self, msg: ActionVLA):
        self.get_logger().info(f"📡 Received VLA action (id={msg.action_id}): action={msg.action}, object_1={msg.object_1}, object_2={msg.object_2}")

        def _process():
            time.sleep(10)  # 模拟执行
            status = ActionStatus()
            status.action_id = msg.action_id
            if self.test_status:
                status.success = False
                self.test_status=False
            else:
                status.success = True
                self.test_status=True
            self.publisher.publish(status)
            
            if status.success:
                self.get_logger().info(f"✅ Succeed VLA action id={msg.action_id}, publish status = {status.success}.")
            else:
                self.get_logger().info(f"❌ Failed VLA action id={msg.action_id}, publish status = {status.success}.")

        threading.Thread(target=_process, daemon=True).start()

def main(args=None):
    rclpy.init(args=args)
    node = FakeVLANode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
