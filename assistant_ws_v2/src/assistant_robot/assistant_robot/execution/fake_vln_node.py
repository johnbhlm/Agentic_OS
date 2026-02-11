import time
import threading
import rclpy
from rclpy.node import Node
from assistant_robot_msgs.msg import ActionVLN, ActionStatus

class FakeVLNNode(Node):
    def __init__(self):
        super().__init__('fake_vln')
        self.test_status=False
        self.subscription = self.create_subscription(
            ActionVLN,
            'vln_actions',
            self._vln_callback,
            10
        )
        self.publisher = self.create_publisher(ActionStatus, 'action_status', 10)
        self.get_logger().info("🧭 Fake VLN Node ready and listening...")

    def _vln_callback(self, msg: ActionVLN):
        self.get_logger().info(f"📡 Received VLN action (id={msg.action_id}): regions={msg.regions}, object={msg.object}")

        def _process():
            time.sleep(10)  # 模拟执行
            status = ActionStatus()
            status.action_id = msg.action_id
            status.success = True
            self.publisher.publish(status)
            self.get_logger().info(f"✅ Finished VLN action id={msg.action_id}, publish status = {status.success}.")

        threading.Thread(target=_process, daemon=True).start()

def main(args=None):
    rclpy.init(args=args)
    node = FakeVLNNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
