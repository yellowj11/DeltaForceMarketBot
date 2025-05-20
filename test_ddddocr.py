import pyautogui
import cv2
import numpy as np
import ddddocr
from PIL import Image
import io
import re

# 配置屏幕尺寸
screen_width, screen_height = pyautogui.size()

def take_screenshot(region):
    """截取指定区域的截图并进行预处理"""
# 1. 截取屏幕
    screenshot = pyautogui.screenshot(region=region)

    # 2. 转换为 OpenCV 格式
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # 3. 转为灰度图
    gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

    # 4. 增强对比度
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 5. 去噪
    denoised = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)

    # 6. 自适应二值化
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)

    # 7. 适当放大
    scale_percent = 200  # 放大 200%
    width = int(binary.shape[1] * scale_percent / 100)
    height = int(binary.shape[0] * scale_percent / 100)
    resized = cv2.resize(binary, (width, height), interpolation=cv2.INTER_CUBIC)

    # 保存调试图像
    cv2.imwrite("./img/price.png", resized)
    return resized

def ocr_image(image: np.ndarray) -> list[str]:
    """
    使用 ddddocr 识别图片中的文字
    Args:
        image (np.ndarray): 图片数组
    Returns:
        list[str]: 识别结果，仅包含文字列表
    """
    # 转换为 PIL 图像
    image_pil = Image.fromarray(image)

    # 初始化 ddddocr
    ocr = ddddocr.DdddOcr(show_ad=False)

    # 将 PIL 图像转换为字节流
    img_byte_arr = io.BytesIO()
    image_pil.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    # 识别文字
    text = ocr.classification(img_bytes)
    # 清理空格和校正双引号
    # cleaned_text = re.sub(r'\s+', ' ', text).replace("'", '"').replace("`", '"').replace(".", '"')
    # result = [cleaned_text] if cleaned_text else []
    
    # for t in result:
    print(f"文字: {text}")

    return text

if __name__ == "__main__":
    # 识别屏幕指定区域
    region_width = int(screen_width * 0.1)
    region_height = int(screen_height * 0.05)
    region_left = int(screen_width * 0.154)
    region_top = int(screen_height * 0.15)
    region = (region_left, region_top, region_width, region_height)
    screenshot = take_screenshot(region=region)
    print("屏幕截图识别结果：")
    ocr_image(screenshot)