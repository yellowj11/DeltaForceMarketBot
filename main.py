import json
import pyautogui
import cv2
import numpy as np
import time
import pandas as pd
from datetime import datetime
import logging
import os
import keyboard
from difflib import SequenceMatcher
from pyautogui import ImageNotFoundException
import ddddocr
from PIL import Image
import io


# 配置日志
if not os.path.exists("log"):
    os.makedirs("log")
log_timestamp = datetime.now().strftime("%Y%m%d_%H-%M-%S")
log_file = f"log/log_{log_timestamp}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger()


# 配置部分
ITEM_CONFIG_FILE = "config/buy_items_info.json"
SYS_CONFIG_FILE = "config/sys_info.json"
LOG_FILE = "log/price_log.xlsx"


def load_config(file_path: str):
    """加载配置文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            items_config = json.load(f)
            return items_config
    except FileNotFoundError:
        print(f"[错误] 配置文件 {file_path} 不存在")
        return {}
    except json.JSONDecodeError:
        print(f"[错误] 配置文件 {file_path} 格式错误")
        return {}
    except Exception as e:
        print(f"[错误] 读取配置时发生未知错误: {str(e)}")
        return {}


# 全局变量
IS_RUNNING = False
IS_PAUSED = False
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# OCR识别
OCR = ddddocr.DdddOcr(show_ad=False)
OCR_FOR_NUM = ddddocr.DdddOcr(show_ad=False)
OCR_FOR_NUM.set_ranges(0)

# 加载配置文件
ITEM_CONFIG = load_config(ITEM_CONFIG_FILE)
SYS_CONFIG = load_config(SYS_CONFIG_FILE)

# 创建地图中文映射
MAP_NAME_CH = SYS_CONFIG["name_cn_mapping"]

# 位置映射坐标
POSITION_MAP = SYS_CONFIG["position_mapping"]

# 购买按钮位置
BUY_BUTTON_POSITION = SYS_CONFIG["buy_buttom_position"]

if not os.path.exists(LOG_FILE):
    df = pd.DataFrame(
        columns=["购买时间", "名称", "购买物品名称", "购买数量", "购买单价"]
    )
    df.to_excel(LOG_FILE, index=False)
else:
    # 文件已存在，插入一行空数据作为分隔
    try:
        existing_data = pd.read_excel(LOG_FILE)

        empty_row = pd.DataFrame(
            {
                "购买时间": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "名称": ["----------------"],
                "购买物品名称": ["新一轮购买开始"],
                "购买数量": ["--------"],
                "购买单价": ["--------"],
            }
        )

        updated_data = pd.concat([existing_data, empty_row], ignore_index=True)
        updated_data.to_excel(LOG_FILE, index=False)
        logger.info("向记录文件添加了一条分隔记录")
    except Exception as e:
        logger.error(f"更新记录文件出错: {str(e)}，将创建新文件")
        df = pd.DataFrame(
            columns=["购买时间", "名称", "购买物品名称", "购买数量", "购买单价"]
        )
        df.to_excel(LOG_FILE, index=False)


def log_to_excel(item_name: str, buyed_name: str, buyed_num: int, price: int | None) -> None:
    """将 购买记录 记录到 Excel"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_data = pd.DataFrame(
        {
            "购买时间": [current_time],
            "名称": [item_name],
            "购买物品名称": [buyed_name],
            "购买数量": [buyed_num],
            "购买单价": [price if price is not None else "N/A"],
        }
    )
    try:
        existing_data = pd.read_excel(LOG_FILE)
        updated_data = pd.concat([existing_data, new_data], ignore_index=True)
        updated_data.to_excel(LOG_FILE, index=False)
    except Exception as e:
        logger.error(f"写入 Excel 失败: {str(e)}")
        new_data.to_excel(LOG_FILE, index=False)


def take_screenshot(region: tuple[int, int, int, int]) -> np.ndarray:
    """截取指定区域的截图并二值化"""
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
    scale_percent = 200
    width = int(processed.shape[1] * scale_percent / 100)
    height = int(processed.shape[0] * scale_percent / 100)
    resized = cv2.resize(processed, (width, height), interpolation=cv2.INTER_CUBIC)

    # 保存调试图像
    # cv2.imwrite("./img/name.png", resized)
    return resized


