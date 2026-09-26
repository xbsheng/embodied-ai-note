import cv2
import numpy as np

def main():
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: 无法打开摄像头")
        return

    # 固化参数
    h_min, h_max = 80, 113
    s_min, s_max = 137, 251
    v_min, v_max = 96, 255
    erode_iter = 1
    dilate_iter = 1
    min_area = 1000

    print("正在运行盒子检测工具 (固定参数)...")
    print(f"HSV范围: H[{h_min}-{h_max}], S[{s_min}-{s_max}], V[{v_min}-{v_max}]")
    print("按 'q' 键退出。")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 复制一份用于绘制结果
        imgContour = frame.copy()

        # 图像预处理
        imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

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

                # 标注中心点坐标
                cv2.putText(imgContour, f"Center:({cx}, {cy})", (x, y - 25), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # 标注宽高
                cv2.putText(imgContour, f"W:{w} H:{h}", (x, y - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # 显示窗口
        cv2.imshow("Mask", mask)
        cv2.imshow("Result", imgContour)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
