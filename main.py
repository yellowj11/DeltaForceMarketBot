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



# 配置部分
CONFIG_FILE = "config/buy_items_info.json"
LOG_FILE = "log/price_log.xlsx"


# 配置日志
if not os.path.exists("log"):
    os.makedirs("log")
    
# 生成带时间戳的日志文件名
log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"log/log_{log_timestamp}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),  # 同时输出到控制台
    ],
)
logger = logging.getLogger()

# 全局变量
is_running = False
is_paused = False
screen_width, screen_height = pyautogui.size()

# 创建地图中文映射
MAP_NAME_CH = {
    "chang_gong_xi_gu": "长工溪谷",
    "ling_hao_da_ba": "零号大坝",
    "hang_tian_ji_di": "航天基地",
    "ba_ke_shi": "巴克什",
}

if not os.path.exists(LOG_FILE):
    df = pd.DataFrame(columns=["时间", "名称", "购买目标名称", "价格", "购买"])
    df.to_excel(LOG_FILE, index=False)


def find_image_by_scroll(img_path: str, scroll_direction: int = -100, timeout: int = 10, 
                         initial_confidence: float = 0.95, min_confidence: float = 0.9, 
                         confidence_step: float = 0.01) -> pyautogui.Point | None:
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
            center = pyautogui.locateCenterOnScreen(img_path, confidence=current_confidence)
            logger.info(f"找到图片 {img_path}，匹配度: {current_confidence:.2f}")
            return center
        except ImageNotFoundException:
            # 尝试滚动
            pyautogui.scroll(scroll_direction)
            time.sleep(0.1)
            
            # 每次滚动后检查是否需要降低匹配度
            if time.time() - start_time > timeout / 2 and current_confidence > min_confidence:
                current_confidence -= confidence_step
                logger.info(f"降低匹配度到 {current_confidence:.2f} 继续查找 {img_path}")
    
    logger.warning(f"未能找到图片 {img_path}，已尝试最低匹配度 {min_confidence}")
    return None


def move_to_click_found_image(img_path: str, scroll_direction: int = -100, timeout: int = 10, 
                             initial_confidence: float = 0.95, min_confidence: float = 0.9) -> bool:
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
        min_confidence=min_confidence
    )
    
    if result:
        center = result
        pyautogui.moveTo(center)
        pyautogui.click()
        time.sleep(0.1)
        return True
    return False


