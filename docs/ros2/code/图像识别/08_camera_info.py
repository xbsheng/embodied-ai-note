import cv2
import numpy as np
import math

def main():
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: 无法打开摄像头")
        return

    # 固化参数 (HSV 阈值)
    h_min, h_max = 80, 113
    s_min, s_max = 137, 251
    v_min, v_max = 96, 255
    erode_iter = 1
    dilate_iter = 1
    min_area = 1000

    # 物理参数
    REAL_WIDTH = 30.0  # 物体实际宽度 (mm)
    REAL_HEIGHT = 30.0 # 物体实际高度 (mm)
    
    # 摄像头参数 (需要校准，这里使用估算值)
    # 焦距 (像素) F = (PixelWidth * Distance) / RealWidth
    # 假设在距离 300mm 处，30mm 的物体占据 55 个像素，则 F = 55 * 300 / 30 = 550
    FOCAL_LENGTH = 550.0 

    print("正在运行摄像头信息计算工具...")
    print(f"物体实际尺寸: {REAL_WIDTH}x{REAL_HEIGHT} mm")
    print(f"预设焦距: {FOCAL_LENGTH} (请根据实际情况校准)")
    print("按 'q' 键退出。")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 获取图像中心点
        img_h, img_w = frame.shape[:2]
        frame_center_x = img_w // 2
        frame_center_y = img_h // 2

        imgContour = frame.copy()
        imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])
        mask = cv2.inRange(imgHSV, lower, upper)

        kernel = np.ones((5, 5), np.uint8)
        if erode_iter > 0:
            mask = cv2.erode(mask, kernel, iterations=erode_iter)
        if dilate_iter > 0:
            mask = cv2.dilate(mask, kernel, iterations=dilate_iter)

        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                # 使用最小外接矩形 (MinAreaRect) 以获取旋转角度和精确宽高
                rect = cv2.minAreaRect(cnt)
                (cx, cy), (w, h), angle = rect

                # 规范化宽高 (取长边为宽，短边为高，或根据实际逻辑调整)
                # 这里假设物体是正方形，取平均值或最大值可能更稳定
                # 为了计算倾斜角，我们需要区分长短边
                pixel_long = max(w, h)
                pixel_short = min(w, h)
                
                # 1. 计算安装高度 (距离)
                # 使用相似三角形原理: Height = (RealWidth * FocalLength) / PixelWidth
                # 使用长边计算距离通常更准确 (受倾斜影响较小)
                distance = (REAL_WIDTH * FOCAL_LENGTH) / pixel_long

                # 2. 计算安装偏移角度 (倾斜角)
                # 假设物体是正方形，如果像素宽高比不为1，说明有倾斜
                # cos(theta) = Short / Long
                if pixel_long > 0:
                    ratio = pixel_short / pixel_long
                    # 限制 ratio 范围防止数学错误
                    ratio = min(max(ratio, 0.0), 1.0)
                    tilt_angle_rad = math.acos(ratio)
                    tilt_angle_deg = math.degrees(tilt_angle_rad)
                else:
                    tilt_angle_deg = 0

                # 3. 计算物体偏离图像中心的偏移量 (像素)
                offset_x = cx - frame_center_x
                offset_y = cy - frame_center_y

                # 绘制旋转矩形
                box = cv2.boxPoints(rect)
                box = np.int64(box)
                cv2.drawContours(imgContour, [box], 0, (0, 0, 255), 2)
                
                # 绘制中心点
                cv2.circle(imgContour, (int(cx), int(cy)), 5, (0, 255, 0), cv2.FILLED)
                
                # 绘制图像中心十字
                cv2.line(imgContour, (frame_center_x - 10, frame_center_y), (frame_center_x + 10, frame_center_y), (255, 255, 0), 2)
                cv2.line(imgContour, (frame_center_x, frame_center_y - 10), (frame_center_x, frame_center_y + 10), (255, 255, 0), 2)

                # 计算文本显示的基准坐标 (使用外接矩形的左上角)
                x, y, w_bound, h_bound = cv2.boundingRect(box)

                # 显示信息
                # 第一行: 像素宽高
                cv2.putText(imgContour, f"Px: {int(w)}x{int(h)}", (int(x), int(y) - 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                # 第二行: 计算的高度 (距离)
                cv2.putText(imgContour, f"Height: {distance:.1f} mm", (int(x), int(y) - 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # 第三行: 倾斜角度 (Tilt)
                cv2.putText(imgContour, f"Tilt: {tilt_angle_deg:.1f} deg", (int(x), int(y) - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # 第四行: 中心偏移
                cv2.putText(imgContour, f"Offset: {int(offset_x)}, {int(offset_y)}", (int(x), int(y)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                # 临时变量 x, y 用于定位文字 (minAreaRect 不返回 x,y，我们用 center 估算或取 box 的顶点)
                # 为了文字显示方便，取 box 的最高点
                # box 顶点顺序不固定，这里简单取 int(cx) 和 int(cy) 附近显示即可，上面的 y 偏移可能需要基于 box 的 min_y
                # 修正文字位置:
                min_y = np.min(box[:, 1])
                min_x = np.min(box[:, 0])
                
                cv2.putText(imgContour, f"H:{distance:.0f}mm A:{tilt_angle_deg:.0f}deg", (min_x, min_y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("Mask", mask)
        cv2.imshow("Result", imgContour)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
