# DFMarketBot

三角洲行动交易行自动补卡、补子弹，通过OCR+模拟鼠标点击实现自动购买。
# 甩锅（bushi）
脚本为闲暇时间写的娱乐脚本，还有很多问题需要修复，敬请见谅

## 功能预览
![功能演示](./img/preveiw.gif)

## 目录结构
```
DFMarketBot/
├── config/           # 配置文件目录
├── img/             # 图像资源目录
├── log/             # 日志文件目录
├── debug.py         # 调试工具（获取鼠标坐标）
├── main.py          # 主程序
├── pyproject.toml   # 项目依赖配置
├── README.md        # 说明文档
└── uv.lock          # 依赖锁定文件
```

## 快速开始

### 1. 环境准备
```bash
# 初始化虚拟环境
uv venv -p 3.12
uv sync
```

### 2. 安装 Tesseract(https://github.com/tesseract-ocr/tesseract)
1. 下载 [Tesseract](https://digi.bib.uni-mannheim.de/tesseract/)
2. 安装时选择需要的语言包：
   ![Tesseract安装](https://github.com/user-attachments/assets/53a513f1-34a1-45bf-a7f9-cfd5b5b74a07)
3. 修改配置：
   ```python
   # 在 main.py 中更新为您的安装路径
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### 3. 运行程序
```bash
python main.py
```
- F8: 开始自动购买
- F9: 停止自动购买

## 使用说明

### 运行环境要求
1. 游戏设置：
   - 使用窗口模式（已适配无窗口模式，但窗口模式识别率更高）
   - 脚本会自动将游戏窗口调整至 1920*1080
   ![窗口设置](https://github.com/user-attachments/assets/07674b92-a3c8-4c61-babc-9685e080a789)

2. 运行要求：
   - 交易行按钮需保持可见且可点击
   - 屏幕上不能有其他窗口遮挡
   ![界面示例](https://github.com/user-attachments/assets/19dd5e96-c969-4d5c-bed1-7497e79f87ca)

### 配置文件说明

#### 1. 购买物品配置 (config/buy_items_info.json)
```json
{
   "key_cards": {
    "ling_hao_da_ba": [               // 房卡、子弹类型，房卡用拼音，子弹直接照抄
      {
        "name": "变电站宿舍",          // 名称，需与游戏保持一致
        "ideal_price": 35700,         // 理想购买价格
        "position": "1-2",            // 物品在商城的位置，第一行第二列
        "want_to_buy": "true",        // 是否加入监控
        "one_time_buy_num": "low",    // 单次购买数量设置，low:1,medium:2,high:3
        "buy_times_limit": 1,         // 购买次数限制
        "buyed_times": 0              // 已购买次数
      }
    ]
  },
  "bullets": {
	  "9x19mm": [
	      {
	        "name": "9x19mm PSO",
	        "ideal_price": 30,
	        "position": "2-2",
	        "want_to_buy": "true",
	        "one_time_buy_num": "low",    // 单次购买数量设置，low:10,medium:100,high:200
	        "buy_times_limit": 5,
	        "buyed_times": 0
	      }
	    ]
  }
}
```
以下为坐标映射示例：
```json
"position_mapping": {
        "1-1": [0.3,0.2],
        "1-2": [0.6,0.2],
        "1-3": [0.8,0.2],
        "2-1": [0.3,0.35],
        "2-2": [0.6,0.35],
        "2-3": [0.8,0.35],
        "3-1": [0.3,0.5],
        "3-2": [0.6,0.5],
        "3-3": [0.8,0.5],
        "4-1": [0.3,0.65],
        "4-2": [0.6,0.65],
        "4-3": [0.8,0.65],
        "5-1": [0.3,0.8],
        "5-2": [0.6,0.8],
        "5-3": [0.8,0.8],
        "6-1": [0.3,0.9],
        "6-2": [0.6,0.9],
        "6-3": [0.8,0.9]
    },
```
![Image](https://github.com/user-attachments/assets/b826c458-548b-47ac-8293-b27cdb06872b)
2. sys_info.json示例如下：
```json
{
    "windows_resize": [1920, 1080],   // 游戏窗口分辨率，锁定1080p
    "position_mapping": {             // 坐标映射，非必要，请不要修改
        "1-1": [0.3,0.2],
        "1-2": [0.6,0.2],
        "1-3": [0.8,0.2],
        "2-1": [0.3,0.35],
        "2-2": [0.6,0.35],
        "2-3": [0.8,0.35],
        "3-1": [0.3,0.5],
        "3-2": [0.6,0.5],
        "3-3": [0.8,0.5],
        "4-1": [0.3,0.65],
        "4-2": [0.6,0.65],
        "4-3": [0.8,0.65],
        "5-1": [0.3,0.8],
        "5-2": [0.6,0.8],
        "5-3": [0.8,0.8],
        "6-1": [0.3,0.9],
        "6-2": [0.6,0.9],
        "6-3": [0.8,0.9]
    },
    "item_name_region":{             // 物品名称截图区域坐标映射
        "window":{                    // 窗口模式
            "left": 0.758,
            "top": 0.165,
            "width": 0.17,
            "height": 0.035
        },
        "borderless_window":{          // 无窗口模式
            "left": 0.768,
            "top": 0.145,
            "width": 0.17,
            "height": 0.035
        }
    },
    "item_price_region":{             // 物品价格截图区域坐标映射
        "window":{                    // 窗口模式
            "left": 0.165,
            "top": 0.175,
            "width": 0.08,
            "height": 0.04
        },
        "borderless_window":{          // 无窗口模式
            "left": 0.153,
            "top": 0.153,
            "width": 0.08,
            "height": 0.04
        }   
    },
    "buy_button_position":{             // 购买按钮位置坐标映射
        "key_card":{                    // 房卡
            "window":{                  // 窗口模式
                "high": [0.8948,0.772],
                "medium": [0.8365,0.772],
                "low": [0.7835,0.772],
                "buy": [0.85,0.85]
            },
            "borderless_window":{          // 无窗口模式
                "high": [0.91,0.772],
                "medium": [0.85,0.772],
                "low": [0.7935,0.772],
                "buy": [0.85,0.85]
            }
        },
        "bullet":{                      // 子弹
              "window":{                  // 窗口模式
                "high": [0.8948,0.72],
                "medium": [0.8365,0.72],
                "low": [0.7865,0.72],
                "buy": [0.85,0.8]
            },
            "borderless_window":{          // 无窗口模式
                "high": [0.91,0.72],
                "medium": [0.8493,0.72],
                "low": [0.7975,0.72],
                "buy": [0.85,0.8]
            }
        }
    },
    "one_time_buy_num_mapping" :{        // 单次购买数量映射
        "key_card": {                    // 房卡
            "low": 1, 
            "medium": 2,
            "high": 3
        },
        "bullet": {                      // 子弹
            "low": 10,
            "medium": 100,
            "high": 200
        }
    },
    "name_cn_mapping": {                // 房卡名称映射
        "chang_gong_xi_gu": "长工溪谷",
        "ling_hao_da_ba": "零号大坝",
        "hang_tian_ji_di": "航天基地",
        "ba_ke_shi": "巴克什"
    },
    "menu_button_img_path_mapping":{    // 菜单按钮图片路径映射
        "yaoshi": "img/yaoshi.png",
        "danyao": "img/danyao.png",
        "jiaoyihang": "img/jiaoyihang.png",
        "buy_menu": "img/buy_menu.png",
        "buy_succeed": "img/buy_succeed.png",
        "buy_failed": "img/buy_failed.png"
    },
    "max_time_per": 600,
    "max_premium_percent": "10%"
}
```

#### 2. 系统配置 (config/sys_info.json)
包含窗口分辨率、坐标映射、界面区域等系统配置，一般无需修改。

### 价格判断机制

#### 核心参数
- 理想价格：期望的最佳购买价格
- 当前价格：实时识别的市场价格
- 最高溢价：允许的最高溢价比例（默认10%）

#### 购买条件
满足以下任一条件时执行购买：
- 当前价格低于理想价格
- 当前价格溢价不超过10%

#### 购买记录
所有购买记录将保存到Excel文件：
![购买记录](https://github.com/user-attachments/assets/b4e0ada0-efde-443d-acae-dfe8c1d10cc8)

## 调试工具
运行调试工具获取鼠标坐标：
```bash
python debug.py
```

## 更新日志

### 2025-5-25
1. 修复物品购买数量映射问题
2. 优化1080p分辨率适配
3. 提升OCR识别准确度
4. OCR引擎更换为Tesseract

### 2025-5-22
1. 新增单次购买数量设置
2. 优化购买逻辑

### 2025-5-21
1. OCR引擎更换为ddddocr
2. 新增子弹购买功能
3. 支持坐标映射
4. 优化购买逻辑
5. 新增Excel记录功能

## 常见问题

1. 截图区域不正确
   > 确认屏幕分辨率为16:9

2. 点击无效/无法截图
   > 使用管理员权限运行CMD

3. 更新后依赖问题
   > 删除.venv文件夹重新初始化

## 免责声明

本脚本仅供学习研究使用，使用风险由用户自行承担：
- 使用第三方工具可能违反游戏平台条款
- 可能导致账号处罚
- 不保证脚本的稳定性和安全性

基于 [@sheldon1998](https://github.com/sheldon1998/DeltaForceKeyBot) 的项目修改开发。
