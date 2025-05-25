import pyautogui
import cv2
import numpy as np
import easyocr

# 配置屏幕尺寸
screen_width, screen_height = 1920, 1080

def take_screenshot(region):
    # 1. 截取屏幕
    screenshot = pyautogui.screenshot(region=region)
    
    # 2. 转换为OpenCV格式
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
    # 3. 转为灰度图
    gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

    # 4. 去噪
    denoised = cv2.fastNlMeansDenoising(
        gray, 
        h=15,
        templateWindowSize=7,
        searchWindowSize=21
    )
    scale_percent = 200  # 放大200%
    width = int(denoised.shape[1] * scale_percent / 100)
    height = int(denoised.shape[0] * scale_percent / 100)
    resized = cv2.resize(denoised, (width, height), interpolation=cv2.INTER_CUBIC)
    cv2.imwrite("./img/name.png", resized)
    return resized



def ocr_image(image: np.ndarray) -> list[str]:
    """
    """
    reader = easyocr.Reader(['en'])  # 英文识别
    result = reader.readtext(image, detail=0)  # 仅返回文本
    print(result)
    return result

if __name__ == "__main__":
    # 识别屏幕指定区域
    region_left = int(screen_width * 0.758)
    region_top = int(screen_height * 0.165)
    region_width = int(screen_width * 0.17)
    region_height = int(screen_height * 0.035)
    region = (region_left, region_top, region_width, region_height)
    # pyautogui.moveTo(region_left, region_top)
    # pyautogui.moveTo(int(screen_width * 0.154), int(screen_height * 0.154))
    screenshot = take_screenshot(region=region)
    print("屏幕截图识别结果：")
    ocr_image(screenshot)