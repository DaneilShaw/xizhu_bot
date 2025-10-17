# -----------------------
# 1. 导入库
# -----------------------
import os
import re
from typing import Dict, List
from nonebot.adapters.onebot.v11 import Message
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment
from . import data_loader
cc = data_loader.cc

# -----------------------
# 2. 加载数据
# -----------------------
# 加载诗词
poems = []
poems.extend(data_loader.load_shijing(os.path.join(data_loader.shijing_dir, "shijing.json")))
poems.extend(data_loader.load_chuci(os.path.join(data_loader.chuci_dir, "chuci.json")))
poems.extend(data_loader.load_dynasty_poems(data_loader.han_dir, "poetry.汉."))
poems.extend(data_loader.load_dynasty_poems(data_loader.weijin_dir, "poetry.晋."))
poems.extend(data_loader.load_poems_from_dir(data_loader.tang_dir, "poet.tang."))
poems.extend(data_loader.load_poems_from_dir(data_loader.song_dir, "poet.song."))
poems.extend(data_loader.load_dynasty_poems(data_loader.jin_dir, "poetry.金."))
poems.extend(data_loader.load_dynasty_poems(data_loader.yuan_dir, "poetry.元."))
poems.extend(data_loader.load_dynasty_poems(data_loader.qing_dir, "poetry.清."))
poems.extend(data_loader.load_poems_from_dir(data_loader.hua_dir, "huajianji-.", is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.nantang_dir, "nantang", is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.ci_tang_dir, "ci.tang", is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.ci_song_dir, "ci.song.", is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.ci_jin_dir, "ci.jin", is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.ci_qing_dir, "ci.清.", is_ci=True))
poems.extend(data_loader.load_poems_from_dir(data_loader.ci_yuan_dir, "ci.元.", is_ci=True))

# 作者信息加载
authors = {}
data_loader.load_all_authors(authors)


# -----------------------
# 3.定义搜索函数
# -----------------------
def fuzzy_search(query, include_title: bool = True):
    query_s = cc.convert(query)  # 用户输入先转换成简体
    results = []
    for poem in poems:
        # 当允许匹配标题并且标题包含关键字时
        if include_title and query_s in poem.get("title_s", ""):
            results.append(poem)
            continue
        # 去掉顿号用于匹配（但不改变原数据）
        for line in poem.get("paragraphs_s", []):
            line_s = line.replace("、", "")  # 去掉诗句中的顿号以便匹配
            if query_s in line_s:
                results.append(poem)
                break
    return results


def get_author_display(poem: dict) -> str:
    """返回作者显示信息；诗经显示为 chapter+section"""
    author_display = poem.get("author", "佚名")
    if author_display == "佚名" and "chapter" in poem and "section" in poem:
        author_display = f"{poem['chapter']} {poem['section']}"
    return author_display


def split_sentences(text: str) -> List[str]:
    """按多种标点（。！？,，；;：: 等）分句并去空白"""
    text = (text or "").strip()
    if not text:
        return []
    parts = re.split(r'[。！？!?，,；;：:]', text)
    return [p.strip() for p in parts if p.strip()]


def format_poem(poem: dict) -> str:
    """把一首诗格式化成字符串（用于查题 / 查句的展示）"""
    author = get_author_display(poem)
    paragraphs = poem.get("paragraphs", [])
    content = "\n".join(paragraphs)
    return f"《{poem.get('title', '')}》 —— {author}\n{content}\n" + "—" * 14 + "\n"


def format_sentence(item: dict) -> str:
    """把单条关键词命中格式化成字符串（用于查关键词）"""
    author = get_author_display(item)
    sentence = item.get("sentence", "")
    title = item.get("title", "")
    return f"{sentence}。——《{title}》 {author}\n" + "-" * 28 + "\n"


# 简单的 per-user 查询缓存（内存缓存）
search_cache: Dict[int, dict] = {}

# 每种查询类型每页显示数量
PAGE_SIZE = {
    "poem": 2,  # 按题目查诗 / 按诗句查诗
    "sentence": 10,  # 按关键词查诗
    "author": 15  # 按作者查诗
}


def set_search_cache(user_id: int, results: List[dict], kind: str = "poem"):
    """缓存查询结果，kind: 'poem' 或 'sentence'"""
    search_cache[user_id] = {"results": results, "page": 0, "kind": kind}