def perform_ocr(image: np.ndarray, debug_name: str | None = None, ocr_type: str = "normal") -> str | None:
    """对图像执行OCR识别"""
    image_pil = Image.fromarray(image)
    if debug_name:
        cv2.imwrite(f"./img/{debug_name}.png", image)

    try:
        img_byte_arr = io.BytesIO()
        image_pil.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()
        if ocr_type == "num":
            result = OCR_FOR_NUM.classification(img_bytes)
        else:
            result = OCR.classification(img_bytes)
        return result
    except Exception:
        logger.info(f"无法解析{debug_name if debug_name else '内容'}")
        return None


def getItemPrice() -> int | None:
    """获取当前物品价格"""
    region_width = int(SCREEN_WIDTH * 0.08)
    region_height = int(SCREEN_HEIGHT * 0.04)
    region_left = int(SCREEN_WIDTH * 0.154)
    region_top = int(SCREEN_HEIGHT * 0.154)
    region = (region_left, region_top, region_width, region_height)

    screenshot = take_screenshot(region=region)
    price_text = perform_ocr(screenshot, ocr_type="num")

    if price_text:
        logger.info(f"提取的物品价格: {price_text}")
        return int(
            price_text.replace("o", "0")
            .replace("O", "0")
            .replace("l", "1")
            .replace("I", "1")
        )
    return None


def getItemName() -> str | None:
    """获取当前物品名称"""
    # region_width = int(SCREEN_WIDTH * 0.18)
    # region_height = int(SCREEN_HEIGHT * 0.03)
    # region_left = int(SCREEN_WIDTH * 0.768)
    # region_top = int(SCREEN_HEIGHT * 0.145)
    region_width = int(SCREEN_WIDTH * 0.17)
    region_height = int(SCREEN_HEIGHT * 0.03)
    region_left = int(SCREEN_WIDTH * 0.7689)
    region_top = int(SCREEN_HEIGHT * 0.1445)
    region = (region_left, region_top, region_width, region_height)

    screenshot = take_screenshot(region=region)
    name = perform_ocr(screenshot)

    if name:
        logger.info(f"提取的物品名称: {name}")
    return name


def clicked_delay() -> None:
    """点击后延迟0.1秒"""
    pyautogui.click()
    time.sleep(0.1)


def find_image_by_scroll(
    img_path: str,
    scroll_direction: int = -100,
    timeout: int = 10,
    initial_confidence: float = 0.95,
    min_confidence: float = 0.9,
    confidence_step: float = 0.01,
) -> pyautogui.Point | None:
    """
    通过滚动查找图片，找不到时尝试降低匹配度

    Args:
        img_path (str): 图片路径
        scroll_direction (int): 滚动方向和幅度，正数向上滚动，负数向下滚动
        timeout (int): 超时时间（秒）
        initial_confidence (float): 初始匹配度
        min_confidence (float): 最低匹配度
        confidence_step (float): 每次降低的匹配度步长

    Returns:
        pyautogui.Point | None: 找到的图片中心坐标，未找到则返回None
    """
    start_time = time.time()
    current_confidence = initial_confidence

    while time.time() - start_time < timeout:
        try:
            # 尝试当前匹配度查找图片
            center = pyautogui.locateCenterOnScreen(
                img_path, confidence=current_confidence
            )
            # logger.info(f"找到图片 {img_path}，匹配度: {current_confidence:.2f}")
            return center
        except ImageNotFoundException:
            # 尝试滚动
            pyautogui.scroll(scroll_direction)
            time.sleep(0.1)

            # 每次滚动后检查是否需要降低匹配度
            if (
                time.time() - start_time > timeout / 2
                and current_confidence > min_confidence
            ):
                current_confidence -= confidence_step
                logger.info(
                    f"降低匹配度到 {current_confidence:.2f} 继续查找 {img_path}"
                )

    logger.warning(f"未能找到图片 {img_path}，已尝试最低匹配度 {min_confidence}")
    return None