def load_items_config(file_path: str):
    """加载配置文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            items_config = json.load(f)
            return items_config
    except FileNotFoundError:
        print(f"[错误] 配置文件 {CONFIG_FILE} 不存在")
        return {}
    except json.JSONDecodeError:
        print(f"[错误] 配置文件 {CONFIG_FILE} 格式错误")
        return {}
    except Exception as e:
        print(f"[错误] 读取配置时发生未知错误: {str(e)}")
        return {}


def take_screenshot(region):
    """截取指定区域的截图并二值化"""
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
    denoised = cv2.medianBlur(enhanced, 3)

    # 6. 二值化
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 7. 适当放大
    scale_percent = 200  
    width = int(binary.shape[1] * scale_percent / 100)
    height = int(binary.shape[0] * scale_percent / 100)
    resized = cv2.resize(binary, (width, height), interpolation=cv2.INTER_CUBIC)

    return resized


def getItemPrice():
    """获取当前物品价格"""
    region_width = int(screen_width * 0.1)
    region_height = int(screen_height * 0.05)
    region_left = int(screen_width * 0.154)
    region_top = int(screen_height * 0.15)
    region = (region_left, region_top, region_width, region_height)

    screenshot = take_screenshot(region=region)
    # cv2.imwrite("./img/price.png", screenshot) # 保存图片到本地
    image_pil = Image.fromarray(screenshot)
    ocr = ddddocr.DdddOcr(show_ad=False)
    
    try:
        img_byte_arr = io.BytesIO()
        image_pil.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        price = ocr.classification(img_bytes)
        logger.info(f"提取的物品价格: {price}")
        return int(price.replace('o', '0').replace('O', '0').replace('l', '1'))
    except:
        logger.info("无法解析价格")
        return None


def getItemName():
    """获取当前物品名称"""
    region_width = int(screen_width * 0.18)  # 区域宽度
    region_height = int(screen_height * 0.03)  # 区域高度
    region_left = int(screen_width * 0.768)
    region_top = int(screen_height * 0.145)
    region = (region_left, region_top, region_width, region_height)

    screenshot = take_screenshot(region=region)
    # cv2.imwrite("./img/name.png", screenshot) # 保存图片到本地
    image_pil = Image.fromarray(screenshot)
    ocr = ddddocr.DdddOcr(show_ad=False)
    try:
        img_byte_arr = io.BytesIO()
        image_pil.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        price = ocr.classification(img_bytes)
        logger.info(f"提取的物品名称: {price}")
        return price
    except:
        logger.info("无法解析名称")
        return None

def ensure_menu_expanded(menu_name: str, scroll_direction: int | None = None) -> None:
    """
    确保左侧下拉菜单已展开，未展开则点击菜单展开

    Args:
        menu_name (str): 菜单名称,如钥匙，弹药
        scroll_direction (int | None): 滚动方向，如果为None则不滚动，有的菜单栏会因为其他展开导致不在屏幕中
    """
    map = {
        "danyao": {"check_img":"img/bullet/.357 Magnum.png","click_img":"img/danyao.png"},
        "yaoshi": {"check_img":"img/key_card/chang_gong_xi_gu.png","click_img":"img/yaoshi.png"},
    }
    try:
        # 检查是否已展开弹药下拉框
        pyautogui.locateCenterOnScreen(
            map[menu_name]["check_img"], confidence=0.9
        )
    except ImageNotFoundException:
        if scroll_direction:

            move_to_left_menu()
            move_to_click_found_image(
                        map[menu_name]["click_img"], 
                        scroll_direction=scroll_direction,
                        timeout=10,
                        initial_confidence=0.95,
                        min_confidence=0.9
                    )
        else:
            move_to_click_img(map[menu_name]["click_img"])

def move_to_left_menu():
    """移动鼠标到左侧菜单"""
    pyautogui.moveTo(screen_width * 0.1, screen_height * 0.5)
    time.sleep(0.1)

def move_to_click_img(img_path):
    """移动鼠标到图片中心"""
    try:
        center = pyautogui.locateCenterOnScreen(img_path, confidence=0.9)
        pyautogui.moveTo(center)
        pyautogui.click()
        time.sleep(0.1)

    except ImageNotFoundException as e:
        logger.error(f"未找到图像: {img_path}，错误信息: {e}")
        raise e


def log_to_excel(item_name, target_name, price, purchased):
    """将价格信息记录到 Excel"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_data = pd.DataFrame(
        {
            "时间": [current_time],
            "名称": [item_name],
            "购买目标名称": [target_name],
            "价格": [price if price is not None else "N/A"],
            "购买": ["是" if purchased else "否"],
        }
    )
    try:
        existing_data = pd.read_excel(LOG_FILE)
        updated_data = pd.concat([existing_data, new_data], ignore_index=True)
        updated_data.to_excel(LOG_FILE, index=False)
    except Exception as e:
        logger.error(f"写入 Excel 失败: {str(e)}")
        new_data.to_excel(LOG_FILE, index=False)