def get_page(user_id: int, page_num: int = None, page_size: int = 3):
    """
    获取指定页或下一页。
    Args:
        user_id: 用户ID
        page_num: 指定页码，如果为 None 则返回下一页
        page_size: 每页数量
    Returns:
        page_results: 当前页结果列表
        total: 总结果数
        current_page: 当前页码
        kind: 查询类型
    """
    cache = search_cache.get(user_id)
    if not cache:
        return [], 0, 0, None

    total = len(cache["results"])
    max_page = (total + page_size - 1) // page_size

    # 如果用户没有指定页码，则自动翻下一页
    if page_num is None:
        page_num = cache.get("page", 0) + 1

    # 页码越界处理
    if page_num < 1:
        page_num = 1
    elif page_num > max_page:
        page_num = max_page

    start = (page_num - 1) * page_size
    end = start + page_size
    page_results = cache["results"][start:end]
    cache["page"] = page_num  # 更新当前页

    return page_results, total, page_num, cache["kind"]


def format_poem_brief(poem: dict, kind: str = "poem") -> str:
    """只显示标题，宋词显示 词牌+首句"""
    author = get_author_display(poem)
    title = poem.get("title", "")
    paragraphs = poem.get("paragraphs", [])

    if "rhythmic" in poem:  # 判断是否为词
        first_line = paragraphs[0] if paragraphs else ""

        if kind == "author":  # 查作者时使用小句分割并去除标点
            # 先拆分句子，以标点为分界
            first_sentences = split_sentences(first_line)
            # 获取第一小句并去掉标点，顿号不参与判断
            first_sentence = first_sentences[0] if first_sentences else ""
            # 去除除顿号外的所有标点
            first_sentence = re.sub(r"[。！？!；:]", "", first_sentence)
        else:  # 查关键词时保持原有带标点输出
            first_sentence = first_line

        # 返回格式化后的标题+首句
        return f"{title} {first_sentence} —— {author}"
    else:
        return f"《{title}》 —— {author}"


# -----------------------
# 4. 命令：按题目查诗
# -----------------------
poem_by_title = on_command("查标题", aliases={"查诗题"}, rule=to_me(), block=True)


@poem_by_title.handle()
async def handle_title(event: MessageEvent, msg: Message = CommandArg()):
    query = msg.extract_plain_text().strip()

    if not query:
        await poem_by_title.finish(
            Message([MessageSegment.at(event.user_id),
                     MessageSegment.text("\n请发送要查询的诗题，比如：@我 查诗题 静夜思")])
        )

    query_s = cc.convert(query)
    results = [p for p in poems if query_s in p.get("title_s", "")]

    if not results:
        await poem_by_title.finish(
            Message([MessageSegment.at(event.user_id),
                     MessageSegment.text("\n没有找到相关标题")])
        )

    # 缓存查询并返回第一页（每页 2 条）
    set_search_cache(event.user_id, results, kind="poem")
    page_results, total, page, _ = get_page(event.user_id, page_num=1, page_size=PAGE_SIZE["poem"])  # 默认第一页

    reply_segments = [
        MessageSegment.at(event.user_id),
        MessageSegment.text(f"\n共找到 {total} 条结果，当前第 {page} 页（每页 2 条）。发送「下一页」或「第x页」查看更多。\n")
    ]

    for poem in page_results:
        reply_segments.append(MessageSegment.text(format_poem(poem)))

    await poem_by_title.finish(Message(reply_segments))


# -----------------------
# 4. 命令：按作者查诗
# -----------------------
poem_by_author = on_command("查作者", rule=to_me(), block=True)


@poem_by_author.handle()
async def handle_author(event: MessageEvent, msg: Message = CommandArg()):
    query = msg.extract_plain_text().strip()
    if not query:
        await poem_by_author.finish(Message([
            MessageSegment.at(event.user_id),
            MessageSegment.text("\n请发送要查询的作者，比如：@我 查作者 李清照")
        ]))

    query_s = cc.convert(query)

    # 作者简介
    author_info = authors.get(query_s) or authors.get(query)
    if author_info:
        # 优先 short_description，没有再用 description / desc
        intro = author_info.get("short_description") or author_info.get("description") or author_info.get(
            "desc") or "暂无简介。"
    else:
        intro = "暂无简介。"

    # 作品检索
    results = [p for p in poems if cc.convert(p.get("author", "")) == query_s]
    if not results:
        await poem_by_author.finish(Message([
            MessageSegment.at(event.user_id),
            MessageSegment.text(f"\n没有找到作者“{query}”的作品")
        ]))

    # 缓存并分页（每页 15 条）
    set_search_cache(event.user_id, results, kind="author")
    page_results, total, page, _ = get_page(event.user_id, page_num=1, page_size=PAGE_SIZE["author"])

    reply_segments = [
        MessageSegment.at(event.user_id),
        MessageSegment.text(f"\n作者：{query}\n简介：{intro}\n"),
        MessageSegment.text(f"\n共找到 {total} 首作品，当前第 {page} 页（每页 15 首）。\n"),
        MessageSegment.text("发送「查看 序号」查看完整内容，发送「下一页」或「第x页」查看更多。\n\n")
    ]
    for idx, poem in enumerate(page_results, start=1 + (page - 1) * 5):
        reply_segments.append(MessageSegment.text(f"{idx}. {format_poem_brief(poem, kind='author')}\n"))

    await poem_by_author.finish(Message(reply_segments))


