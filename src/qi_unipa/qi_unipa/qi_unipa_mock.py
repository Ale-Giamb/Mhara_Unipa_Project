import time
import threading

import rclpy
from rclpy.node import Node

from std_msgs.msg import Bool, String, Int32
from geometry_msgs.msg import Vector3
from sensor_msgs.msg import Image

from qi_unipa_msgs.msg import PostureWithSpeed, Track, JointAnglesWithSpeed, Hand, Sonar, Bumper


class QiUnipaMock(Node):
    def __init__(self):
        super().__init__('qi_unipa_mock')

        # Publishers (robot -> system)
        self.sonar_pub = self.create_publisher(Sonar, '/sonar', 10)
        self.bumper_pub = self.create_publisher(Bumper, '/bumper', 10)
        self.position_pub = self.create_publisher(Vector3, '/position', 10)
        self.is_speaking_pub = self.create_publisher(Bool, '/is_speaking', 10)
        self.is_speaking_bdi_pub = self.create_publisher(Bool, '/is_speaking_bdi', 10)
        self.start_conv_pub = self.create_publisher(Bool, '/start_conv', 10)
        self.stt_pub = self.create_publisher(String, '/stt', 10)
        self.stt_bdi_pub = self.create_publisher(String, '/stt_bdi', 10)
        self.transcription_pub = self.create_publisher(String, '/transcription', 10)
        self.transcription_bdi_pub = self.create_publisher(String, '/transcription_bdi', 10)
        self.touched_pub = self.create_publisher(Bool, '/touched', 10)
        self.camera_pub = self.create_publisher(Image, '/camera_call', 10)
        self.image_tablet_pub = self.create_publisher(Bool, '/image_tablet', 10)

        # Subscribers (system -> robot)
        self.create_subscription(String, '/speak', self.on_speak, 10)
        self.create_subscription(Bool, '/record', self.on_record, 10)
        self.create_subscription(Bool, '/record_no_mic', self.on_record_no_mic, 10)
        self.create_subscription(Bool, '/end', self.on_end, 10)
        self.create_subscription(Bool, '/start_bdi', self.on_start_bdi, 10)
        self.create_subscription(Bool, '/get_camera', self.on_get_camera, 10)
        self.create_subscription(Track, '/track', self.on_track, 10)
        self.create_subscription(PostureWithSpeed, '/posture', self.on_posture, 10)
        self.create_subscription(Int32, '/state', self.on_state, 10)
        self.create_subscription(JointAnglesWithSpeed, '/joint_angles_with_speed', self.on_joint_angles, 10)
        self.create_subscription(Vector3, '/walk', self.on_walk, 10)
        self.create_subscription(Hand, '/hands', self.on_hands, 10)

        # Timers
        self.create_timer(1.0, self.publish_sonar)
        self.create_timer(1.0, self.publish_bumper)
        self.create_timer(1.0, self.publish_position)

        self.get_logger().info('Mock robot node avviato (senza hardware).')

    # ---- Timed publishers ----
    def publish_sonar(self):
        msg = Sonar()
        msg.front_sonar = 0.7
        msg.back_sonar = 0.9
        self.sonar_pub.publish(msg)

    def publish_bumper(self):
        msg = Bumper()
        msg.left = 0.0
        msg.right = 0.0
        msg.back = 0.0
        self.bumper_pub.publish(msg)

    def publish_position(self):
        msg = Vector3()
        msg.x = 0.0
        msg.y = 0.0
        msg.z = 0.0
        self.position_pub.publish(msg)

    # ---- Callbacks ----
    def on_speak(self, msg: String):
        self.get_logger().info(f"[MOCK] /speak: {msg.data}")
        self._publish_speaking(duration=1.0)

    def on_record(self, msg: Bool):
        if not msg.data:
            return
        self.get_logger().info("[MOCK] /record: start")
        self._publish_transcription("Trascrizione simulata da /record")

    def on_record_no_mic(self, msg: Bool):
        if not msg.data:
            return
        self.get_logger().info("[MOCK] /record_no_mic: start")
        self._publish_transcription("Trascrizione simulata da /record_no_mic")

    def on_end(self, msg: Bool):
        self.get_logger().info(f"[MOCK] /end: {msg.data}")

    def on_start_bdi(self, msg: Bool):
        self.get_logger().info(f"[MOCK] /start_bdi: {msg.data}")
        self.is_speaking_bdi_pub.publish(msg)

    def on_get_camera(self, msg: Bool):
        if not msg.data:
            return
        self.get_logger().info("[MOCK] /get_camera: invio immagine fittizia")
        img = Image()
        img.height = 1
        img.width = 1
        img.encoding = 'rgb8'
        img.is_bigendian = 0
        img.step = 3
        img.data = bytes([0, 0, 0])
        self.camera_pub.publish(img)

        ok = Bool()
        ok.data = True
        self.image_tablet_pub.publish(ok)

    def on_track(self, msg: Track):
        self.get_logger().info(f"[MOCK] /track: {msg.target_name} dist={msg.distance}")

    def on_posture(self, msg: PostureWithSpeed):
        self.get_logger().info(f"[MOCK] /posture: {msg.posture_name} speed={msg.speed}")

    def on_state(self, msg: Int32):
        self.get_logger().info(f"[MOCK] /state: {msg.data}")

    def on_joint_angles(self, msg: JointAnglesWithSpeed):
        self.get_logger().info(f"[MOCK] /joint_angles_with_speed: {len(msg.names)} joints")

    def on_walk(self, msg: Vector3):
        self.get_logger().info(f"[MOCK] /walk: x={msg.x} y={msg.y} z={msg.z}")

    def on_hands(self, msg: Hand):
        self.get_logger().info(f"[MOCK] /hands: {msg.hand} fun={msg.fun}")

    # ---- Helpers ----
    def _publish_speaking(self, duration: float = 1.0):
        msg = Bool()
        msg.data = True
        self.is_speaking_pub.publish(msg)

        def _stop():
            end_msg = Bool()
            end_msg.data = False
            self.is_speaking_pub.publish(end_msg)
        threading.Timer(duration, _stop).start()

    def _publish_transcription(self, text: str):
        def _do_publish():
            msg = String()
            msg.data = text
            self.transcription_pub.publish(msg)
            self.transcription_bdi_pub.publish(msg)

            stt = String()
            stt.data = text
            self.stt_pub.publish(stt)
            self.stt_bdi_pub.publish(stt)

            touched = Bool()
            touched.data = True
            self.touched_pub.publish(touched)

            start = Bool()
            start.data = True
            self.start_conv_pub.publish(start)

        threading.Timer(0.5, _do_publish).start()


def main(args=None):
    rclpy.init(args=args)
    node = QiUnipaMock()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
