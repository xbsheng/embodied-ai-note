import cv2
import numpy as np

def empty(a):
    pass

def main():
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: 无法打开摄像头")
        return

    # 创建控制面板窗口
    cv2.namedWindow("TrackBars")
    cv2.resizeWindow("TrackBars", 640, 350)

    # 创建 HSV 阈值调节滑块
    cv2.createTrackbar("Hue Min", "TrackBars", 0, 179, empty)
    cv2.createTrackbar("Hue Max", "TrackBars", 179, 179, empty)
    cv2.createTrackbar("Sat Min", "TrackBars", 0, 255, empty)
    cv2.createTrackbar("Sat Max", "TrackBars", 255, 255, empty)
    cv2.createTrackbar("Val Min", "TrackBars", 0, 255, empty)
    cv2.createTrackbar("Val Max", "TrackBars", 255, 255, empty)

    # 创建腐蚀和膨胀迭代次数调节滑块
    cv2.createTrackbar("Erode Iter", "TrackBars", 0, 10, empty)
    cv2.createTrackbar("Dilate Iter", "TrackBars", 0, 10, empty)

    print("正在运行 HSV 遮罩调试工具...")
    print("调整 'TrackBars' 窗口中的滑块来过滤颜色。")
    print("按 'q' 键退出。")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: 无法读取帧")
            break

        # 转换为 HSV 空间
        imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 获取滑块当前值
        h_min = cv2.getTrackbarPos("Hue Min", "TrackBars")
        h_max = cv2.getTrackbarPos("Hue Max", "TrackBars")
        s_min = cv2.getTrackbarPos("Sat Min", "TrackBars")
        s_max = cv2.getTrackbarPos("Sat Max", "TrackBars")
        v_min = cv2.getTrackbarPos("Val Min", "TrackBars")
        v_max = cv2.getTrackbarPos("Val Max", "TrackBars")
        erode_iter = cv2.getTrackbarPos("Erode Iter", "TrackBars")
        dilate_iter = cv2.getTrackbarPos("Dilate Iter", "TrackBars")

        # 定义 HSV 范围数组
        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])

        # 创建 Mask
        mask = cv2.inRange(imgHSV, lower, upper)

        # 形态学操作 kernel
        kernel = np.ones((5, 5), np.uint8)

        # 腐蚀操作 (Erosion): 消除噪点
        if erode_iter > 0:
            mask = cv2.erode(mask, kernel, iterations=erode_iter)
        
        # 膨胀操作 (Dilation): 填补孔洞
        if dilate_iter > 0:
            mask = cv2.dilate(mask, kernel, iterations=dilate_iter)

        # 使用 Mask 提取原图中的目标区域
        result = cv2.bitwise_and(frame, frame, mask=mask)

        # 显示窗口
        cv2.imshow("Original", frame)
        cv2.imshow("Mask", mask)
        cv2.imshow("Result", result)

        # 按 'q' 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
