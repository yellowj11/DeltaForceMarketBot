# import pyautogui
# import pytesseract
# import cv2
# import pyautogui
# import pytesseract
# import numpy as np
# pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'

# def take_screenshot(region):
#     """截取指定区域的截图并二值化"""
#     # 1. 截取屏幕
#     screenshot = pyautogui.screenshot(region=region)
    
#     # 2. 转换为OpenCV格式
#     screenshot_np = np.array(screenshot)
#     screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
#     # 3. 转为灰度图
#     gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

#     # 4. 去噪
#     denoised = cv2.fastNlMeansDenoising(
#         gray, 
#         h=15,
#         templateWindowSize=7,
#         searchWindowSize=21
#     )
#     scale_percent = 200  # 放大200%
#     width = int(denoised.shape[1] * scale_percent / 100)
#     height = int(denoised.shape[0] * scale_percent / 100)
#     resized = cv2.resize(denoised, (width, height), interpolation=cv2.INTER_CUBIC)

#     return resized

# # 方法 1：全屏截图
# screen_width, screen_height = pyautogui.size()

# region_left = int(screen_width * 0.0664)
# region_top = int(screen_height * 0.0285)
# region_right = int(screen_width * 0.48)
# region_bottom = int(screen_height * 0.06)

# region = (region_left, region_top, region_right, region_bottom)
    
# screenshot = take_screenshot(region=region)
# # screenshot_full = pyautogui.screenshot()

# # 转换 PIL Image 为 OpenCV 格式 (RGB to BGR)
# # screenshot_cv = cv2.cvtColor(numpy.array(screenshot_full), cv2.COLOR_RGB2BGR)
# cv2.imwrite("./img/screenshot.png", screenshot)

# data_full = pytesseract.image_to_data(screenshot, lang='chi_sim', output_type=pytesseract.Output.DICT)
# region_left, region_top = 0, 0

# target_text = "交易行"
# for i in range(len(data_full['text'])):
#     if data_full['text'][i] == target_text and data_full['conf'][i] > 50:
#         left_img = data_full['left'][i]
#         top_img = data_full['top'][i]
#         width = data_full['width'][i]
#         height = data_full['height'][i]
#         screen_left = region_left + left_img
#         screen_top = region_top + top_img
#         center_x = screen_left + width / 2
#         center_y = screen_top + height / 2
#         pyautogui.moveTo(center_x, center_y)
#         print(f"全屏模式：鼠标已移动到 ({center_x}, {center_y})")
#         break
# else:
#     print("全屏模式：未找到目标文字")

import pyautogui

# 设置截图文件路径
image_file = 'img/yaoshi.png'

# 在屏幕上查找图像的中心坐标
# center = pyautogui.locateCenterOnScreen(image_file)
center = pyautogui.locateCenterOnScreen(image_file, confidence=0.9)

if center is not None:
    # 移动鼠标到找到的图像中心
    pyautogui.moveTo(center)
    pyautogui.click()
    print(f"鼠标已移动到位置: {center}")
else:
    print("未在屏幕上找到该图像")