def move_to_click_found_image(
    img_path: str,
    scroll_direction: int = -100,
    timeout: int = 10,
    initial_confidence: float = 0.95,
    min_confidence: float = 0.9,
) -> bool:
    """
    查找图片并点击，找不到时尝试滚动查找

    Args:
        img_path (str): 图片路径
        scroll_direction (int): 滚动方向和幅度，正数向上滚动，负数向下滚动
        timeout (int): 超时时间（秒）
        initial_confidence (float): 初始匹配度
        min_confidence (float): 最低匹配度

    Returns:
        bool: 是否成功找到并点击图片
    """
    result = find_image_by_scroll(
        img_path=img_path,
        scroll_direction=scroll_direction,
        timeout=timeout,
        initial_confidence=initial_confidence,
        min_confidence=min_confidence,
    )

    if result:
        center = result
        pyautogui.moveTo(center)
        clicked_delay()
        return True
    return False


def check_img_in_screen(check_img: str, confidence: float = 0.9) -> bool:
    """检查图片是否在屏幕上"""
    try:
        pyautogui.locateCenterOnScreen(check_img, confidence=confidence)
        return True
    except ImageNotFoundException:
        return False


def ensure_menu_expanded(menu_name: str) -> str:
    """
    确保左侧下拉菜单已展开，未展开则点击菜单展开

    查找图片的逻辑：
    1. 首先直接尝试查找
    2. 找不到则先向下滚动5次(每次-100)，每次滚动后检测图片
    3. 仍找不到则向上滚动10次(每次100)，每次滚动后检测图片
    4. 如果最终仍未找到，抛出异常

    Args:
        menu_name (str): 菜单名称,如钥匙，弹药

    Returns:
        str: 找到的菜单展开锚点的位置，'top' 或 'bottom'
    """
    map = {
        "danyao": {
            "check_img1": "img/bullet/5.54x39mm.png",
            "check_img2": "img/bullet/6.8x51mm.png",
            "click_img": "img/danyao.png",
        },
        "yaoshi": {
            "check_img1": "img/key_card/ling_hao_da_ba.png",
            "check_img2": "img/key_card/ba_ke_shi.png",
            "click_img": "img/yaoshi.png",
        },
    }
    move_to_left_menu()

    if check_img_in_screen(map[menu_name]["check_img1"]):
        return "top"
    if check_img_in_screen(map[menu_name]["check_img2"]):
        return "bottom"

    # 两个展开锚点都未找到，则移动到左侧菜单，准备滚动查找
    move_to_click_found_image(
        map[menu_name]["click_img"],
        scroll_direction=-100,
        timeout=10,
        initial_confidence=0.95,
        min_confidence=0.9,
    )
    return "top"


def move_into_market() -> None:
    """进入交易行"""
    move_to_click_img("img/jiaoyihang.png")

    # 进入交易行后，确定当前锚点在购买，而不是出售或交易记录
    move_to_click_img("img/buy_menu.png")


def move_to_left_menu() -> None:
    """移动鼠标到左侧菜单"""
    pyautogui.moveTo(SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.5)
    time.sleep(0.1)


def move_to_click_img(img_path: str, confidence: float = 0.9) -> None:
    """移动鼠标到图片中心"""
    try:
        center = pyautogui.locateCenterOnScreen(img_path, confidence=confidence)
        pyautogui.moveTo(center)
        clicked_delay()

    except ImageNotFoundException as e:
        logger.error(f"未找到图像: {img_path}，错误信息: {e}")
        raise e


