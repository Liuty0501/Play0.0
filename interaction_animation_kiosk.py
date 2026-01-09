import cv2 
import serial
import time
import vlc
from PIL import ImageFont, ImageDraw, Image
import numpy as np
import os

# 配置参数
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600
VIDEO_PATH = r'animial.mp4'
FONT_PATH = r"font.ttf"
VLC_PATH = r"C:\Program Files\VideoLAN\VLC"

# 初始化VLC环境
if os.path.exists(VLC_PATH):
    os.add_dll_directory(VLC_PATH)

# 初始化串口
ser = None
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)  # 缩短超时时间
    ser.flushInput()  # 清空缓冲区
    print("串口连接成功，开始监听...")
except Exception as e:
    print(f"串口连接失败: {e}")

# 预渲染旋转文字（增大字体）
def create_rotated_text():
    try:
        # 增大字体到60
        font = ImageFont.truetype(FONT_PATH, 60)
    except:
        print("使用备用字体")
        # 备用字体也增大
        font = ImageFont.load_default()
        font.size = 60
    
    text = "请使用下方卡片刷卡进入闸机"
    # 计算文字尺寸
    text_size = font.getbbox(text)
    w, h = text_size[2], text_size[3]
    
    # 创建文字图像（带背景）- 增大背景框
    text_img = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 200))  # 更深的背景
    draw = ImageDraw.Draw(text_img)
    # 文字位置居中
    draw.text((20, 20), text, font=font, fill=(255, 255, 255, 255))
    
    # 旋转90度并转换格式
    rotated = text_img.rotate(90, expand=True)
    return np.array(rotated), rotated.width, rotated.height

# 播放带声音的视频
def play_video_with_sound(path):
    print("开始播放刷卡视频...")
    instance = vlc.Instance("--no-xlib --quiet")  # 禁用GUI组件
    player = instance.media_player_new()
    media = instance.media_new(path)
    player.set_media(media)
    player.play()
    
    # 等待播放启动
    start_time = time.time()
    while player.get_state() not in [vlc.State.Playing, vlc.State.Ended]:
        if time.time() - start_time > 3:  # 3秒超时
            print("视频启动超时")
            break
        time.sleep(0.1)
    
    # 精确等待播放结束
    while player.get_state() not in [vlc.State.Ended, vlc.State.Stopped]:
        time.sleep(0.2)
    
    player.stop()
    print("视频播放完成，返回摄像头")
    cv2.destroyAllWindows()  # 清理残留窗口

# 显示摄像头画面
def show_camera_with_text():
    # 预渲染文字（使用更大的字体）
    text_img, text_w, text_h = create_rotated_text()
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # 使用DirectShow加速
    if not cap.isOpened():
        print("无法打开摄像头")
        return
    
    # 设置高分辨率和高帧率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # 创建全屏窗口
    cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Camera", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    print("摄像头开启，等待刷卡...")
    last_card_time = time.time()
    last_serial_check = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("摄像头读取失败")
            break
        
        # 高效叠加文字（使用OpenCV操作）
        y_pos = (frame.shape[0] - text_h) // 2
        x_pos = (frame.shape[1] - text_w) // 2
        
        # 确保位置在图像范围内
        if x_pos < 0 or y_pos < 0 or (x_pos + text_w) > frame.shape[1] or (y_pos + text_h) > frame.shape[0]:
            # 如果文字超出范围，居中显示但缩小尺寸
            scale = min(frame.shape[1]/text_w, frame.shape[0]/text_h) * 0.9
            new_w = int(text_w * scale)
            new_h = int(text_h * scale)
            resized_text = cv2.resize(text_img, (new_w, new_h))
            y_pos = (frame.shape[0] - new_h) // 2
            x_pos = (frame.shape[1] - new_w) // 2
            
            # 获取ROI区域
            roi = frame[y_pos:y_pos+new_h, x_pos:x_pos+new_w]
            
            # 提取alpha通道
            mask = resized_text[:, :, 3]  # Alpha通道
            mask_inv = cv2.bitwise_not(mask)
            
            # 混合图像
            bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
            fg = cv2.bitwise_and(resized_text[:, :, :3], resized_text[:, :, :3], mask=mask)
            frame[y_pos:y_pos+new_h, x_pos:x_pos+new_w] = cv2.add(bg, fg)
        else:
            # ROI区域处理
            roi = frame[y_pos:y_pos+text_h, x_pos:x_pos+text_w]
            
            # 提取alpha通道
            mask = text_img[:, :, 3]  # Alpha通道
            mask_inv = cv2.bitwise_not(mask)
            
            # 混合图像
            bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
            fg = cv2.bitwise_and(text_img[:, :, :3], text_img[:, :, :3], mask=mask)
            frame[y_pos:y_pos+text_h, x_pos:x_pos+text_w] = cv2.add(bg, fg)
        
        cv2.imshow("Camera", frame)
        
        # 键盘退出检测
        if cv2.waitKey(1) & 0xFF == ord('q'):
            ser.close()
            break
        
        # 定期检查串口（每0.1秒检查一次）
        current_time = time.time()
        if current_time - last_serial_check > 0.1:
            last_serial_check = current_time
            
            # 串口检测（非阻塞）
            if ser and ser.in_waiting > 0:
                try:
                    data = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
                    # 校验有效刷卡信号
                    if 'C' in data and current_time - last_card_time > 1.0:
                        print(f"检测到刷卡信号: {data.strip()}")
                        last_card_time = current_time
                        cap.release()
                        cv2.destroyAllWindows()
                        play_video_with_sound(VIDEO_PATH)
                        return
                except Exception as e:
                    print(f"串口错误: {e}")
    
    cap.release()
    cv2.destroyAllWindows()

# 主程序
if __name__ == "__main__":
    while True:
        show_camera_with_text()