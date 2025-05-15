from nonebot import on_command, get_bot
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.log import logger
from nonebot.exception import FinishedException
import httpx
import time
import asyncio
from typing import Tuple

from nonebot.plugin import PluginMetadata
from .config import Config, plugin_config, RETRY_TIMES, RETRY_DELAY

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
在配置中设置 VVQUEST_API_BASE 项，填写完整API地址（如 http://localhost:8000/search）
""",
    type="application",
    homepage="https://github.com/webjoin111/nonebot-plugin-vvquest",
    config=Config,
    supported_adapters={"~onebot.v11"},
    extra={"author": "webjoin111", "version": "0.1.0"},
)


last_request_time: float = 0

vv_quote = on_command("vv语录", aliases={"维维语录"}, priority=5, block=True)


async def build_message(img_urls: list) -> Message:
    """构建普通消息"""
    return Message(
        [
            MessageSegment.text(f"找到 {len(img_urls)} 条相关语录：\n"),
            *[MessageSegment.image(url) for url in img_urls],
        ]
    )


@vv_quote.handle()
async def handle_vv_quote(event: MessageEvent, args: Message = CommandArg()):
    global last_request_time
    try:
        max_num = plugin_config.vvquest_max_num
        use_forward = plugin_config.vvquest_use_forward
        api_base = plugin_config.vvquest_api_base
        cooldown = plugin_config.vvquest_cooldown

        logger.debug(
            f"当前配置: max_num={max_num}, use_forward={use_forward}, api_base={api_base}, "
            f"cooldown={cooldown}, retry_times={RETRY_TIMES}, retry_delay={RETRY_DELAY}"
        )

        current_time = time.time()
        if current_time - last_request_time < cooldown:
            remaining = cooldown - (current_time - last_request_time)
            await vv_quote.finish(f"⏳ 请求过于频繁，请等待 {int(remaining)} 秒后再试")
        last_request_time = current_time

        title, num = await parse_arguments(event, args)
        if not title:
            await vv_quote.finish("⚠️ 搜索内容不能为空！")

        num = max(1, min(max_num, num))

        api_url = api_base if api_base else "https://api.zvv.quest/search"

        data = await fetch_data(api_url, title, num, RETRY_TIMES, RETRY_DELAY, api_base)

        if not data.get("data"):
            await vv_quote.finish("🔍 未找到相关语录图片")

        if use_forward and len(data["data"]) > 1:
            try:
                await send_forward_message(event, data["data"])
                await vv_quote.finish()
            except Exception as e:
                logger.error(f"合并转发消息发送失败: {repr(e)}")

        await vv_quote.finish(await build_message(data["data"]))

    except httpx.HTTPError as e:
        logger.error(f"API请求失败 | {str(e)}")
        await vv_quote.finish("⏳ 请求超时，请稍后再试")
    except FinishedException:
        pass
    except Exception as e:
        logger.error(f"处理异常 | {repr(e)}")
        await vv_quote.finish("❌ 发生意外错误，请联系管理员")


async def fetch_data(
    api_url: str,
    title: str,
    num: int,
    retry_times: int,
    retry_delay: float,
    api_base: str = "",
):
    """发送API请求并处理重试逻辑"""
    async with httpx.AsyncClient(timeout=20) as client:

        async def make_request(
            url: str, params: dict, attempt: int = 1, is_fallback: bool = False
        ):
            """发送请求并处理重试逻辑"""
            try:
                logger.debug(f"正在发送请求 (尝试 {attempt}/{retry_times + 1}): {url}")
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as e:
                if is_fallback or attempt > retry_times:
                    logger.error(f"请求失败 ({url}): {str(e)}")
                    raise

                logger.warning(f"请求失败 (尝试 {attempt}/{retry_times + 1}): {str(e)}")
                await asyncio.sleep(retry_delay)
                return await make_request(url, params, attempt + 1, is_fallback)

        try:
            resp = await make_request(api_url, {"q": title, "n": num})
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
            if api_base:
                logger.warning(f"本地API {api_base} 访问失败，尝试使用默认API")
                resp = await make_request(
                    "https://api.zvv.quest/search",
                    {"q": title, "n": num},
                    is_fallback=True,
                )
            else:
                raise

        data = resp.json()
        if data["code"] != 200:
            raise ValueError(f"API错误: {data.get('msg', '未知错误')}")

        return data


async def send_forward_message(event: MessageEvent, img_urls: list):
    """发送合并转发消息"""
    bot = get_bot(str(event.self_id))
    msgs = []

    for idx, url in enumerate(img_urls, 1):
        image_msg = MessageSegment.image(url)
        msgs.append(
            {
                "type": "node",
                "data": {
                    "name": f"维维语录 {idx}",
                    "uin": str(event.self_id),
                    "content": str(image_msg),
                },
            }
        )

    if event.message_type == "group":
        await bot.call_api(
            "send_group_forward_msg",
            group_id=event.group_id,
            messages=msgs,
        )
    else:
        await bot.call_api(
            "send_private_forward_msg",
            user_id=event.user_id,
            messages=msgs,
        )


async def parse_arguments(event: MessageEvent, args: Message) -> Tuple[str, int]:
    """参数解析"""
    title = ""
    num = 5

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