def buy_item(item_info: dict, item_type: str) -> bool:
    """通用物品购买流程
    
    Args:
        item_info: 物品配置信息
        item_type: 物品类型，'key_card'或'bullet'
        
    Returns:
        bool: 是否成功购买
    """
    # 获取对应类型的按钮位置
    buy_button_position = BUY_BUTTON_POSITION[item_type]
    
    # 检查购买次数上限
    buy_times_limit = item_info.get("buy_times_limit", 2)
    buyed_times = item_info.get("buyed_times", 0)

    if buyed_times >= buy_times_limit:
        logger.info(f"{item_info['name']} 已购买 {buy_times_limit} 次，跳过当前物品")
        return False
    
    # 点击物品位置
    position = POSITION_MAP[item_info.get("position")]
    pyautogui.moveTo(position[0] * SCREEN_WIDTH, position[1] * SCREEN_HEIGHT)
    clicked_delay()
    time.sleep(0.3)
    
    # 获取物品信息
    try:
        item_name = getItemName().strip()
        current_price = getItemPrice()
        if current_price is None:
            logger.warning("无法获取有效价格，跳过当前物品")
            pyautogui.press("esc")
            time.sleep(0.1)
            return False
    except Exception as e:
        logger.error(f"获取物品信息失败: {str(e)}")
        pyautogui.press("esc")
        time.sleep(0.1)
        return False
    
    # 计算价格信息
    base_price = item_info.get("base_price", 0)
    ideal_price = item_info.get("ideal_price", base_price)
    max_premium_percent = 10  # 允许最高溢价10%
    # 如果理想价格低于基准价格太多，则计算溢价基于理想价格
    if ideal_price < base_price * 0.9:
        logger.info("当前设置理想价格低于基准价格90%，计算溢价基于理想价格")
        max_price = ideal_price * 1.1
        premium = ((current_price / ideal_price) - 1) * 100
    elif ideal_price > base_price * 1.1:
        logger.info("当前设置理想价格高于基准价格110%，计算溢价基于理想价格")
        max_price = ideal_price * 1.1
        premium = ((current_price / ideal_price) - 1) * 100
    else:
        logger.info("当前计算溢价基于基准价格")
        max_price = base_price * 1.1  # 最高溢价 10%
        premium = ((current_price / base_price) - 1) * 100
    
    # 检查物品名称相似度，去掉空格和引号提高匹配度，ocr可能识别不出空格和引号
    check_item_name = item_info.get("name")
    similarity = SequenceMatcher(None, item_name, check_item_name.replace("'", '').replace('"', '').replace(' ', '')).ratio()
    
    logger.info(
        f"当前物品: {item_name}  |  需要购买的物品: {check_item_name}  |  相似度: {similarity:.2%}"
    )
    
    if similarity < 0.8:
        logger.info("需要购买的物品与点击的物品相似度不足 80%，已返回上一层")
        pyautogui.press("esc")
        time.sleep(0.1)
        return False
    
    # 输出价格信息
    logger.info(
        f"基准价格: {base_price} , 理想价格: {ideal_price} | 当前价格: {current_price} ，溢价{premium:.2f}% | 最高溢价百分比：{max_premium_percent}% , 最高溢价：{max_price:.2f}"
    )
    
    # 判断价格是否满足购买条件
    if current_price < ideal_price or premium < 0 or premium <= max_premium_percent:
        # 默认购买数量和乘数
        buy_num = 1
        multiplier = 3 if item_type == "key_card" else 200
        
        # 如果设置了购买最大值
        if item_info.get("buy_max_one_time", "false").lower() == "true":
            logger.info("设置为购买最大值，点击 Max 按钮")
            pyautogui.moveTo(
                SCREEN_WIDTH * buy_button_position["max"][0],
                SCREEN_HEIGHT * buy_button_position["max"][1],
            )
            clicked_delay()
            buy_num = buy_num * multiplier
        
        # 点击购买按钮
        pyautogui.moveTo(
            SCREEN_WIDTH * buy_button_position["buy"][0],
            SCREEN_HEIGHT * buy_button_position["buy"][1],
        )
        clicked_delay()
        time.sleep(0.2)
        
        # 检查是否购买失败
        if check_img_in_screen("img/buy_fail.png", confidence=0.85):
            logger.info(">> 购买失败，最低价格已售罄，重新刷新价格 <<\n\n")
            pyautogui.press("esc")
            time.sleep(0.1)
            return False
        else:
            # 购买成功
            logger.info(
                f"[+]已自动购买{item_name},价格为：{current_price},溢价：{premium:.2f}%"
            )
            item_info["buyed_times"] = item_info.get("buyed_times", 0) + 1
            logger.info(f"已购买次数: {item_info.get('buyed_times', 0)}/{buy_times_limit}\n")
            log_to_excel(check_item_name, item_name, buy_num, current_price)
            pyautogui.press("esc")
            time.sleep(0.1)
            return True
    else:
        logger.info(">> 价格过高，重新刷新价格 <<\n")
        pyautogui.press("esc")
        time.sleep(0.1)
        return False


def buy_key_card(item_info: dict) -> bool:
    """钥匙房卡购买流程"""
    return buy_item(item_info, "key_card")


def buy_bullet(item_info: dict) -> bool:
    """弹药购买流程"""
    return buy_item(item_info, "bullet")


