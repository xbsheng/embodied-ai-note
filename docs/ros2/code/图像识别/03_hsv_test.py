import cv2
import numpy as np

def hsv_test():
    # 打开默认摄像头
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Error: 无法打开摄像头")
        return

    print("摄像头已打开。")
    print("显示窗口说明:")
    print("  - Original: 原始 BGR 图像")
    print("  - Hue: 色调通道 (H)")
    print("  - Saturation: 饱和度通道 (S)")
    print("  - Value: 亮度通道 (V)")
    print("按 'q' 键退出...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: 无法读取帧")
            break

        # 将 BGR 图像转换为 HSV 图像
        hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 分离 HSV 通道
        # h: 色调 (0-179)
        # s: 饱和度 (0-255)
        # v: 亮度 (0-255)
        h, s, v = cv2.split(hsv_image)

        # 显示原始图像和分离后的三个通道
        cv2.imshow('Original', frame)
        cv2.imshow('Hue', h)
        cv2.imshow('Saturation', s)
        cv2.imshow('Value', v)

        # 按 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    hsv_test()
