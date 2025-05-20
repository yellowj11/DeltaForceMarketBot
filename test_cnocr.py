from cnocr import CnOcr
import pyautogui
import cv2
import numpy as np

# 配置日志
screen_width, screen_height = pyautogui.size()

def take_screenshot(region):
    """截取指定区域的截图并二值化"""
    # 1. 截取屏幕
    screenshot = pyautogui.screenshot(region=region)

    # 2. 转换为OpenCV格式
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # 3. 转为灰度图
    gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

    # 4. 去噪
    denoised = cv2.fastNlMeansDenoising(
        gray, h=15, templateWindowSize=7, searchWindowSize=21
    )
    scale_percent = 200  # 放大200%
    width = int(denoised.shape[1] * scale_percent / 100)
    height = int(denoised.shape[0] * scale_percent / 100)
    resized = cv2.resize(denoised, (width, height), interpolation=cv2.INTER_CUBIC)

    return resized

def ocr_image(image: np.ndarray | str) -> list[dict]:
    """
    识别图片中的文字
    Args:
        image (np.ndarray | str): 图片数组或图片路径
    Returns:
        list[dict]: 识别结果，每行为{'text': 文字, 'bbox': 坐标, 'score': 置信度}
    """
    ocr = CnOcr()
    result = ocr.ocr(image)
    for line in result:
        print(f"文字: {line['text']}, 坐标: {line.get('bbox', '无')}, 置信度: {line['score']}")
    return result

if __name__ == "__main__":
    # 识别屏幕指定区域
    region_width = int(screen_width * 0.1)
    region_height = int(screen_height * 0.03)
    region_left = int(screen_width * 0.768)
    region_top = int(screen_height * 0.145)
    region = (region_left, region_top, region_width, region_height)
    screenshot = take_screenshot(region=region)
    print("屏幕截图识别结果：")
    ocr_image(screenshot)