def start_loop():
    """开始循环"""
    global IS_RUNNING, IS_PAUSED
    IS_RUNNING = True
    IS_PAUSED = False
    print("循环已启动")


def stop_loop():
    """停止循环"""
    global IS_RUNNING, IS_PAUSED
    IS_RUNNING = False
    IS_PAUSED = False
    print("循环已停止")


def register_hotkeys(suppress: bool = True):
    # 使用 suppress=True 创建全局热键
    keyboard.add_hotkey("f8", start_loop, suppress=suppress)
    keyboard.add_hotkey("f9", stop_loop, suppress=suppress)


def collect_items_to_buy() -> tuple[dict, dict]:
    """收集需要购买的钥匙房卡和弹药

    Returns:
        tuple: (key_cards_to_buy, bullets_to_buy) 包含需要购买的所有物品
    """
    # 获取需要购买的钥匙房卡和弹药
    key_cards_config = ITEM_CONFIG.get("key_cards", {})
    bullets_config = ITEM_CONFIG.get("bullets", {})

    # 收集所有需要购买的钥匙房卡
    key_cards_to_buy = key_cards_config.copy()
    for cards in key_cards_to_buy.values():
        for i in range(len(cards) - 1, -1, -1):
            if cards[i].get("want_to_buy", "false").lower() != "true":
                del cards[i]

    key_cards_to_buy = {k: v for k, v in key_cards_to_buy.items() if v}

    # 收集所有需要购买的弹药
    bullets_to_buy = bullets_config.copy()
    for bullets in bullets_to_buy.values():
        for i in range(len(bullets) - 1, -1, -1):
            if bullets[i].get("want_to_buy", "false").lower() != "true":
                del bullets[i]

    bullets_to_buy = {k: v for k, v in bullets_to_buy.items() if v}

    # 打印需要购买的物品信息
    if key_cards_to_buy or bullets_to_buy:
        logger.info("需要购买的物品:")

        if key_cards_to_buy:
            logger.info("--------------房卡------------------")
            for map_name, cards in key_cards_to_buy.items():
                logger.info(f"-----地图: {MAP_NAME_CH[map_name]}-----")
                for card in cards:
                    logger.info(
                        f"     {card['name']} * {int(card['buy_times_limit']) * 3 if card['buy_max_one_time'] == 'true' else int(card['buy_times_limit'])}"
                    )
            logger.info("")

        if bullets_to_buy:
            logger.info("--------------弹药------------------")
            for type, bullets in bullets_to_buy.items():
                logger.info(f"-----弹药口径: {type}-----")
                for bullet in bullets:
                    logger.info(
                        f"     {bullet['name']} * {int(bullet['buy_times_limit']) * 200 if bullet['buy_max_one_time'] == 'true' else int(bullet['buy_times_limit'])}"
                    )
            logger.info("")

    return key_cards_to_buy, bullets_to_buy


