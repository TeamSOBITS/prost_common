import rclpy
from rclpy.node import Node
import cv2
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

# ROSトピックのキューサイズ
QUEUE_SIZE = 10


class QrRecode(Node):

    def __init__(self):
        super().__init__('qr_recode')
        self.get_logger().info("qr_recode Started")

        self.bridge_qr = CvBridge()
        self.pub_ros_scratch = self.create_publisher(String, '/ros_scratch', QUEUE_SIZE)

        self.image_sub_qr = self.create_subscription(
            Image,
            "/image_raw",
            self.qr_recode,
            QUEUE_SIZE
        )

        self.detector = cv2.QRCodeDetector()

    def qr_recode(self, data):
        try:
            cv_image = self.bridge_qr.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(str(e))
            return

        text, points, _ = self.detector.detectAndDecode(cv_image)

        if text:

            try:
                fixed = text.encode("latin1").decode("shift_jis")
            except Exception:
                fixed = text  

            msg = String()
            msg.data = "qr_recode:" + fixed
            self.pub_ros_scratch.publish(msg)
            self.get_logger().info(f"[Detected QR] {fixed}")


def main(args=None):
    rclpy.init(args=args)
    qr_node = QrRecode()
    rclpy.spin(qr_node)
    qr_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
