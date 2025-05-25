import json
import logging
import os
import time
from datetime import datetime
from difflib import SequenceMatcher
from typing import Literal

import cv2
import pytesseract
import keyboard
import numpy as np
import pandas as pd
import pyautogui
import pygetwindow as gw
from PIL import Image
from pyautogui import ImageNotFoundException


pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'

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

# 加载配置文件
ITEM_CONFIG = load_config(ITEM_CONFIG_FILE)
SYS_CONFIG = load_config(SYS_CONFIG_FILE)

# 缩放
WINDOW_RESIZE = SYS_CONFIG["windows_resize"]
# 窗口设置为1080p
window = gw.getWindowsWithTitle('三角洲行动')[0]
window.resizeTo(WINDOW_RESIZE[0], WINDOW_RESIZE[1])
window.moveTo(0, 0)
REGION = (window.left, window.top, window.width, window.height)
SCREEN_WIDTH = WINDOW_RESIZE[0]
SCREEN_HEIGHT = WINDOW_RESIZE[1]

WINDOW_TYPE = "window"

# 创建地图中文映射
MAP_NAME_CH = SYS_CONFIG["name_cn_mapping"]

# 位置映射坐标
POSITION_MAP = SYS_CONFIG["position_mapping"]

# 购买按钮位置
BUY_BUTTON_POSITION = SYS_CONFIG["buy_button_position"]

# 购买数量映射
ONE_TIME_BUY_NUM_MAPPING = SYS_CONFIG["one_time_buy_num_mapping"]

# 菜单按钮图片路径
MENU_BUTTON_IMG_PATH_MAPPING = SYS_CONFIG["menu_button_img_path_mapping"]


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


def log_to_excel(
    item_name: str, buyed_name: str, buyed_num: int, price: int | None
) -> None:
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


def take_screenshot(region: tuple[int, int, int, int], scale_percent: int = 400) -> np.ndarray:
    """截取指定区域的截图并预处理"""
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
    scale_percent = 175
    width = int(denoised.shape[1] * scale_percent / 100)
    height = int(denoised.shape[0] * scale_percent / 100)
    resized = cv2.resize(denoised, (width, height), interpolation=cv2.INTER_CUBIC)

    # 保存调试图像
    cv2.imwrite("./img/name.png", resized)
    return resized


def getItemPrice() -> int | None:
    """获取当前物品价格"""
    item_price_region = SYS_CONFIG["item_price_region"][WINDOW_TYPE]
    region_left = int(SCREEN_WIDTH * item_price_region["left"])
    region_top = int(SCREEN_HEIGHT * item_price_region["top"])
    region_width = int(SCREEN_WIDTH * item_price_region["width"])
    region_height = int(SCREEN_HEIGHT * item_price_region["height"])

    region = (region_left, region_top, region_width, region_height)

    screenshot = take_screenshot(region=region)

    # price_text = pytesseract.image_to_string(screenshot, lang='eng', config="--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789,")
    price_text = pytesseract.image_to_string(screenshot, lang='chi_sim+eng', config="--psm 10")

    if price_text:
        logger.info(f"提取的物品价格: {price_text}")
        return int(
            price_text.replace("o", "0")
            .replace("O", "0")
            .replace("l", "1")
            .replace("I", "1")
            .replace(",", "")
            .replace("，", "")
        )
    return None


def getItemName() -> str | None:
    """获取当前物品名称"""
    item_name_region = SYS_CONFIG["item_name_region"][WINDOW_TYPE]
    region_left = int(SCREEN_WIDTH * item_name_region["left"])
    region_top = int(SCREEN_HEIGHT * item_name_region["top"])
    region_width = int(SCREEN_WIDTH * item_name_region["width"])
    region_height = int(SCREEN_HEIGHT * item_name_region["height"])
    region = (region_left, region_top, region_width, region_height)

    screenshot = take_screenshot(region=region)

    name = pytesseract.image_to_string(screenshot, lang='chi_sim+eng', config="--psm 10")

    if name:
        logger.info(f"提取的物品名称: {name}")
    return name


def clicked_delay(delay: float = 0.1) -> None:
    """点击后延迟0.1秒"""
    pyautogui.click()
    time.sleep(delay)


def press_esc_delay(delay: float = 0.1) -> None:
    """按esc键"""
    pyautogui.press("esc")
    time.sleep(delay)


