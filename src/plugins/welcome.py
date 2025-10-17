from nonebot import on_notice
from nonebot.adapters.onebot.v11 import GroupIncreaseNoticeEvent, MessageSegment

# 设置允许触发欢迎的群号列表
ALLOWED_GROUPS = {517953320, 1055152158}

# 监听所有 notice 事件
welcome_new_member = on_notice()


@welcome_new_member.handle()
async def handle_new_member(event: GroupIncreaseNoticeEvent):
    # 只处理新成员加群的事件
    if not isinstance(event, GroupIncreaseNoticeEvent):
        return

    # 限定白名单群
    if event.group_id not in ALLOWED_GROUPS:
        return

    # 新成员的 QQ 号
    new_member = event.user_id

    # 构造欢迎消息
    welcome_message = (
        f"\n文字是非常联友 青春在不老诗心\n"
        "欢迎加入楹联诗词协会！\n"
        "使用「帮助」查看功能列表~"
    )

    await welcome_new_member.finish(MessageSegment.at(new_member) + welcome_message)
