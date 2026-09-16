import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError


# RGB / HSV の切り替え
# True → HSV
# False → RGB
USE_HSV = False

# ROSトピックのキューサイズ
QUEUE_SIZE = 10

# ROI（640×480 の中央付近）
ROI_HEIGHT_MIN = 230
ROI_HEIGHT_MAX = 250
ROI_WIDTH_MIN = 310
ROI_WIDTH_MAX = 330

# RGB分類のしきい値
RGB_LOW = 50
RGB_WHITE_MIN = 150
RGB_WHITE_MAX = 200
RGB_RED_OTHER_MAX = 100
RGB_YELLOW_GREEN_G_MAX = 60

# HSV分類のしきい値
HSV_BLACK_V_MAX = 60
HSV_WHITE_S_MAX = 40
HSV_WHITE_V_MIN = 200
HSV_RED_HUE_MAX = 25
HSV_RED_HUE_MIN = 330
HSV_HUE_MAX = 360
HSV_GREEN_HUE_MIN = 150
HSV_GREEN_HUE_MAX = 180
HSV_GREEN_S_MIN = 50
HSV_CYAN_HUE_MIN = 150
HSV_CYAN_HUE_MAX = 210
HSV_CYAN_S_MIN = 60
HSV_CYAN_V_MIN = 70
HSV_BLUE_HUE_MIN = 210
HSV_BLUE_HUE_MAX = 260
HSV_BLUE_S_MIN = 50
HSV_PURPLE_HUE_MIN = 210
HSV_PURPLE_HUE_MAX = 280

# OpenCVのHueは0-179で扱われるため、一般的な0-360のHue値へ変換する係数
OPENCV_HUE_SCALE = 2


def map_rgb_to_color_name(r, g, b):
    if b < RGB_LOW and g < RGB_LOW and r < RGB_LOW:
        return "黒"
    elif RGB_WHITE_MIN < b < RGB_WHITE_MAX and RGB_WHITE_MIN < g < RGB_WHITE_MAX and RGB_WHITE_MIN < r < RGB_WHITE_MAX:
        return "白"
    elif r > g and r > b and g < RGB_RED_OTHER_MAX and b < RGB_RED_OTHER_MAX:
        return "赤"
    elif b > g and b > r and r < RGB_LOW:
        return "青"
    elif g > b and g > r and r < RGB_LOW:
        return "緑"
    elif r > g and b > g:
        return "紫"
    # elif r > b and g > b and r > 150 and g > 150:
    #     return "黃"
    elif g > r and b > r:
        return "水色"

    elif g > r and b > r:
        return "グレイ"
    elif g < r and g < RGB_YELLOW_GREEN_G_MAX and r < RGB_LOW:
        return "黄緑"

    return "不明"



def map_hsv_to_color_name(H, S, V):

    if V < HSV_BLACK_V_MAX:
        return "黒"
    if S < HSV_WHITE_S_MAX and V > HSV_WHITE_V_MIN:
        return "白"
    if (0 <= H < HSV_RED_HUE_MAX) or (HSV_RED_HUE_MIN <= H <= HSV_HUE_MAX):
        return "赤"
    if HSV_GREEN_HUE_MIN <= H < HSV_GREEN_HUE_MAX and S > HSV_GREEN_S_MIN:
        return "緑"
    if HSV_CYAN_HUE_MIN <= H < HSV_CYAN_HUE_MAX and S > HSV_CYAN_S_MIN and V > HSV_CYAN_V_MIN:
        return "水色"
    if HSV_BLUE_HUE_MIN <= H < HSV_BLUE_HUE_MAX and S > HSV_BLUE_S_MIN:
        return "青"
    if HSV_PURPLE_HUE_MIN <= H < HSV_PURPLE_HUE_MAX:
        return "紫"

    return "不明"


class RGBAverage(Node):

    def __init__(self):
        super().__init__('rgb_average_value')
        self.get_logger().info("rgb_average_value Started")

        self.bridge = CvBridge()

        self.height_min_range = ROI_HEIGHT_MIN
        self.height_max_range = ROI_HEIGHT_MAX
        self.width_min_range = ROI_WIDTH_MIN
        self.width_max_range = ROI_WIDTH_MAX

        self.b = []
        self.g = []
        self.r = []

        self.pub_ros_scratch = self.create_publisher(String, '/ros_scratch', QUEUE_SIZE)

        self.image_sub_rgb = self.create_subscription(
            Image,
            "/image_raw",
            self.image_rgb_ave,
            QUEUE_SIZE
        )

    def image_rgb_ave(self, ros_image):
        try:
            frame = self.bridge.imgmsg_to_cv2(ros_image, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(str(e))
            return

        # 対象領域デバッグ用
        # cv2.rectangle(
        #     frame,
        #     (self.width_min_range, self.height_min_range),
        #     (self.width_max_range, self.height_max_range),
        #     (255, 255, 255),
        #     1
        # )
        # cv2.imshow("ROI Debug", frame)
        # cv2.waitKey(1)


        # ROIのRGB値を取得
        for i in range(self.height_min_range, self.height_max_range):
            for j in range(self.width_min_range, self.width_max_range):
                self.b.append(frame[i][j][0])
                self.g.append(frame[i][j][1])
                self.r.append(frame[i][j][2])

        # 平均RGBを計算
        b_ave = sum(self.b) / len(self.b)
        g_ave = sum(self.g) / len(self.g)
        r_ave = sum(self.r) / len(self.r)

        # RGB / HSV の切り替え部分
        if USE_HSV:
            bgr_pixel = np.uint8([[[b_ave, g_ave, r_ave]]])
            hsv_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2HSV)[0][0]

            H = int(hsv_pixel[0] * OPENCV_HUE_SCALE)
            S = int(hsv_pixel[1])
            V = int(hsv_pixel[2])

            color_name = map_hsv_to_color_name(H, S, V)

            self.pub_ros_scratch.publish(String(data=f"hsv_H:{H}"))
            self.pub_ros_scratch.publish(String(data=f"hsv_S:{S}"))
            self.pub_ros_scratch.publish(String(data=f"hsv_V:{V}"))
            self.pub_ros_scratch.publish(String(data=f"color:{color_name}"))


        else:
            color_name = map_rgb_to_color_name(r_ave, g_ave, b_ave)

            self.pub_ros_scratch.publish(String(data=f"rgb_r:{r_ave}"))
            self.pub_ros_scratch.publish(String(data=f"rgb_g:{g_ave}"))
            self.pub_ros_scratch.publish(String(data=f"rgb_b:{b_ave}"))
            self.pub_ros_scratch.publish(String(data=f"color:{color_name}"))

        # 初期化
        self.b = []
        self.g = []
        self.r = []


def main(args=None):
    rclpy.init(args=args)
    node = RGBAverage()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