def locate_center_on_screen(img_path: str, confidence: float = 0.95, min_confidence: float = 0.8) -> pyautogui.Point | None:
    """查找图片中心坐标, 适配2k下的截图在不同分辨率下的查找

    Args:
        img_path: 图片路径
        confidence (float): 匹配度
        min_confidence (float): 最低匹配度

    Returns:
        pyautogui.Point | None: 找到则返回中心坐标点，否则返回None
    """
    original_image = Image.open(img_path)

    while confidence >= min_confidence:
        try:
            center = pyautogui.locateCenterOnScreen(
                original_image, confidence=confidence, region=REGION
            )
            if center is not None:
                # logger.info(f"在confidence={confidence:.2f}时找到图像{img_path}")
                return center
            
        except pyautogui.ImageNotFoundException:
            pass
        confidence -= 0.01

    raise ImageNotFoundException(
        f"未能找到图片 {img_path}，已尝试最低匹配度 {min_confidence}"
    )


def find_image_by_scroll(
    img_path: str,
    scroll_direction: int = -100,
    timeout: int = 10,
    confidence: float = 0.95,
    min_confidence: float = 0.8,
) -> pyautogui.Point | None:
    """
    通过滚动查找图片，找不到时尝试降低匹配度

    Args:
        img_path (str): 图片路径
        scroll_direction (int): 滚动方向和幅度，正数向上滚动，负数向下滚动
        timeout (int): 超时时间（秒）
        confidence (float): 匹配度
        min_confidence (float): 最低匹配度
    Returns:
        pyautogui.Point | None: 找到的图片中心坐标，未找到则返回None
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            center = locate_center_on_screen(img_path, confidence=confidence, min_confidence=min_confidence)
            return center
        except ImageNotFoundException:
            # 尝试滚动
            pyautogui.scroll(scroll_direction)
            time.sleep(0.1)
    return None


def move_to_click_found_image(
    img_path: str,
    scroll_direction: int = -100,
    timeout: int = 10,
    confidence: float = 0.95,
    min_confidence: float = 0.8,
) -> bool:
    """
    查找图片并点击，找不到时尝试滚动查找

    Args:
        img_path (str): 图片路径
        scroll_direction (int): 滚动方向和幅度，正数向上滚动，负数向下滚动
        timeout (int): 超时时间（秒）
        confidence (float): 匹配度
        min_confidence (float): 最低匹配度
    Returns:
        bool: 是否成功找到并点击图片
    """
    result = find_image_by_scroll(
        img_path=img_path,
        scroll_direction=scroll_direction,
        timeout=timeout,
        confidence=confidence,
        min_confidence=min_confidence,
    )

    if result:
        center = result
        pyautogui.moveTo(center)
        clicked_delay()
        return True
    return False


def check_img_in_screen(check_img: str, confidence: float = 0.95, min_confidence: float = 0.8) -> bool:
    """检查图片是否在屏幕上"""
    try:
        locate_center_on_screen(check_img, confidence=confidence, min_confidence=min_confidence)
        return True
    except ImageNotFoundException:
        return False


def check_window_type() -> str:
    """检查当前窗口类型"""
    if check_img_in_screen("img/sanjiaozhou.png"):
        return "window"
    return "borderless_window"


def move_into_market() -> None:
    """进入交易行"""
    move_to_click_img(img_path=MENU_BUTTON_IMG_PATH_MAPPING["jiaoyihang"], min_confidence=0.75)

    # 进入交易行后，确定当前锚点在购买，而不是出售或交易记录
    move_to_click_img(MENU_BUTTON_IMG_PATH_MAPPING["buy_menu"])


def move_to_left_menu() -> None:
    """移动鼠标到左侧菜单"""
    pyautogui.moveTo(SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.5)
    time.sleep(0.1)


def move_to_click_img(img_path: str, confidence: float = 0.95, min_confidence: float = 0.8) -> None:
    """移动鼠标到图片中心点击"""
    center = locate_center_on_screen(img_path, confidence=confidence, min_confidence=min_confidence)
    pyautogui.moveTo(center)
    clicked_delay()

def ensure_menu_expanded(menu_name: str) -> str:
    """
    确保左侧下拉菜单已展开，未展开则点击菜单展开

    Args:
        menu_name (str): 菜单名称,如钥匙，弹药

    Returns:
        str: 找到的菜单展开锚点的位置，'top' 或 'bottom'
    """
    move_to_left_menu()

    if menu_name == "yaoshi":
        scroll_direction = -200
        sub_menu_path = "img/key_card/ling_hao_da_ba.png"
    else:
        scroll_direction = 200
        sub_menu_path = "img/bullet/.50 AE.png"

    if check_img_in_screen(MENU_BUTTON_IMG_PATH_MAPPING[menu_name], min_confidence=0.75):
        if check_img_in_screen(sub_menu_path):
            move_to_click_img(MENU_BUTTON_IMG_PATH_MAPPING[menu_name], min_confidence=0.75)
    else:
        move_to_click_found_image(
            MENU_BUTTON_IMG_PATH_MAPPING[menu_name],
            scroll_direction=scroll_direction,
            min_confidence=0.75
        )

    move_to_click_img(MENU_BUTTON_IMG_PATH_MAPPING[menu_name], min_confidence=0.75)



def buy_item(item_info: dict, item_type: Literal["key_card", "bullet"]) -> bool:
    """单个物品的购买处理流程

    处理单个物品的购买逻辑，包括价格判断、相似度检查、购买操作等。

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
    time.sleep(0.2)

    # 获取物品信息
    try:
        item_name = getItemName().strip()
        current_price = getItemPrice()
        if current_price is None:
            logger.warning("无法获取有效价格，跳过当前物品")
            press_esc_delay()
            return False
    except Exception as e:
        logger.error(f"获取物品信息失败: {str(e)}")
        press_esc_delay()
        return False

    # 计算价格信息
    ideal_price = item_info.get("ideal_price")
    max_premium_percent = (
        int(SYS_CONFIG.get("max_premium_percent", "10%").replace("%", "")) / 100
    )  # 允许最高溢价
    max_price = ideal_price * (1 + max_premium_percent)
    premium = (current_price / ideal_price) - 1  # * 100

    # 检查物品名称相似度，去掉空格和引号提高匹配度，ocr可能识别不出空格和引号
    check_item_name = item_info.get("name")
    similarity = SequenceMatcher(
        None,
        item_name.replace("'", "").replace('"', ""),
        check_item_name.replace("'", "").replace('"', ""),
    ).ratio()

    logger.info(
        f"当前物品: {item_name}  |  需要购买的物品: {check_item_name}  |  相似度: {similarity:.2%}"
    )

    if similarity < 0.8:
        logger.info("需要购买的物品与点击的物品相似度不足 80%，已返回上一层")
        press_esc_delay()
        return False

    # 输出价格信息
    logger.info(
        f"理想价格: {ideal_price} | 当前价格: {current_price} ，溢价{(premium * 100):.2f}% | 最高溢价百分比：{max_premium_percent * 100}% , 最高溢价：{max_price:.2f}"
    )

    # 判断价格是否满足购买条件
    if current_price < ideal_price or premium < 0 or premium <= max_premium_percent:
        # 默认购买数量和乘数
        buy_num = 1

        # 获取购买数量设置
        one_time_setting = item_info.get("one_time_buy_num", "low")

        # 根据物品类型和设置获取购买数量
        buy_num = ONE_TIME_BUY_NUM_MAPPING[item_type][one_time_setting]

        # 移动到对应按钮
        pyautogui.moveTo(
            SCREEN_WIDTH * buy_button_position[WINDOW_TYPE][one_time_setting][0],
            SCREEN_HEIGHT * buy_button_position[WINDOW_TYPE][one_time_setting][1],
        )

        clicked_delay()

        # 点击购买按钮
        pyautogui.moveTo(
            SCREEN_WIDTH * buy_button_position[WINDOW_TYPE]["buy"][0],
            SCREEN_HEIGHT * buy_button_position[WINDOW_TYPE]["buy"][1],
        )
        clicked_delay()
        time.sleep(0.1)

        # 检查是否购买失败
        if check_img_in_screen(MENU_BUTTON_IMG_PATH_MAPPING["buy_failed"]):
            logger.info(">> 购买失败，最低价格已售罄，重新刷新价格 <<\n\n")
            press_esc_delay()
            return False
        else:
            # 购买成功
            logger.info(
                f"[+]已自动购买{item_name},价格为：{current_price},溢价：{premium:.2f}%"
            )
            item_info["buyed_times"] = item_info.get("buyed_times", 0) + 1
            logger.info(
                f"已购买次数: {item_info.get('buyed_times', 0)}/{buy_times_limit}\n"
            )
            log_to_excel(check_item_name, item_name, buy_num, current_price)
            press_esc_delay()
            return True
    else:
        logger.info(">> 价格过高，重新刷新价格 <<\n")
        press_esc_delay()
        return False