def buy_key_card(item_info, map_name) -> bool:
    """钥匙房卡购买流程"""

    # move_to_click_img(f"img/key_card/{map_name}.png")

    purchased = False

    buy_times_limit = item_info.get("buy_times_limit", 2)
    buyed_times = item_info.get("buyed_times", 0)

    if buyed_times >= buy_times_limit:
        logger.info(f"{item_info['name']} 已购买 {buy_times_limit} 次，跳过当前物品")
        return purchased

    position = item_info.get("position")
    pyautogui.moveTo(position[0] * screen_width, position[1] * screen_height)
    pyautogui.click()
    time.sleep(0.3)

    try:
        item_name = getItemName().strip()
        current_price = getItemPrice()
        if current_price is None:
            logger.warning("无法获取有效价格，跳过当前物品")
            # log_to_excel("key_card", item_name, item_info.get("name"), None, purchased)
            pyautogui.press("esc")
            time.sleep(0.1)
            return purchased
    except Exception as e:
        logger.error(f"获取物品信息失败: {str(e)}")
        # log_to_excel("key_card", "", item_info.get("name"), None, purchased)
        pyautogui.press("esc")
        time.sleep(0.1)
        return purchased

    base_price = item_info.get("base_price", 0)
    ideal_price = item_info.get("ideal_price", base_price)
    max_price = item_info.get("base_price") * 1.1  # 最高溢价 10%
    premium = ((current_price / base_price) - 1) * 100
    max_premium_percent = 10  # 允许最高溢价10%

    check_item_name = item_info.get("name")
    similarity = SequenceMatcher(None, item_name, check_item_name).ratio()

    if similarity < 0.8:
        logger.info("需要购买的卡与点击的卡相似度不足 80%，已返回上一层")
        # log_to_excel("key_card", item_name, check_item_name, current_price, purchased)
        pyautogui.press("esc")
        time.sleep(0.1)
        return purchased

    logger.info(
        f"基准价格: {base_price} | 理想价格: {ideal_price} | 当前价格: {current_price} ,溢价：{premium:.2f}% | 最高溢价{max_premium_percent}%：{max_price:.4f}"
    )

    if current_price < ideal_price or premium < 0 or premium <= max_premium_percent:
        if item_info.get("buy_max_one_time", "false").lower() == "true":
            logger.info("设置为购买最大值，点击 Max 按钮")
            pyautogui.moveTo(
                screen_width * 0.9104, screen_height * 0.7807
            )  # 点击 Max 按钮
            pyautogui.click()
            time.sleep(0.1)

        pyautogui.moveTo(screen_width * 0.825, screen_height * 0.852)
        pyautogui.click()  # 调试先把点击购买注释
        time.sleep(0.2)
        logger.info(
            f"[+]已自动购买{item_name},价格为：{current_price},溢价：{premium:.2f}%"
        )
        item_info["buyed_times"] = item_info.get("buyed_times", 0) + 1
        logger.info(f"已购买次数: {item_info['buyed_times']}/{buy_times_limit}")
        purchased = True
        pyautogui.press("esc")
        time.sleep(0.1)
    else:
        logger.info(">> 价格过高，重新刷新价格 <<\n")
        pyautogui.press("esc")
        time.sleep(0.1)

    # log_to_excel("key_card", item_name, check_item_name, current_price, purchased)
    return purchased


