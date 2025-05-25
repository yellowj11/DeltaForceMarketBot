import pyautogui
import cv2
import numpy as np
from PIL import Image
import time
region = (0, 0, 1920, 1080)


def preprocess_image_complex(image: Image.Image) -> Image.Image:
    """预处理图像以提高匹配精度"""
    screenshot_np = np.array(image)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(gray, -1, kernel)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)

    _, binary = cv2.threshold(enhanced, 127, 255, cv2.THRESH_BINARY)

    kernel = np.ones((2, 2), np.uint8)
    eroded = cv2.erode(binary, kernel, iterations=1)
    processed = cv2.dilate(eroded, kernel, iterations=1)

    scale_percent = 400
    width = int(processed.shape[1] * scale_percent / 100)
    height = int(processed.shape[0] * scale_percent / 100)
    resized = cv2.resize(processed, (width, height), interpolation=cv2.INTER_CUBIC)

    enhanced_pil = Image.fromarray(resized)
    return enhanced_pil


# image_file = "img/bullet/12.7x55mm.png"
image_files = [
    # "img/bullet/.357 Magnum.png",
    # "img/bullet/.45 ACP.png",
    # "img/bullet/.50 AE.png",
    # "img/bullet/12 Gauge.png",
    # "img/bullet/12.7x55mm.png",
    # "img/bullet/5.54x39mm.png",
    # "img/bullet/5.56x45mm.png",
    # "img/bullet/5.7x28mm.png",
    # "img/bullet/5.8x42mm.png",
    # "img/bullet/6.8x51mm.png",
    # "img/bullet/7.62x39mm.png",
    # "img/bullet/7.62x51mm.png",
    # "img/bullet/7.62x54mm.png",
    # "img/bullet/9x19mm.png",
    # "img/bullet/9x39mm.png",
    # "img/bullet/4.6x30mm.png",
    # "img/bullet/.300 BLK.png",
    "img/jiaoyihang.png",
    "img/buy_menu.png",
    "img/yaoshi.png",
    "img/danyao.png",
    # "img/search.png",
    # "img/sanjiaozhou.png",
    # "img/key_card/ling_hao_da_ba.png",
    # "img/key_card/hang_tian_ji_di.png",
    # "img/key_card/chang_gong_xi_gu.png",
    # "img/key_card/ba_ke_shi.png",
]

# current_resolution = pyautogui.size()  # 获取当前屏幕分辨率
# reference_resolution = (2560, 1440)  # 假设目标图像在2K下截取

# 计算缩放因子，考虑both宽度和高度
resize_factor = 1.1
# resize_factor = current_resolution[0] / reference_resolution[0]  # 宽度比例
for image_file in image_files:
    # 加载并预处理目标图像
    original_image = Image.open(image_file)
    # processed_image = preprocess_image_complex(original_image)

    # 调整图像大小
    resized_image = original_image.resize(
        (
            int(original_image.width * resize_factor),
            int(original_image.height * resize_factor),
        ),
        Image.Resampling.LANCZOS,
    )

    # resized_image.save(f"img/debug/{image_file[4:]}.png")

    # 在屏幕上查找图像的中心坐标，从高精度开始尝试
    confidence = 0.95
    center = None

    while confidence >= 0.75 and center is None:
        try:
            center = pyautogui.locateCenterOnScreen(
                original_image, confidence=confidence, region=region
            )
            if center is not None:
                print(f"在confidence={confidence:.2f}时找到图像{image_file}")
                break
        except pyautogui.ImageNotFoundException:
            pass
        confidence -= 0.01

    if center is not None:
        pyautogui.moveTo(center)
        pyautogui.click()
        time.sleep(0.1)
        print(f"鼠标已移动到位置: {center}")
    else:
        print("未在屏幕上找到该图像")
