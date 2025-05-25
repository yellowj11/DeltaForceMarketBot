import pyautogui
import cv2
import numpy as np
import ddddocr
from PIL import Image
import io

# 配置屏幕尺寸
screen_width, screen_height = 1920, 1080

pyautogui.moveTo(0.7865 * screen_width, 0.72 * screen_height)
pyautogui.click()
