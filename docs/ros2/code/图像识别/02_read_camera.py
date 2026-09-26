import cv2

def read_camera():
    # 打开默认摄像头 (索引通常为 1)
    cap = cv2.VideoCapture(1)

    # 检查摄像头是否成功打开
    if not cap.isOpened():
        print("Error: 无法打开摄像头")
        return

    print("摄像头已打开，按 'q' 键退出...")

    while True:
        # 读取一帧
        # ret: 布尔值，表示是否读取成功
        # frame: 读取到的图像帧
        ret, frame = cap.read()

        if not ret:
            print("Error: 无法读取帧 (可能摄像头已断开)")
            break

        # 将第50行50列到第100行200列的区域，颜色设置为红色
        # 对应索引 49:100 (行) 和 49:200 (列)
        frame[49:100, 49:200] = [0, 0, 255]

        # 显示图像
        cv2.imshow('Camera Feed', frame)

        # 等待按键，延迟 1ms
        # 如果按下 'q' 键 (ASCII 码判断)，则退出循环
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    print("摄像头已关闭")

if __name__ == "__main__":
    read_camera()