def main():
    global IS_RUNNING, IS_PAUSED

    if not ITEM_CONFIG or not SYS_CONFIG:
        logger.info("无法加载配置文件，程序退出")
        return

    # 调用新方法收集需要购买的物品
    key_cards_to_buy, bullets_to_buy = collect_items_to_buy()

    if not key_cards_to_buy and not bullets_to_buy:
        logger.info("没有需要购买的物品，程序退出")
        return

    # 移动到交易行
    logger.info("程序启动，进入交易行")

    register_hotkeys()

    logger.info("按 F8 开始循环，按 F9 停止循环")

    while True:
        if IS_RUNNING and not IS_PAUSED:
            move_into_market()
            max_time_per = 120  # 每种物品最多尝试~秒
            # 处理钥匙房卡购买
            if key_cards_to_buy:
                scroll_direction = (
                    -100 if ensure_menu_expanded("yaoshi") == "top" else 100
                )

                logger.info(
                    "<--------------------------------开始购买房卡-------------------------------->"
                )
                for map_name, cards in key_cards_to_buy.items():
                    if not IS_RUNNING:
                        break

                    logger.info(f"当前地图: {MAP_NAME_CH[map_name]}")

                    for card in cards:
                        if not IS_RUNNING:
                            break
                        logger.info(f"当前购买房卡: {card['name']}")

                        # 使用滚动查找函数查找子弹类型
                        move_to_click_found_image(
                            f"img/key_card/{map_name}.png",
                            scroll_direction=scroll_direction,
                            timeout=15,
                            initial_confidence=0.95,
                            min_confidence=0.9,
                        )

                        start_time = time.time()

                        # 循环购买当前卡片直到达到购买上限或超时
                        while (
                            card.get("buyed_times", 0) < card.get("buy_times_limit", 2)
                            and IS_RUNNING
                            and time.time() - start_time < max_time_per
                        ):
                            buy_key_card(card)

                            time.sleep(0.1)

                        if time.time() - start_time >= max_time_per:
                            logger.warning(
                                f"{card['name']} 尝试购买超时，移至下一张卡\n\n"
                            )
                        else:
                            logger.info(
                                f"{card['name']} 已完成购买，当前购买次数: {card.get('buyed_times', 0)}/{card.get('buy_times_limit', 2)}"
                            )

                    logger.info(f"地图 {MAP_NAME_CH[map_name]} 的所有卡片购买完成")
                    move_to_left_menu()

                # 关闭钥匙交易界面，准备进入弹药购买
                move_to_click_found_image(
                    "img/yaoshi.png",
                    scroll_direction=100,
                    timeout=10,
                    initial_confidence=0.95,
                    min_confidence=0.9,
                )

                logger.info(
                    "<--------------------------------购买房卡完成-------------------------------->"
                )

            # 处理弹药购买
            if bullets_to_buy:
                scroll_direction = (
                    -100 if ensure_menu_expanded("danyao") == "top" else 100
                )

                logger.info(
                    "<--------------------------------开始购买弹药-------------------------------->"
                )
                for type, bullets in bullets_to_buy.items():
                    if not IS_RUNNING:
                        break

                    logger.info(f"当前子弹类型: {type}")

                    for bullet in bullets:
                        if not IS_RUNNING:
                            break
                        logger.info(f"当前购买子弹: {bullet['name']}")

                        # 使用滚动查找函数查找子弹类型
                        move_to_click_found_image(
                            f"img/bullet/{type}.png",
                            scroll_direction=scroll_direction,
                            timeout=15,
                            initial_confidence=0.95,
                            min_confidence=0.9,
                        )

                        start_time = time.time()

                        while (
                            bullet.get("buyed_times", 0)
                            < bullet.get("buy_times_limit", 2)
                            and IS_RUNNING
                            and time.time() - start_time < max_time_per
                        ):
                            buy_bullet(bullet)

                            time.sleep(0.1)

                        if time.time() - start_time >= max_time_per:
                            logger.warning(
                                f"{bullet['name']} 尝试购买超时，移至下一个子弹\n\n"
                            )
                        else:
                            logger.info(
                                f"{bullet['name']} 已完成购买，当前购买次数: {bullet.get('buyed_times', 0)}/{bullet.get('buy_times_limit', 2)}"
                            )

                    logger.info(f"{type} 的所有子弹购买完成")
                    move_to_left_menu()

                # 使用滚动查找函数查找弹药菜单，向上滚动回到原位置
                move_to_click_found_image(
                    "img/danyao.png",
                    scroll_direction=100,
                    timeout=10,
                    initial_confidence=0.95,
                    min_confidence=0.9,
                )

                logger.info(
                    "<--------------------------------购买弹药完成-------------------------------->"
                )

            # 检查是否所有物品都已达到购买上限
            key_cards_finished = (
                all(
                    card.get("buyed_times", 0) >= card.get("buy_times_limit", 2)
                    for cards in key_cards_to_buy.values()
                    for card in cards
                )
                if key_cards_to_buy
                else True
            )
            bullets_finished = (
                all(
                    bullet.get("buyed_times", 0) >= bullet.get("buy_times_limit", 2)
                    for bullets in bullets_to_buy.values()
                    for bullet in bullets
                )
                if bullets_to_buy
                else True
            )

            if key_cards_finished and bullets_finished:
                logger.info("所有物品均已达到购买上限，程序停止")
                IS_RUNNING = False

        elif IS_PAUSED:
            print("循环已暂停，等待手动恢复...")
            time.sleep(1)
        else:
            time.sleep(0.1)


if __name__ == "__main__":
    main()
