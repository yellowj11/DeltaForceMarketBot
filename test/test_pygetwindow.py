import pyautogui
import pygetwindow as gw

SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

window = gw.getWindowsWithTitle('三角洲行动')[0]
window.activate()

window.resizeTo(1920, 1080)
window.moveTo(0, 0)  # 可选：移动到屏幕左上角

region = (window.left, window.top, window.width, window.height)
print(f"窗口 region: {region}")