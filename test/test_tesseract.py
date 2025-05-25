import pyautogui
import cv2
import numpy as np
import ddddocr
from PIL import Image
import io
import pytesseract

# 配置屏幕尺寸
screen_width, screen_height = 1920, 1080
pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'


def take_screenshot(region, is_chinese=False):
    # 1. 截取屏幕
    # screenshot = pyautogui.screenshot(region=region)
    # screenshot_np = np.array(screenshot)
    # screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    # gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
    # denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
    # binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    # kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    # sharpened = cv2.filter2D(binary, -1, kernel)
    # scale_percent = 400
    # width = int(sharpened.shape[1] * scale_percent / 100)
    # height = int(sharpened.shape[0] * scale_percent / 100)
    # resized = cv2.resize(sharpened, (width, height), interpolation=cv2.INTER_CUBIC)
    # return resized
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

    # _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    # closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    scale_percent = 175
    width = int(denoised.shape[1] * scale_percent / 100)
    height = int(denoised.shape[0] * scale_percent / 100)
    resized = cv2.resize(denoised, (width, height), interpolation=cv2.INTER_CUBIC)
    # resized = cv2.resize(denoised, (width, height), interpolation=cv2.INTER_LINEAR)
    # resized = cv2.resize(denoised, (width, height), interpolation=cv2.INTER_AREA)
    
    cv2.imwrite("./img/name.png", resized)
    return resized



def ocr_image(image: np.ndarray) -> list[str]:
    """
    """
    text = pytesseract.image_to_string(screenshot, lang='chi_sim+eng', config="--psm 10")
    # text = pytesseract.image_to_string(screenshot, lang='eng', config="--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789")
    # text = pytesseract.image_to_string(screenshot, lang='eng', config='--psm 7 --oem 1 -c tessedit_char_whitelist=0123456789')
    print(f"文字: {text}")

    return text

if __name__ == "__main__":
    # 识别屏幕指定区域
    # region_left = int(screen_width * 0.758)
    # region_top = int(screen_height * 0.165)
    # region_width = int(screen_width * 0.17)
    # region_height = int(screen_height * 0.035)
    region_left = int(screen_width * 0.165)
    region_top = int(screen_height * 0.175)
    region_width = int(screen_width * 0.08)
    region_height = int(screen_height * 0.04)
    region = (region_left, region_top, region_width, region_height)
    screenshot = take_screenshot(region=region)
    print("屏幕截图识别结果：")
    ocr_image(screenshot)