def process_category(
    item_info: dict,
    item_type: Literal["key_card", "bullet"],
    menu_name: Literal["yaoshi", "danyao"],
) -> bool:
    """物品类别批量购买流程

    处理整个类别物品的批量购买，包括菜单导航、循环遍历物品列表、购买尝试等。

    Args:
        item_info: 需要购买的物品字典 如'key_card'或'bullet'
        item_type: 类别名称，如'房卡'或'弹药'
        menu_name: 菜单名称，如'yaoshi'或'danyao'

    Returns:
        bool: 处理完成
    """
    global IS_RUNNING

    max_time_per = SYS_CONFIG.get("max_time_per", 120)  # 每种物品最多购买~秒

    # 确保菜单展开
    ensure_menu_expanded(menu_name)

    category_name = "房卡" if item_type == "key_card" else "弹药"

    logger.info(
        f"<--------------------------------开始购买{category_name}-------------------------------->"
    )

    for type_name, items in item_info.items():
        if not IS_RUNNING:
            break

        if item_type == "key_card":
            logger.info(f"当前地图: {MAP_NAME_CH[type_name]}")
        else:
            logger.info(f"当前子弹类型: {type_name}")

        for item in items:
            if not IS_RUNNING:
                break

            if item_type == "key_card":
                logger.info(f"当前购买房卡: {item['name']}")
            else:
                logger.info(f"当前购买子弹: {item['name']}")

            # 使用滚动查找函数查找物品类型
            move_to_click_found_image(
                f"img/{item_type}/{type_name}.png",
                scroll_direction=-200,
            )

            start_time = time.time()

            # 循环购买当前物品直到达到购买上限或超时
            while (
                item.get("buyed_times", 0) < item.get("buy_times_limit", 2)
                and IS_RUNNING
                and time.time() - start_time < max_time_per
            ):
                buy_item(item, item_type)

            if time.time() - start_time >= max_time_per:
                if item_type == "key_card":
                    logger.warning(f"{item['name']} 尝试购买超时，移至下一张卡\n\n")
                else:
                    logger.warning(f"{item['name']} 尝试购买超时，移至下一个子弹\n\n")
            else:
                logger.info(
                    f"{item['name']} 已完成购买，当前购买次数: {item.get('buyed_times', 0)}/{item.get('buy_times_limit', 2)}"
                )

        if item_type == "key_card":
            logger.info(f"地图 {MAP_NAME_CH[type_name]} 的所有卡片购买完成")
        else:
            logger.info(f"{type_name} 的所有子弹购买完成")

        move_to_left_menu()

    move_to_click_found_image(
        MENU_BUTTON_IMG_PATH_MAPPING[menu_name],
        scroll_direction=200,
        min_confidence=0.75
    )

    logger.info(
        f"<--------------------------------购买{category_name}完成-------------------------------->"
    )

    return True


