import time
import json
import threading
from pynput.keyboard import Listener as KeyboardListener, KeyCode
from pynput.mouse import Listener as MouseListener, Controller as MouseController
from PIL import ImageGrab
import numpy as np
import cv2
import os

# 保存日志的路径
log_file_path = "game_logs.json"

# 目标图案文件路径
target_image_path = 'target.png'

# 日志结构
log_data = []

# 运行状态
is_running = False

# 当前鼠标位置
current_mouse_position = (0, 0)

# 创建鼠标控制器
mouse_controller = MouseController()
last_record_time = time.time()
record_interval = 0.1  # 记录间隔为0.1秒

# 捕获键盘输入记录
def on_key_press(key):
    global is_running
    if isinstance(key, KeyCode) and key.char == 'm':
        is_running = not is_running
        if is_running:
            print("程序已启动")
        else:
            print("程序已暂停")
    else:
        if is_running:
            event_time = time.time()
            log_entry = {
                'timestamp': event_time,
                'event_type': 'key_press',
                'key': str(key)
            }
            log_data.append(log_entry)
            save_logs()  # 每次捕获后立即保存日志
            print(f"Key pressed: {key}")


# 捕获鼠标点击记录
def on_mouse_click(x, y, button, pressed):
    if is_running:
        event_time = time.time()
        event_type = 'mouse_press' if pressed else 'mouse_release'
        log_entry = {
            'timestamp': event_time,
            'event_type': event_type,
            'position': (x, y),
            'button': str(button)
        }
        log_data.append(log_entry)
        save_logs()  # 每次捕获后立即保存日志
        print(f"Mouse {event_type} at ({x}, {y}) with {button}")


# 捕获鼠标位移记录m
def on_mouse_move(x, y):
    global last_record_time
    if is_running:
        current_time = time.time()
        if current_time - last_record_time >= record_interval:
            last_record_time = current_time
            log_entry = {
                'timestamp': current_time,
                'event_type': 'mouse_move',
                'position': (x, y)
            }
            log_data.append(log_entry)
            save_logs()  # 每次捕获后立即保存日志
            print(f"Mouse moved to ({x}, {y})")


# 捕获屏幕状态并检测目标图案
def capture_screen(region=(0, 0, 1920, 1080), output_dir="screenshots"):
    if is_running:
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
        save_logs()  # 每次捕获后立即保存日志
        print(f"Captured screenshot at {screenshot_filename}")

        # 检测目标图案
        if detect_target(screenshot_np):
            print("目标图案检测到！")
            # 在这里添加调整视角或其他处理逻辑
            log_entry = {
                'timestamp': timestamp,
                'event_type': 'target_detected',
                'file_path': screenshot_filename
            }
            log_data.append(log_entry)
            save_logs()


# 检测目标图案
def detect_target(image_np):
    target = cv2.imread(target_image_path, cv2.IMREAD_GRAYSCALE)
    if target is None:
        print(f"无法读取目标图案文件: {target_image_path}")
        return False

    # 转换屏幕截图为灰度图
    screenshot_gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

    # 模板匹配
    result = cv2.matchTemplate(screenshot_gray, target, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # 设置一个阈值来判断是否检测到目标
    threshold = 0.8
    if max_val >= threshold:
        return True
    return False


# 定期捕捉游戏状态
def capture_game_state(interval=1):
    while True:
        if is_running:
            capture_screen()
        time.sleep(interval)  # 每隔interval秒捕获一次屏幕状态


# 保存日志数据
def save_logs():
    with open(log_file_path, 'w') as log_file:
        json.dump(log_data, log_file, indent=4)
    print(f"Logs saved to {log_file_path}")


# 主程序
def main():
    global is_running
    # 启动键盘和鼠标事件监听
    with KeyboardListener(on_press=on_key_press) as keyboard_listener, \
            MouseListener(on_click=on_mouse_click, on_move=on_mouse_move) as mouse_listener:

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
