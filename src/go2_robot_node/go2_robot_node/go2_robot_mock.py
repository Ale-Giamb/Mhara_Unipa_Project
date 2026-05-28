import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist
import threading
import time


class Go2RobotMock(Node):
    def __init__(self):
        super().__init__('go2_robot_mock')

        # Publisher
        self.status_pub = self.create_publisher(String, 'go2/status', 10)

        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist, 'go2/cmd_vel', self.cmd_vel_callback, 10)
        
        self.action_sub = self.create_subscription(
            String, 'go2/action', self.action_callback, 10)
        
        self.audio_play_sub = self.create_subscription(
            String, 'go2/audio/play', self.audio_play_callback, 10)
        
        self.audio_speak_sub = self.create_subscription(
            String, 'go2/audio/speak', self.audio_speak_callback, 10)
        
        self.camera_sub = self.create_subscription(
            Bool, 'go2/camera', self.camera_callback, 10)

        # Timer per pubblicare status
        self.create_timer(5.0, self.publish_status)

        self.get_logger().info('[MOCK GO2] Go2 Robot Mock Node avviato (senza hardware)')

    def publish_status(self):
        msg = String()
        msg.data = "Mock Go2 online"
        self.status_pub.publish(msg)

    def cmd_vel_callback(self, msg: Twist):
        self.get_logger().info(
            f"[MOCK GO2] cmd_vel: linear.x={msg.linear.x:.2f}, "
            f"linear.y={msg.linear.y:.2f}, angular.z={msg.angular.z:.2f}"
        )

    def action_callback(self, msg: String):
        action = msg.data
        self.get_logger().info(f"[MOCK GO2] action: {action}")
        
        # Simula un ritardo per "esecuzione"
        def _delayed_status():
            time.sleep(1.0)
            status = String()
            status.data = f"Action '{action}' completata (mock)"
            self.status_pub.publish(status)
        
        threading.Thread(target=_delayed_status, daemon=True).start()

    def audio_play_callback(self, msg: String):
        audio_file = msg.data
        self.get_logger().info(f"[MOCK GO2] audio/play: {audio_file}")

    def audio_speak_callback(self, msg: String):
        text = msg.data
        self.get_logger().info(f"[MOCK GO2] audio/speak: '{text}'")

    def camera_callback(self, msg: Bool):
        if msg.data:
            self.get_logger().info("[MOCK GO2] camera: richiesta frame (mock, nessuna immagine)")


def main(args=None):
    rclpy.init(args=args)
    node = Go2RobotMock()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