def buy_bullet(item_info, type) -> bool:
    """弹药购买流程"""

    # move_to_click_img(f"img/bullet/{type}.png")

    purchased = False

    buy_times_limit = item_info.get("buy_times_limit", 2)
    if item_info.get("buyed_times", 0) >= buy_times_limit:
        logger.info(f"{item_info['name']} 已购买 {buy_times_limit} 次，跳过当前物品")
        return purchased

    position = item_info.get("position")
    pyautogui.moveTo(position[0] * screen_width, position[1] * screen_height)
    pyautogui.click()
    time.sleep(0.3) # 给0.3s页面加载

    try:
        item_name = getItemName().strip()
        current_price = getItemPrice()
        if current_price is None:
            logger.warning("无法获取有效价格，跳过当前物品")
            # log_to_excel("key_card", item_name, item_info.get("name"), None, purchased)
            pyautogui.press("esc")
            time.sleep(0.1)
            return purchased
    except Exception as e:
        logger.error(f"获取物品信息失败: {str(e)}")
        # log_to_excel("key_card", "", item_info.get("name"), None, purchased)
        pyautogui.press("esc")
        time.sleep(0.1)
        return purchased

    base_price = item_info.get("base_price", 0)
    ideal_price = item_info.get("ideal_price", base_price)
    max_price = item_info.get("base_price") * 1.1  # 最高溢价 10%
    premium = ((current_price / base_price) - 1) * 100
    max_premium_percent = 10  # 允许最高溢价10%

    check_item_name = item_info.get("name")
    similarity = SequenceMatcher(None, item_name, check_item_name).ratio()
    logger.info(
        f"当前子弹: {item_name}  |  需要购买的子弹: {check_item_name}  |  相似度: {similarity:.2%}"
    )

    if similarity < 0.8:
        logger.info("需要购买的卡与点击的卡相似度不足 80%，已返回上一层")
        # log_to_excel("key_card", item_name, check_item_name, current_price, purchased)
        pyautogui.press("esc")
        time.sleep(0.1)
        return purchased

    logger.info(
        f"基准价格: {base_price} | 理想价格: {ideal_price} | 当前价格: {current_price} ，溢价{premium:.2f}% | 最高溢价{max_premium_percent}%：{max_price}"
    )
    logger.info(f"已购买次数: {item_info.get('buyed_times', 0)}/{buy_times_limit}")

    if current_price < ideal_price or premium < 0 or premium <= max_premium_percent:
        if item_info.get("buy_max_one_time", "false").lower() == "true":
            logger.info("设置为购买最大值，点击 Max 按钮")
            pyautogui.moveTo(
                screen_width * 0.909, screen_height * 0.722
            )  # 点击 Max 按钮
            pyautogui.click()
            # pyautogui.moveTo(
            #     screen_width * 0.8493, screen_height * 0.7204
            # )  # 点击 medium 按钮

            time.sleep(0.1)

        pyautogui.moveTo(screen_width * 0.855, screen_height * 0.797)
        pyautogui.click()
        logger.info(
            f"[+]已自动购买{item_name},价格为：{current_price},溢价：{premium:.2f}%"
        )
        item_info["buyed_times"] = item_info.get("buyed_times", 0) + 1
        purchased = True
        pyautogui.press("esc")
        time.sleep(0.1)
    else:
        logger.info(">> 价格过高，重新刷新价格 <<\n\n")
        pyautogui.press("esc")
        time.sleep(0.1)

    # log_to_excel("key_card", item_name, check_item_name, current_price, purchased)
    return purchased


def start_loop():
    """开始循环"""
    global is_running, is_paused
    is_running = True
    is_paused = False
    print("循环已启动")


def stop_loop():
    """停止循环"""
    global is_running, is_paused
    is_running = False
    is_paused = False
    print("循环已停止")


def register_hotkeys(suppress=True):
    # 使用 suppress=True 创建全局热键
    keyboard.add_hotkey("f8", start_loop, suppress=suppress)
    keyboard.add_hotkey("f9", stop_loop, suppress=suppress)


