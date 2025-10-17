
# 飞花令裁判插件
import re
import asyncio
from nonebot import on_message
from nonebot import on_command, get_driver
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment, Bot, GroupMessageEvent
from nonebot.rule import to_me
from nonebot.params import CommandArg
from . import data_loader


# ...existing code...

# 主动结束命令
end_flower = on_command('结束', rule=to_me(), block=True)

@end_flower.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = event.group_id
    game = flower_games.get(gid)
    if not game or not game['started']:
        await end_flower.finish('当前没有正在进行的飞花令游戏。')
    # 主动结束，取消超时任务
    if game.get('timeout_task'):
        game['timeout_task'].cancel()
    await end_game(bot, gid, event)

    
    await end_flower.finish('游戏已手动结束。')


cc = data_loader.cc

# 游戏状态缓存（群号为key）
flower_games = {}

# 诗句分句函数，参考 poetry_search
# 修改分句规则：以逗号、句号、问号、感叹号为分界（不考虑顿号）
SENTENCE_SPLIT_REGEX = r'[，,。！？!?]'
def split_sentences(text):
    return [s.strip() for s in re.split(SENTENCE_SPLIT_REGEX, text or '') if s.strip()]

def remove_punct(text):
	return re.sub(r'[，,。！？!；;：:、\s]', '', text)

# 加载所有诗句（简体，无标点）
all_sentences = []
poems = []
poems.extend(data_loader.load_shijing(data_loader.shijing_dir + '/shijing.json'))
poems.extend(data_loader.load_chuci(data_loader.chuci_dir + '/chuci.json'))
poems.extend(data_loader.load_dynasty_poems(data_loader.han_dir, 'poetry.汉.'))
poems.extend(data_loader.load_dynasty_poems(data_loader.weijin_dir, 'poetry.晋.'))
poems.extend(data_loader.load_poems_from_dir(data_loader.tang_dir, 'poet.tang.'))
poems.extend(data_loader.load_poems_from_dir(data_loader.song_dir, 'poet.song.'))
poems.extend(data_loader.load_dynasty_poems(data_loader.jin_dir, 'poetry.金.'))
poems.extend(data_loader.load_dynasty_poems(data_loader.yuan_dir, 'poetry.元.'))
poems.extend(data_loader.load_dynasty_poems(data_loader.qing_dir, 'poetry.清.'))
poems.extend(data_loader.load_poems_from_dir(data_loader.hua_dir, 'huajianji-.', is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.nantang_dir, 'nantang', is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.ci_tang_dir, 'ci.tang', is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.ci_song_dir, 'ci.song.', is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.ci_jin_dir, 'ci.jin', is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.ci_qing_dir, 'ci.清.', is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.ci_yuan_dir, 'ci.元.', is_ci=True))

for poem in poems:
	for para in poem.get('paragraphs', []):
		for sent in split_sentences(para):
			all_sentences.append({
				'sentence': sent,
				'sentence_s': remove_punct(cc.convert(sent)),
				'poem': poem
			})

def get_sentence_match(keyword, used_sentences):
	key = remove_punct(cc.convert(keyword))
	for item in all_sentences:
		if key in item['sentence_s'] and item['sentence_s'] not in used_sentences:
			return item
	return None

# 可选关键字列表
FLOWER_KEYWORDS = [
    "花", "月", "风", "雪", "山", "水", "云", "雨", "春", "秋", "夜", "江", "柳", "梅", "叶", "阳", "天", "日"
]

# ----------------------
# 指令：准备飞花令
# ----------------------
prepare_flower = on_command('飞花令', rule=to_me(), block=True)

@prepare_flower.handle()
async def _(event: GroupMessageEvent):
    gid = event.group_id
    # 进入准备阶段，重置游戏状态
    flower_games[gid] = {
        'players': [], 'scores': {}, 'turn': 0, 'started': False, 'used': set(), 'current_keyword': '', 'timeout_task': None
    }
    await prepare_flower.finish('飞花令准备\n使用“加入”加入游戏')

# ----------------------
# 指令：加入飞花令
# ----------------------
join_flower = on_command('加入', rule=to_me(), block=True)

@join_flower.handle()
async def _(event: GroupMessageEvent):
	gid = event.group_id
	uid = event.user_id
	game = flower_games.setdefault(gid, {
		'players': [], 'scores': {}, 'turn': 0, 'started': False, 'used': set(), 'current_keyword': '', 'timeout_task': None
	})
	if game['started']:
		await join_flower.finish('游戏已开始，无法加入。')
	if uid not in game['players']:
		game['players'].append(uid)
		game['scores'][uid] = 0
		await join_flower.finish(Message([MessageSegment.at(uid), MessageSegment.text(f' 加入成功，当前玩家：{len(game["players"])}人')]))
	else:
		await join_flower.finish(Message([MessageSegment.at(uid), MessageSegment.text(' 已在游戏中')]))

# ----------------------
# 指令：开始飞花令
# ----------------------
start_flower = on_command('开始', rule=to_me(), block=True)

@start_flower.handle()
async def _(bot: Bot, event: GroupMessageEvent, msg: Message = CommandArg()):
    gid = event.group_id
    game = flower_games.get(gid)
    if not game or len(game['players']) < 2:
        await start_flower.finish('至少需要2人加入才能开始游戏。')
    if game['started']:
        await start_flower.finish('游戏已在进行中。')
    keyword = msg.extract_plain_text().strip()
    if not keyword:
        import random
        keyword = random.choice(FLOWER_KEYWORDS)
    game['started'] = True
    game['turn'] = 0
    game['used'] = set()
    game['current_keyword'] = keyword
    await start_flower.send(Message([
        MessageSegment.text(f'飞花令开始，关键字为“{keyword}”！\n第1轮：'),
        MessageSegment.at(game["players"][0]),
        MessageSegment.text(' 请作答（90秒内回复包含关键字的诗句）')
    ]))
    # 启动超时任务
    game['timeout_task'] = asyncio.create_task(timeout_judge(bot, event, 0, gid))

