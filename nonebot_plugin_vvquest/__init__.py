"""
维维语录 - 通过API获取维维语录图片的NoneBot2插件
"""

from nonebot import on_command, get_bot, get_plugin_config
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.log import logger
import httpx
import time
from typing import Tuple

from nonebot.plugin import PluginMetadata
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="维维语录",
    description="通过API获取维维语录图片",
    usage="""
使用方式：
1. 直接搜索：
/vv语录 <标题> [数量/参数]
2. 引用消息搜索：
引用某条消息 + /vv语录 [数量/参数]
3. 支持本地API：
在配置中设置 api_base 项，填写完整API地址（如 http://localhost:8000/search）
""",
    type="application",
    homepage="https://github.com/webjoin111/nonebot-plugin-vvquest",
    config=Config,
    supported_adapters={"~onebot.v11"},
    extra={
        "author": "webjoin111",
        "version": "0.1.0"
    }
)



last_request_time: float = 0

# 获取插件配置
plugin_config = get_plugin_config(Config)

vv_quote = on_command("vv语录", aliases={"维维语录"}, priority=5, block=True)

async def build_message(img_urls: list) -> Message:
    """构建普通消息"""
    return Message([
        MessageSegment.text(f"找到 {len(img_urls)} 条相关语录：\n"),
        *[MessageSegment.image(url) for url in img_urls]
    ])

@vv_quote.handle()
async def handle_vv_quote(event: MessageEvent, args: Message = CommandArg()):
    global last_request_time
    try:
        # 从插件配置中获取值
        max_num = plugin_config.max_num
        use_forward = plugin_config.use_forward
        api_base = plugin_config.api_base
        cooldown = plugin_config.cooldown

        # 记录日志，便于调试
        logger.debug(f"当前配置: max_num={max_num}, use_forward={use_forward}, api_base={api_base}, cooldown={cooldown}")

        current_time = time.time()
        if current_time - last_request_time < cooldown:
            remaining = cooldown - (current_time - last_request_time)
            await vv_quote.finish(f"⏳ 请求过于频繁，请等待 {int(remaining)} 秒后再试")
            return
        last_request_time = current_time  # 更新冷却时间

        # 参数解析
        title, num = await parse_arguments(event, args)
        if not title:
            await vv_quote.finish("⚠️ 搜索内容不能为空！")
            return

        # 数值修正
        num = max(1, min(max_num, num))
        # 动态选择API地址
        api_url = api_base if api_base else "https://api.zvv.quest/search"

        async with httpx.AsyncClient(timeout=20) as client:
            try:
                # 优先尝试配置的API
                resp = await client.get(api_url, params={"q": title, "n": num})
            except (httpx.ConnectError, httpx.TimeoutException):
                # 本地API失败时回退在线API
                if api_base:
                    logger.warning(f"本地API {api_base} 访问失败，尝试使用默认API")
                    resp = await client.get("https://api.zvv.quest/search", params={"q": title, "n": num})
                else:
                    raise

            resp.raise_for_status()
            data = resp.json()

            if data["code"] != 200:
                await vv_quote.finish(f"❌ 接口错误：{data.get('msg', '未知错误')}")
                return

            if not data.get("data"):
                await vv_quote.finish("🔍 未找到相关语录图片")
                return

            # 处理合并转发
            if use_forward and len(data["data"]) > 1:
                try:
                    bot = get_bot(str(event.self_id))
                    msgs = []

                    for idx, url in enumerate(data["data"], 1):
                        image_msg = MessageSegment.image(url)
                        msgs.append({
                            "type": "node",
                            "data": {
                                "name": f"维维语录 {idx}",
                                "uin": str(event.self_id),
                                "content": str(image_msg)
                            }
                        })

                    if event.message_type == "group":
                        await bot.call_api(
                            "send_group_forward_msg",
                            group_id=event.group_id,
                            messages=msgs
                        )
                    else:
                        await bot.call_api(
                            "send_private_forward_msg",
                            user_id=event.user_id,
                            messages=msgs
                        )
                    return
                except Exception as e:
                    logger.error(f"合并转发消息发送失败: {repr(e)}")

            await vv_quote.finish(await build_message(data["data"]))

    except httpx.HTTPError as e:
        logger.error(f"API请求失败 | {str(e)}")
        await vv_quote.finish("⏳ 请求超时，请稍后再试")
    except Exception as e:
        logger.error(f"处理异常 | {repr(e)}")
        await vv_quote.finish("❌ 发生意外错误，请联系管理员")

async def parse_arguments(event: MessageEvent, args: Message) -> Tuple[str, int]:
    """参数解析"""
    # 使用固定默认值
    title = ""
    num = 5  # 默认返回5条结果

    if event.reply:
        title = event.reply.message.extract_plain_text().strip()

    args_str = args.extract_plain_text().strip()
    if args_str:
        parts = args_str.split()
        num_args = []

        for part in parts:
            if part.lower().startswith("n="):
                try:
                    num = int(part.split("=")[1])
                    num_args.append(part)
                except ValueError:
                    pass
            elif part.isdigit():
                num = int(part)
                num_args.append(part)

        if not event.reply:
            title = " ".join([p for p in parts if p not in num_args])

    return title.strip(), num