def main():
    # getItemName()
    # getItemPrice()
    global is_running, is_paused

    items_config = load_items_config(CONFIG_FILE)
    if not items_config:
        logger.info("无法加载配置文件，程序退出")
        return

    # 获取需要购买的钥匙房卡和弹药
    key_cards_config = items_config.get("key_cards", {})
    bullets_config = items_config.get("bullets", {})

    # 收集所有需要购买的钥匙房卡
    key_cards_to_buy = key_cards_config.copy()
    for cards in key_cards_to_buy.values():
        for i in range(len(cards) - 1, -1, -1):
            if cards[i].get("want_to_buy", "false").lower() != "true":
                # 删除不需要购买的
                del cards[i]

    key_cards_to_buy = {k: v for k, v in key_cards_to_buy.items() if v}

    # 收集所有需要购买的弹药
    bullets_to_buy = bullets_config.copy()
    for bullets in bullets_to_buy.values():
        for i in range(len(bullets) - 1, -1, -1):
            if bullets[i].get("want_to_buy", "false").lower() != "true":
                del bullets[i]

    bullets_to_buy = {k: v for k, v in bullets_to_buy.items() if v}

    if not key_cards_to_buy and not bullets_to_buy:
        logger.info("没有需要购买的物品，程序退出")
        return

    logger.info("需要购买的物品:")
    for map_name, cards in key_cards_to_buy.items():
        logger.info(f"-----地图: {MAP_NAME_CH[map_name]}-----")
        for card in cards:
            logger.info(f"   房卡:{card['name']}")

    for type, bullets in bullets_to_buy.items():
        logger.info(f"-----弹药口径: {type}-----")
        for bullet in bullets:
            logger.info(f"   弹药:{bullet['name']}")

    logger.info("")
    # 移动到交易行
    logger.info("程序启动，进入交易行")
    move_to_click_img("img/jiaoyihang.png")

    register_hotkeys()

    logger.info("按 F8 开始循环，按 F9 停止循环")

    while True:
        if is_running and not is_paused:
            max_time_per = 20 # 每种物品最多尝试~秒
            # 处理钥匙房卡购买
            if key_cards_to_buy:
                
                ensure_menu_expanded("yaoshi", -100)

                logger.info(
                    "<--------------------------------开始购买房卡-------------------------------->"
                )
                for map_name, cards in key_cards_to_buy.items():
                    if not is_running:
                        break

                    logger.info(f"当前地图: {MAP_NAME_CH[map_name]}")

                    for card in cards:
                        if not is_running:
                            break
                        logger.info(f"当前购买房卡: {card['name']}")

                        # 使用滚动查找函数查找子弹类型
                        move_to_click_found_image(
                            f"img/key_card/{map_name}.png", 
                            scroll_direction=-100,
                            timeout=15,
                            initial_confidence=0.95,
                            min_confidence=0.9
                        )

                        start_time = time.time()
                       
                        # 循环购买当前卡片直到达到购买上限或超时
                        while (
                            card.get("buyed_times", 0) < card.get("buy_times_limit", 2)
                            and is_running
                            and time.time() - start_time < max_time_per
                        ):
                            buy_key_card(card, map_name)

                            time.sleep(0.1)

                        if time.time() - start_time >= max_time_per:
                            logger.warning(f"{card['name']} 尝试购买超时，移至下一张卡\n\n")
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
                    min_confidence=0.9
                )
                
                logger.info(
                    "<--------------------------------购买房卡完成-------------------------------->"
                )

            # 处理弹药购买
            if bullets_to_buy:

                ensure_menu_expanded("danyao")

                logger.info(
                    "<--------------------------------开始购买弹药-------------------------------->"
                )
                for type, bullets in bullets_to_buy.items():
                    if not is_running:
                        break
                    
                    logger.info(f"当前子弹类型: {type}")

                    for bullet in bullets:
                        if not is_running:
                            break
                        logger.info(f"当前购买子弹: {bullet['name']}")

                        # 使用滚动查找函数查找子弹类型
                        move_to_click_found_image(
                            f"img/bullet/{type}.png", 
                            scroll_direction=-100,
                            timeout=15,
                            initial_confidence=0.95,
                            min_confidence=0.9
                        )
                                
                        start_time = time.time()

                        while (
                            bullet.get("buyed_times", 0) < bullet.get("buy_times_limit", 2)
                            and is_running
                            and time.time() - start_time < max_time_per
                        ):
                            buy_bullet(bullet, type)

                            time.sleep(0.1)

                        if time.time() - start_time >= max_time_per:
                            logger.warning(f"{bullet['name']} 尝试购买超时，移至下一个子弹\n\n")
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
                    min_confidence=0.9
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
                is_running = False

        elif is_paused:
            print("循环已暂停，等待手动恢复...")
            time.sleep(1)
        else:
            time.sleep(0.1)


if __name__ == "__main__":
    main()
