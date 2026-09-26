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
    cv2.namedWindow("Parameters")
    cv2.resizeWindow("Parameters", 640, 350)

    # 初始 HSV 阈值 (示例值，可根据实际情况调整)
    # 默认范围设为宽泛，方便用户通过滑块调节
    cv2.createTrackbar("Hue Min", "Parameters", 0, 179, empty)
    cv2.createTrackbar("Hue Max", "Parameters", 179, 179, empty)
    cv2.createTrackbar("Sat Min", "Parameters", 0, 255, empty)
    cv2.createTrackbar("Sat Max", "Parameters", 255, 255, empty)
    cv2.createTrackbar("Val Min", "Parameters", 0, 255, empty)
    cv2.createTrackbar("Val Max", "Parameters", 255, 255, empty)

    # 腐蚀和膨胀迭代次数
    cv2.createTrackbar("Erode Iter", "Parameters", 1, 10, empty)
    cv2.createTrackbar("Dilate Iter", "Parameters", 1, 10, empty)
    
    # 最小面积阈值，过滤小噪点
    cv2.createTrackbar("Min Area", "Parameters", 1000, 20000, empty)

    print("正在运行 HSV 物体定位工具...")
    print("调整滑块以选中目标物体。")
    print("按 'q' 键退出。")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 复制一份用于绘制结果
        imgContour = frame.copy()

        # 图像预处理
        imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 获取滑块参数
        h_min = cv2.getTrackbarPos("Hue Min", "Parameters")
        h_max = cv2.getTrackbarPos("Hue Max", "Parameters")
        s_min = cv2.getTrackbarPos("Sat Min", "Parameters")
        s_max = cv2.getTrackbarPos("Sat Max", "Parameters")
        v_min = cv2.getTrackbarPos("Val Min", "Parameters")
        v_max = cv2.getTrackbarPos("Val Max", "Parameters")
        erode_iter = cv2.getTrackbarPos("Erode Iter", "Parameters")
        dilate_iter = cv2.getTrackbarPos("Dilate Iter", "Parameters")
        min_area = cv2.getTrackbarPos("Min Area", "Parameters")

        # 创建 Mask
        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])
        mask = cv2.inRange(imgHSV, lower, upper)

        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        if erode_iter > 0:
            mask = cv2.erode(mask, kernel, iterations=erode_iter)
        if dilate_iter > 0:
            mask = cv2.dilate(mask, kernel, iterations=dilate_iter)

        # 轮廓检测
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # 过滤小面积噪点
            if area > min_area:
                # 绘制轮廓 (可选)
                # cv2.drawContours(imgContour, cnt, -1, (255, 0, 255), 2)

                # 计算外接矩形
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                x, y, w, h = cv2.boundingRect(approx)

                # 绘制红色边框
                cv2.rectangle(imgContour, (x, y), (x + w, y + h), (0, 0, 255), 2)

                # 计算中心点
                cx = x + w // 2
                cy = y + h // 2

                # 绘制中心点 (绿色圆点)
                cv2.circle(imgContour, (cx, cy), 5, (0, 255, 0), cv2.FILLED)

                # 标注坐标文本
                cv2.putText(imgContour, f"({cx}, {cy})", (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # 显示窗口
        # 堆叠显示 Mask (转为3通道以便堆叠) 和 结果图
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        # 水平拼接显示，方便对比
        # hstack = np.hstack([mask_bgr, imgContour])
        
        cv2.imshow("Mask", mask)
        cv2.imshow("Result", imgContour)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
