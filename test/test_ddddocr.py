import pyautogui
import cv2
import numpy as np
import ddddocr
from PIL import Image
import io

# 配置屏幕尺寸
screen_width, screen_height = pyautogui.size()

def take_screenshot(region, is_chinese=False):
    # 1. 截取屏幕
    screenshot = pyautogui.screenshot(region=region)

    # 2. 转换为 OpenCV 格式
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # 3. 转为灰度图
    gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
    
    # 4. 使用锐化滤镜突出边缘
    kernel = np.array([[-1,-1,-1], 
                       [-1, 9,-1],
                       [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, kernel)
    
    # 5. 增强对比度
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)
    
    # 6. 二值化
    _, binary = cv2.threshold(enhanced, 127, 255, cv2.THRESH_BINARY)
    
    # 7. 形态学处理（可选）
    # 先腐蚀后膨胀，有助于去除小噪点并保持字符形状
    kernel = np.ones((2, 2), np.uint8)
    eroded = cv2.erode(binary, kernel, iterations=1)
    processed = cv2.dilate(eroded, kernel, iterations=1)
    
    # 8. 适当放大
    scale_percent = 400
    width = int(processed.shape[1] * scale_percent / 100)
    height = int(processed.shape[0] * scale_percent / 100)
    resized = cv2.resize(processed, (width, height), interpolation=cv2.INTER_CUBIC)

    # 保存调试图像
    cv2.imwrite("./img/name.png", resized)
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
    region_width = int(screen_width * 0.08)
    region_height = int(screen_height * 0.04)
    region_left = int(screen_width * 0.154)
    region_top = int(screen_height * 0.154)
    # region_width = int(screen_width * 0.17)
    # region_height = int(screen_height * 0.035)
    # region_left = int(screen_width * 0.7689)
    # region_top = int(screen_height * 0.1445)
    region = (region_left, region_top, region_width, region_height)
    screenshot = take_screenshot(region=region, is_chinese=False)
    print("屏幕截图识别结果：")
    ocr_image(screenshot)