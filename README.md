# nonebot-plugin-vvquest

[![License](https://img.shields.io/github/license/webjoin111/nonebot-plugin-vvquest)](LICENSE)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![NoneBot Version](https://img.shields.io/badge/nonebot-2.0.0+-red.svg)
![Adapter](https://img.shields.io/badge/adapter-OneBot-green.svg)

通过API获取维维语录图片的NoneBot2插件

## 功能介绍

通过API获取维维语录图片，支持直接搜索和引用消息搜索，可配置返回图片数量和使用合并转发消息。

## 安装方式

### 使用 nb-cli 安装（推荐）

```bash
nb plugin install nonebot-plugin-vvquest
```

### 使用 pip 安装

```bash
pip install nonebot-plugin-vvquest
```

### 手动安装

1. 克隆本仓库

```bash
git clone https://github.com/webjoin111/nonebot-plugin-vvquest.git
```

2. 将`nonebot_plugin_vvquest`文件夹复制到你的插件目录下

3. 在`pyproject.toml`中添加插件

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_vvquest"]
```

## 配置项

在`.env`文件中添加以下配置：

```dotenv
# 最大返回图片数量限制 (1-50)
VVQUEST_MAX_NUM=10

# 是否使用合并转发消息
VVQUEST_USE_FORWARD=true

# 本地API完整地址（如 http://localhost:8000/search），留空使用默认在线API
VVQUEST_API_BASE=""

# API请求冷却时间（秒），防止频繁请求 (1-300)
VVQUEST_COOLDOWN=30
```

## 使用方法

### 直接搜索

```
/vv语录 <标题> [数量/参数]
```

### 引用消息搜索

```
引用某条消息 + /vv语录 [数量/参数]
```

### 支持本地API

在配置中设置 `VVQUEST_API_BASE` 项，填写完整API地址（如 <http://localhost:8000/search）>

## 示例

```
/vv语录 你好
/vv语录 你好 5
/vv语录 你好 n=5
```

## 注意事项

- 默认返回5条结果，最大返回数量受配置限制
- 请求有冷却时间，防止频繁请求
- 本地API失败时会自动回退到在线API

## 开源协议

本项目使用 [MIT](LICENSE) 许可证开源。