# -----------------------
# 5.命令：按诗句查诗
# -----------------------
poem_by_content = on_command("查诗句", rule=to_me(), block=True)


@poem_by_content.handle()
async def handle_content(event: MessageEvent, msg: Message = CommandArg()):
    query = msg.extract_plain_text().strip()

    if not query:
        await poem_by_content.finish(
            Message([MessageSegment.at(event.user_id),
                     MessageSegment.text("\n请发送要查询的诗句，比如：@我 查诗句 <关键字>")])
        )

    results = fuzzy_search(query, include_title=False)

    if not results:
        await poem_by_content.finish(
            Message([MessageSegment.at(event.user_id),
                     MessageSegment.text("\n没有找到包含该诗句的诗词")])
        )

    # 缓存并分页（每页 2 条）
    set_search_cache(event.user_id, results, kind="poem")
    page_results, total, page, _ = get_page(event.user_id, page_num=1, page_size=PAGE_SIZE["poem"])

    reply_segments = [
        MessageSegment.at(event.user_id),
        MessageSegment.text(f"\n共找到 {total} 条结果，当前第 {page} 页（每页 2 条）。发送「下一页」或「第x页」查看更多。\n")
    ]

    for poem in page_results:
        reply_segments.append(MessageSegment.text(format_poem(poem)))

    await poem_by_content.finish(Message(reply_segments))


# -----------------------
# 5.命令：按关键词查诗
# -----------------------
poem_by_keyword = on_command("查关键词", rule=to_me(), block=True)


@poem_by_keyword.handle()
async def handle_keyword(event: MessageEvent, msg: Message = CommandArg()):
    query = msg.extract_plain_text().strip()

    if not query:
        await poem_by_keyword.finish(
            Message([MessageSegment.at(event.user_id),
                     MessageSegment.text("\n请发送要查询的关键词，比如：@我 查关键词 黄河")])
        )

    query_s = cc.convert(query)
    results: List[dict] = []

    for poem in poems:
        for line_s, line in zip(poem["paragraphs_s"], poem["paragraphs"]):
            if query_s in line_s:
                for s in split_sentences(line):
                    if query_s in cc.convert(s):
                        results.append({
                            "sentence": s,
                            "title": poem.get("title", ""),
                            "author": poem.get("author", "佚名"),
                            "chapter": poem.get("chapter"),
                            "section": poem.get("section"),
                        })
                break  # 每首诗只取一次匹配

    if not results:
        await poem_by_keyword.finish(
            Message([MessageSegment.at(event.user_id),
                     MessageSegment.text(f"\n没有找到包含关键词“{query}”的诗句")])
        )

    # 缓存并分页（每页 10 条）
    set_search_cache(event.user_id, results, kind="sentence")
    page_results, total, page, _ = get_page(event.user_id, page_num=1, page_size=PAGE_SIZE["sentence"])

    reply_segments = [
        MessageSegment.at(event.user_id),
        MessageSegment.text(
            f"\n共找到 {total} 条包含关键词“{query}”的诗句，当前第 {page} 页（每页 10 条）。发送「下一页」或「第x页」查看更多。\n")
    ]

    for item in page_results:
        reply_segments.append(MessageSegment.text(format_sentence(item)))

    await poem_by_keyword.finish(Message(reply_segments))


# -----------------------
# 5.命令：查看某一首作品全文
# -----------------------
view_poem_cmd = on_command("查看", rule=to_me(), block=True)