def buy_key_card(key_cards_to_buy: dict) -> bool:
    """钥匙房卡购买流程"""
    return process_category(key_cards_to_buy, "key_card", "yaoshi")


def buy_bullet(bullets_to_buy: dict) -> bool:
    """弹药购买流程"""
    return process_category(bullets_to_buy, "bullet", "danyao")


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
                    # 获取购买数量设置
                    one_time_setting = card.get("one_time_buy_num", "low")
                    # 根据物品类型和设置获取购买数量
                    buy_num = ONE_TIME_BUY_NUM_MAPPING["key_card"][one_time_setting]
                    logger.info(
                        f"     {card['name']} * {int(card['buy_times_limit']) * buy_num}"
                    )
            logger.info("")

        if bullets_to_buy:
            logger.info("--------------弹药------------------")
            for type, bullets in bullets_to_buy.items():
                logger.info(f"-----弹药口径: {type}-----")
                for bullet in bullets:
                    # 获取购买数量设置
                    one_time_setting = bullet.get("one_time_buy_num", "low")
                    # 根据物品类型和设置获取购买数量
                    buy_num = ONE_TIME_BUY_NUM_MAPPING["bullet"][one_time_setting]

                    logger.info(
                        f"     {bullet['name']} * {int(bullet['buy_times_limit']) * buy_num}"
                    )
            logger.info("")

    return key_cards_to_buy, bullets_to_buy


def main():
    global IS_RUNNING, IS_PAUSED, WINDOW_TYPE

    WINDOW_TYPE = check_window_type()

    if not ITEM_CONFIG or not SYS_CONFIG:
        logger.info("无法加载配置文件，程序退出")
        return

    key_cards_to_buy, bullets_to_buy = collect_items_to_buy()

    if not key_cards_to_buy and not bullets_to_buy:
        logger.info("没有需要购买的物品，程序退出")
        return

    logger.info("程序启动，进入交易行")

    register_hotkeys()

    logger.info("按 F8 开始循环，按 F9 停止循环")

    while True:
        if IS_RUNNING and not IS_PAUSED:
            move_into_market()

            # 处理钥匙房卡购买
            if key_cards_to_buy:
                buy_key_card(key_cards_to_buy)

            # 处理弹药购买
            if bullets_to_buy:
                buy_bullet(bullets_to_buy)

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
