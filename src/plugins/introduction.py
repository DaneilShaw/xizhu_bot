# from nonebot import on_message, get_driver, get_loaded_plugins
# from nonebot.rule import to_me
# from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment
# from typing import Set

# # -------------------------
# # 收集所有命令并缓存
# # -------------------------
# CACHED_COMMANDS: Set[str] = set()
# driver = get_driver()


# @driver.on_startup
# async def collect_commands_at_startup():
#     """启动时收集所有命令名和别名"""
#     global CACHED_COMMANDS
#     CACHED_COMMANDS = set()
#     for plugin in get_loaded_plugins():
#         matchers = getattr(plugin, "matchers", []) or []
#         for matcher in matchers:
#             # 尝试安全获取常见命令属性
#             for attr in ["names", "aliases", "command"]:
#                 val = getattr(matcher, attr, None)
#                 if val:
#                     if isinstance(val, str):
#                         CACHED_COMMANDS.add(val.strip())
#                     elif isinstance(val, (list, tuple, set)):
#                         for n in val:
#                             if isinstance(n, str) and n.strip():
#                                 CACHED_COMMANDS.add(n.strip())


# def is_command_text(text: str) -> bool:
#     """判断消息是否以已注册命令开头"""
#     text = text.strip()
#     if not text:
#         return False
#     for cmd in CACHED_COMMANDS:
#         if not cmd:
#             continue
#         # 精确匹配或命令后跟空格/换行视为命令
#         if text == cmd or text.startswith(cmd + " ") or text.startswith(cmd + "\n"):
#             return True
#     return False


# # -------------------------
# # 兜底 matcher
# # -------------------------
# introduction = on_message(rule=to_me(), priority=100, block=True)


# @introduction.handle()
# async def handle_introduce(event: MessageEvent):
#     text = event.get_plaintext().strip()
#     # 如果文本是命令，放行不触发
#     if is_command_text(text):
#         return

#     user_id = event.get_user_id()
#     introduction_msg = (
#         " 使用「帮助」查看功能列表"
#     )
#     await introduction.finish(MessageSegment.at(user_id) + introduction_msg)
