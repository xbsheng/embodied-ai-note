import cv2
import numpy as np

def create_image():
    # 创建一个 300x300 的黑色背景图片 (3通道, uint8类型)
    # 高度 300, 宽度 300, 通道 3 (BGR)
    img = np.zeros((300, 300, 3), dtype=np.uint8)

    # 将第3行到第10行的内容修改为红色
    # 在 OpenCV 中，颜色顺序为 BGR，红色为 (0, 0, 255)
    # Python 索引从 0 开始，第 3 行对应索引 2
    # 切片范围 [start:end] 是左闭右开，第 10 行对应索引 9，如果要包含第 10 行，结束索引应为 10 (即包含 2,3,4,5,6,7,8,9 对应第3到第10行)
    # 也可以理解为 2:10 覆盖了 8 行像素
    img[2:10, :] = [0, 0, 255]

    # 将第100行的第100列，到第200行的第200列修改为蓝色
    # 对应索引 99 到 199 (切片 99:200)
    # 蓝色 (255, 0, 0)
    img[99:200, 99:200] = [255, 0, 0]

    # 输出效果
    cv2.imshow('Image', img)
    
    print("按任意键关闭窗口...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    create_image()
