from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment

# 定义一个帮助命令插件
help_command = on_command("帮助", aliases={"help", "帮助列表"}, rule=to_me(), block=True)


@help_command.handle()
async def handle_help(event: MessageEvent):
    # 获取当前用户的ID
    user_id = event.get_user_id()

    # 定义插件命令和说明
    commands = {
        "查作者": "查看某个作者的所有诗歌",
        "查标题": "根据诗歌标题查询诗歌内容",
        "查诗句": "根据诗句内容查询相关诗歌",
        "查关键词": "根据关键词查找相关诗句",
        "查对联": "查询相关对联（维护中）",
        "飞花令": "一起玩飞花令游戏（开发中）",
    }

    # 拼接帮助信息
    help_message = f"\n以下是功能列表：\n"
    for command, description in commands.items():
        help_message += f"{command}: {description}\n"

    # 回复帮助信息并@当前用户
    await help_command.finish(MessageSegment.at(user_id) + help_message)
