import os
import json
from opencc import OpenCC

# 初始化OpenCC用于简繁体转换
cc = OpenCC('t2s')  # 繁体 -> 简体

# 设置数据目录
root_dir = os.path.join(os.path.dirname(__file__), "../../")
shijing_dir = os.path.join(root_dir, "data/poetry/The Book of Songs")
chuci_dir = os.path.join(root_dir, "data/poetry/chuci")
han_dir = os.path.join(root_dir, "data/poetry/han")
weijin_dir = os.path.join(root_dir, "data/poetry/weijin")
tang_dir = os.path.join(root_dir, "data/poetry/tang")
song_dir = os.path.join(root_dir, "data/poetry/song")
jin_dir = os.path.join(root_dir, "data/poetry/jin")
yuan_dir = os.path.join(root_dir, "data/poetry/yuan")
qing_dir = os.path.join(root_dir, "data/poetry/qing")
hua_dir = os.path.join(root_dir, "data/ci/wudaishiguo/huajianji")
nantang_dir = os.path.join(root_dir, "data/ci/wudaishiguo/nantang")
ci_song_dir = os.path.join(root_dir, "data/ci/song")
ci_jin_dir = os.path.join(root_dir, "data/ci/jin")
ci_tang_dir = os.path.join(root_dir, "data/ci/tang")
ci_qing_dir = os.path.join(root_dir, "data/ci/qing")
ci_yuan_dir = os.path.join(root_dir, "data/ci/yuan")


def load_poems_from_dir(dir_path, prefix, is_ci=False):
    poems_list = []
    if not os.path.exists(dir_path):
        return poems_list
    for filename in os.listdir(dir_path):
        if filename.startswith(prefix) and filename.endswith(".json"):
            file_path = os.path.join(dir_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for poem in data:
                    if is_ci:
                        # 如果是宋词，优先用 rhythmic
                        if "rhythmic" in poem:
                            poem["title"] = poem.get("rhythmic", "无题")
                        # 如果是金词或其他 ci 类型，content -> paragraphs
                        if "content" in poem:
                            poem["paragraphs"] = poem.get("content", [])
                        # 处理作者字段
                        if "authorName" in poem:
                            poem["author"] = poem["authorName"]
                        elif "author" not in poem:
                            poem["author"] = "佚名"
                    else:
                        # 非 ci 类型也保证有 author 字段
                        if "author" not in poem:
                            poem["author"] = "佚名"
                    # 增加简体字段，便于检索
                    poem["title_s"] = cc.convert(poem.get("title", ""))
                    poem["paragraphs_s"] = [cc.convert(p) for p in poem.get("paragraphs", [])]
                    poems_list.append(poem)
    return poems_list


def load_dynasty_poems(dir_path, prefix):  # 加载指定朝代的诗歌数据
    poems_list = []
    if not os.path.exists(dir_path):
        return poems_list

    for filename in os.listdir(dir_path):
        if filename.startswith(prefix) and filename.endswith(".json"):
            file_path = os.path.join(dir_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for poem in data:
                    # 处理标题
                    poem["title_s"] = cc.convert(poem.get("title", ""))
                    # content -> paragraphs
                    poem["paragraphs"] = poem.get("content", [])
                    poem["paragraphs_s"] = [cc.convert(p) for p in poem["paragraphs"]]
                    # 处理作者
                    if "authorName" in poem:
                        poem["author"] = poem["authorName"]
                    elif "author" not in poem:
                        poem["author"] = "佚名"
                    poems_list.append(poem)
    return poems_list


def load_shijing(path):
    poems_list = []
    if not os.path.exists(path):
        return poems_list
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for poem in data:
            # 标题
            poem["title_s"] = cc.convert(poem.get("title", ""))
            # content -> paragraphs
            poem["paragraphs"] = poem.get("content", [])
            poem["paragraphs_s"] = [cc.convert(p) for p in poem["paragraphs"]]
            # 默认作者为佚名
            if "author" not in poem:
                poem["author"] = "佚名"
            poems_list.append(poem)
    return poems_list


def load_chuci(path):
    poems_list = []
    if not os.path.exists(path):
        return poems_list
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for poem in data:
            # 标题
            poem["title_s"] = cc.convert(poem.get("title", ""))
            # content -> paragraphs
            poem["paragraphs"] = poem.get("content", [])
            poem["paragraphs_s"] = [cc.convert(p) for p in poem["paragraphs"]]
            # 默认作者为佚名
            if "author" not in poem:
                poem["author"] = "佚名"
            poems_list.append(poem)
    return poems_list


# 加载作者信息
def load_authors_once(path, authors_dict):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        authors_list = json.load(f)
    for author in authors_list:
        name = author.get("name", "佚名")
        name_s = cc.convert(name)  # 转成简体
        desc = author.get("desc") or author.get("description") or author.get("short_description") or ""

        # 构造只保留 name 和 desc 的作者信息
        author_info = {
            "name": name,
            "desc": desc
        }

        # 确保简体和原名都能检索到
        if name not in authors_dict:
            authors_dict[name] = author_info
        if name_s not in authors_dict:
            authors_dict[name_s] = author_info


# 加载所有作者信息
def load_all_authors(authors_dict):
    load_authors_once(os.path.join(tang_dir, "authors.tang.json"), authors_dict)
    load_authors_once(os.path.join(song_dir, "authors.song.json"), authors_dict)
    load_authors_once(os.path.join(ci_song_dir, "author.song.json"), authors_dict)
    load_authors_once(os.path.join(nantang_dir, "authors.json"), authors_dict)
    load_authors_once(os.path.join(qing_dir, "author.json"), authors_dict)