@view_poem_cmd.handle()
async def handle_view(event: MessageEvent, msg: Message = CommandArg()):
    query = msg.extract_plain_text().strip()
    if not query.isdigit():
        await view_poem_cmd.finish(Message([
            MessageSegment.at(event.user_id),
            MessageSegment.text("\n请输入要查看的序号，比如：@我 查看 3")
        ]))

    index = int(query)
    cache = search_cache.get(event.user_id)
    if not cache or cache.get("kind") != "author":
        await view_poem_cmd.finish(Message([
            MessageSegment.at(event.user_id),
            MessageSegment.text("\n请先使用“查作者”获取作品列表")
        ]))

    results = cache["results"]
    if index < 1 or index > len(results):
        await view_poem_cmd.finish(Message([
            MessageSegment.at(event.user_id),
            MessageSegment.text("\n序号超出范围")
        ]))

    poem = results[index - 1]
    await view_poem_cmd.finish(Message([
        MessageSegment.at(event.user_id),
        MessageSegment.text(format_poem(poem))
    ]))


# -----------------------
# 5.命令：翻页
# -----------------------
next_page_cmd = on_command("下一页", rule=to_me(), block=True)


@next_page_cmd.handle()
async def handle_next(event: MessageEvent, _: Message = CommandArg()):
    user_id = event.user_id
    cache = search_cache.get(user_id)
    if not cache:
        await next_page_cmd.finish(Message([
            MessageSegment.at(user_id),
            MessageSegment.text("\n请先发起查询（例如：@我 查诗句 xx 或 查作者 xx）")
        ]))

    kind = cache.get("kind", "poem")
    page_size = PAGE_SIZE.get(kind, 2)

    # 不传 page_num = None 就是下一页
    page_results, total, page, kind = get_page(user_id, page_num=None, page_size=page_size)

    if not page_results:
        await next_page_cmd.finish(Message([
            MessageSegment.at(user_id),
            MessageSegment.text("\n没有更多了")
        ]))

    reply_segments = [MessageSegment.at(user_id),
                      MessageSegment.text(f"\n共找到 {total} 条结果，当前第 {page} 页。\n")]

    if kind == "poem":
        for poem in page_results:
            reply_segments.append(MessageSegment.text(format_poem(poem)))
    elif kind == "sentence":
        for item in page_results:
            reply_segments.append(MessageSegment.text(format_sentence(item)))
    elif kind == "author":
        reply_segments.append(MessageSegment.text("发送「查看 序号」可查看完整内容。\n\n"))
        start_index = (page - 1) * page_size + 1
        for idx, poem in enumerate(page_results, start=start_index):
            reply_segments.append(MessageSegment.text(f"{idx}. {format_poem_brief(poem, kind='author')}\n"))

    await next_page_cmd.finish(Message(reply_segments))


# -----------------------
# 5.命令：跳转到某页
# -----------------------
jump_page_cmd = on_command("第", rule=to_me(), block=True)


@jump_page_cmd.handle()
async def handle_jump(event: MessageEvent, msg: Message = CommandArg()):
    text = msg.extract_plain_text().strip()
    if not text.endswith("页") or not text[:-1].isdigit():
        await jump_page_cmd.finish(Message([
            MessageSegment.at(event.user_id),
            MessageSegment.text("\n请输入要跳转的页码，比如：@我 第3页")
        ]))

    page_num = int(text[:-1])
    cache = search_cache.get(event.user_id)
    if not cache:
        await jump_page_cmd.finish(Message([
            MessageSegment.at(event.user_id),
            MessageSegment.text("\n请先发起查询（例如：@我 查诗句 xx 或 查作者 xx）")
        ]))

    kind = cache.get("kind", "poem")
    page_size = PAGE_SIZE.get(kind, 2)

    page_results, total, page, kind = get_page(event.user_id, page_num=page_num, page_size=page_size)
    if not page_results:
        await jump_page_cmd.finish(Message([
            MessageSegment.at(event.user_id),
            MessageSegment.text(f"\n页码超出范围（共 {(total + page_size - 1) // page_size} 页）")
        ]))

    reply_segments = [MessageSegment.at(event.user_id),
                      MessageSegment.text(f"\n共找到 {total} 条结果，当前第 {page} 页。\n")]

    if kind == "poem":
        for poem in page_results:
            reply_segments.append(MessageSegment.text(format_poem(poem)))
    elif kind == "sentence":
        for item in page_results:
            reply_segments.append(MessageSegment.text(format_sentence(item)))
    elif kind == "author":
        reply_segments.append(MessageSegment.text("发送「查看 序号」可查看完整内容。\n\n"))
        start_index = (page - 1) * page_size + 1
        for idx, poem in enumerate(page_results, start=start_index):
            reply_segments.append(MessageSegment.text(f"{idx}. {format_poem_brief(poem, kind='author')}\n"))

    await jump_page_cmd.finish(Message(reply_segments))
