import threading
import time
import json
from pynput.keyboard import Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener
from PIL import ImageGrab
import numpy as np
import cv2
import os

# 保存日志的路径
log_file_path = "game_logs.json"

# 日志结构
log_data = []


# 捕获键盘输入记录
def on_key_press(key):
    event_time = time.time()
    log_entry = {
        'timestamp': event_time,
        'event_type': 'key_press',
        'key': str(key)
    }
    log_data.append(log_entry)
    print(f"Key pressed: {key}")


# 捕获鼠标点击记录
def on_mouse_click(x, y, button, pressed):
    event_time = time.time()
    event_type = 'mouse_press' if pressed else 'mouse_release'
    log_entry = {
        'timestamp': event_time,
        'event_type': event_type,
        'position': (x, y),
        'button': str(button)
    }
    log_data.append(log_entry)
    print(f"Mouse {event_type} at ({x}, {y}) with {button}")


# 捕获屏幕状态
def capture_screen(region=(0, 0, 1920, 1080), output_dir="screenshots"):
    # 创建截图保存目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取当前时间作为文件名
    timestamp = time.time()
    screenshot = ImageGrab.grab(bbox=region)
    screenshot_np = np.array(screenshot)

    # 保存截图文件
    screenshot_filename = f"{output_dir}/screenshot_{timestamp}.png"
    cv2.imwrite(screenshot_filename, cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR))

    # 记录截图的文件路径和时间戳
    log_entry = {
        'timestamp': timestamp,
        'event_type': 'screenshot',
        'file_path': screenshot_filename
    }
    log_data.append(log_entry)
    print(f"Captured screenshot at {screenshot_filename}")


# 定期捕捉游戏状态
def capture_game_state(interval=1):
    while True:
        capture_screen()
        time.sleep(interval)  # 每隔interval秒捕获一次屏幕状态


# 保存日志数据
def save_logs():
    with open(log_file_path, 'w') as log_file:
        json.dump(log_data, log_file, indent=4)
    print(f"Logs saved to {log_file_path}")


# 主程序
def main():
    # 启动键盘和鼠标事件监听
    with KeyboardListener(on_press=on_key_press) as keyboard_listener, \
            MouseListener(on_click=on_mouse_click) as mouse_listener:

        # 在单独的线程中捕获游戏状态
        try:
            capture_game_state_thread = threading.Thread(target=capture_game_state)
            capture_game_state_thread.start()

            # 保持监听直到用户停止
            keyboard_listener.join()
            mouse_listener.join()

        except KeyboardInterrupt:
            print("程序终止中...")

        # 保存操作和状态日志
        save_logs()


if __name__ == "__main__":
    main()