async def timeout_judge(bot, event, turn, gid):
    print(f"[飞花令] timeout_judge 启动: gid={gid}, turn={turn}")
    try:
        await asyncio.sleep(90)
        print(f"[飞花令] timeout_judge 90秒到: gid={gid}, turn={turn}")
        game = flower_games.get(gid)
        if not game:
            print(f"[飞花令] 超时: 未找到游戏状态 gid={gid}")
            return
        if not game['started']:
            print(f"[飞花令] 超时: 游戏未开始 gid={gid}")
            return
        if game['turn'] != turn:
            print(f"[飞花令] 超时: 当前轮已变化 gid={gid} turn={turn} 当前turn={game['turn']}")
            return
        if not game['players']:
            print(f"[飞花令] 超时: 无玩家 gid={gid}")
            return
        # turn 可能已超出（被移除玩家），需修正
        if game['turn'] >= len(game['players']):
            game['turn'] = 0
        uid = game['players'][turn]
        print(f"[飞花令] 玩家超时淘汰: uid={uid} gid={gid}")
        await bot.send_group_msg(group_id=gid, message=Message([
            MessageSegment.at(uid),
            MessageSegment.text(' 作答超时，出局')
        ]))
        # 淘汰该玩家
        game['players'].remove(uid)
        # 如果淘汰后只剩一人，直接结束
        if len(game['players']) == 1:
            print(f"[飞花令] 只剩一人，游戏结束 gid={gid}")
            await end_game(bot, gid, event)
            return
        # turn 不自增，直接轮到下一个（如果 turn 已超出则归零）
        if game['turn'] >= len(game['players']):
            game['turn'] = 0
        # 只在剩余玩家大于1时继续下一轮
        print(f"[飞花令] 下一位作答: uid={game['players'][game['turn']]} gid={gid}")
        await bot.send_group_msg(group_id=gid, message=Message([
            MessageSegment.at(game["players"][game["turn"]]),
            MessageSegment.text(' 请作答（90秒内回复）')
        ]))
        game['timeout_task'] = asyncio.create_task(timeout_judge(bot, event, game['turn'], gid))
    except Exception as e:
        import traceback
        print(f"[飞花令] timeout_judge 异常: {e}\n{traceback.format_exc()}")

# ----------------------
# 监听群消息作为答题
# ----------------------
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata
from nonebot import require
from nonebot.adapters.onebot.v11 import Bot

flower_message = on_message(priority=50, block=False)

@flower_message.handle()
async def handle_flower_message(bot: Bot, event: GroupMessageEvent):
    print(f"收到群消息: {event.group_id} {event.user_id} {event.message}")  # 调试日志
    gid = event.group_id
    uid = event.user_id
    game = flower_games.get(gid)
    if not game or not game['started']:
        return
    # 只允许当前轮到的玩家作答
    if uid != game['players'][game['turn']]:
        print(f"不是当前轮到的玩家: {uid}，应为: {game['players'][game['turn']]}")
        await bot.send(event, Message([
            MessageSegment.at(uid),
            MessageSegment.text(' 当前未轮到作答，请稍等')
        ]))
        return
    msg = str(event.message).strip()
    if not msg:
        print("消息内容为空")
        return
    keyword = game['current_keyword']
    ans_s = remove_punct(cc.convert(msg))
    # 匹配时以分句为单位，且必须完整等于最小分句
    found = None
    for item in all_sentences:
        # 必须完全等于最小分句（去标点、转简体后）且包含关键字，且未用过
        if ans_s == item['sentence_s'] and keyword in item['sentence_s'] and item['sentence_s'] not in game['used']:
            found = item
            break
    if not found:
        print(f"未匹配到诗句: {ans_s}")
        return
    # 回答正确
    print(f"玩家{uid}回答正确: {found['sentence']}")
    game['used'].add(found['sentence_s'])
    game['scores'][uid] += 1
    poem = found['poem']
    await bot.send(event, Message([
        MessageSegment.at(uid),
        MessageSegment.text(f'\n回答正确\n{found["sentence"]}。\n——《{poem.get("title", "")}》 {poem.get("author", "佚名")}')
    ]))
    # 下一轮
    game['turn'] = (game['turn'] + 1) % len(game['players'])
    if game['timeout_task']:
        print(f"[飞花令] 取消上一轮超时定时器 gid={gid}")
        game['timeout_task'].cancel()
    await bot.send_group_msg(group_id=gid, message=Message([
        MessageSegment.at(game["players"][game["turn"]]),
        MessageSegment.text(' 请作答（90秒内回复）')
    ]))
    print(f"[飞花令] 新一轮定时器启动: turn={game['turn']} uid={game['players'][game['turn']]} gid={gid}")
    game['timeout_task'] = asyncio.create_task(timeout_judge(bot, event, game['turn'], gid))
    # 检查是否只剩一人
    if len(game['players']) == 1:
        await end_game(bot, gid, event)

async def end_game(bot, gid, event):
    game = flower_games.get(gid)
    if not game:
        return
    game['started'] = False
    scores = game['scores']
    msg = [MessageSegment.text('游戏结束！最终得分：\n')]
    for uid, score in scores.items():
        msg.append(MessageSegment.at(uid))
        msg.append(MessageSegment.text(f'：{score}分\n'))
    await bot.send_group_msg(group_id=gid, message=Message(msg))
    del flower_games[gid]
