# -*- coding: utf-8 -*-
# v2: 主源=英文维基百科词条首图(pageimages)，兜底=Wikimedia Commons 搜索
# 统一裁剪为 512x512 PNG；可断点续跑
# 用法: python3 fetch_images.py [--offset N] [--limit M]
import json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageOps

ROOT = "/Users/naeemo/Workspace/word_game"
IMGDIR = os.path.join(ROOT, "images")
MANIFEST = os.path.join(IMGDIR, "manifest.json")
FAILED = os.path.join(IMGDIR, "failed.json")
UA = {"User-Agent": "wordgame-local/1.0 (offline kids word game, family use)"}

# 抽象词（虚词/代词/冠词/系动词/情态/疑问/连词/介词/感叹）+ 描述性形容词/情绪/程度词
# 这些词维基没有合适首图，留给第二阶段（AI 生图或家长手配）
SKIP = set("""
a an the and or but of to in on at by for from with about after before behind beside between
under over off out up down all any some every many much no not yes OK please sorry thank hello hi goodbye welcome
be do have can may must should will I you he she it we they me him her us them my your his its our their
this that these those there here what when where which who whose why how now then today tomorrow yesterday
again also always often sometimes never very too so because Mr Mrs Ms Miss PE o'clock time lot pair kind idea
age way sure dear well fine OK such
big small long short tall fast slow heavy thin hard strong happy sad angry tired excited afraid surprised
beautiful cute lovely wonderful nice good bad great fine new old young easy difficult right wrong far near
early late last next hot cold warm cool clean dirty interesting favourite famous helpful careful difficult
hungry ill free different same full empty light dark high low deep wide
""".split())

# 词条名修正（消歧/重定向优化）；默认用首字母大写的原词
HINTS = {
    "apple": "Apple", "orange": "Orange (fruit)", "mouse": "Mouse", "chicken": "Chicken",
    "bear": "Bear", "plane": "Airplane", "spring": "Spring (season)", "fan": "Electric fan",
    "watch": "Watch", "glass": "Drinking glass", "cap": "Baseball cap", "letter": "Letter (message)",
    "TV": "Television", "ping-pong": "Table tennis", "football": "Association football",
    "bike": "Bicycle", "phone": "Telephone", "maths": "Mathematics", "body": "Human body",
    "doctor": "Physician", "baby": "Infant", "kid": "Child", "friend": "Friendship",
    "cook": "Cooking", "sweep": "Broom", "fly": "Flight", "play": "Play (activity)",
    "run": "Running", "walk": "Walking", "jump": "Jumping", "swim": "Swimming",
    "sing": "Singing", "read": "Reading", "write": "Writing", "draw": "Drawing",
    "eat": "Eating", "drink": "Drinking", "sleep": "Sleep", "cry": "Crying",
    "wash": "Washing", "clean": "Cleaning", "shop": "Retail", "panda": "Giant panda",
    "cow": "Cattle", "card": "Greeting card", "table": "Table (furniture)",
    "worker": "Wage labour", "hour": "Hour", "minute": "Minute", "week": "Week",
    "month": "Month", "season": "Season", "photo": "Photograph", "picture": "Image",
    "colour": "Color", "sock": "Sock", "shoe": "Shoe", "shorts": "Shorts",
    "trousers": "Trousers", "clothes": "Clothing", "dress": "Dress", "coat": "Coat",
    "noodle": "Noodle", "meat": "Meat", "plant": "Plant", "star": "Star",
    "art": "Art", "music": "Music", "song": "Song", "film": "Film",
    "cinema": "Movie theater", "game": "Game", "toy": "Toy", "ball": "Ball",
    "answer": "Answer", "question": "Question", "word": "Word", "name": "Name",
}

def slug(w):
    return re.sub(r"[^a-z0-9]+", "_", w.lower()).strip("_")

def http_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def fetch_bytes(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()

def wiki_lead_image(title):
    params = {"action": "query", "format": "json", "prop": "pageimages",
              "piprop": "thumbnail|name", "pithumbsize": "640",
              "titles": title, "redirects": "1"}
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    res = http_json(url)
    for p in res.get("query", {}).get("pages", {}).values():
        t = p.get("thumbnail")
        if t and t.get("source"):
            return t["source"], "https://en.wikipedia.org/wiki/" + urllib.parse.quote(p.get("title", title).replace(" ", "_"))
    return None, None

def commons_search(query):
    params = {"action": "query", "format": "json", "generator": "search",
              "gsrsearch": query, "gsrnamespace": "6", "gsrlimit": "8",
              "prop": "imageinfo", "iiprop": "url|size|mime", "iiurlwidth": "640"}
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    res = http_json(url)
    pages = res.get("query", {}).get("pages", {})
    for p in sorted(pages.values(), key=lambda x: x.get("index", 99)):
        ii = (p.get("imageinfo") or [None])[0]
        if not ii or ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        w, h = ii.get("width", 0), ii.get("height", 0)
        if w < 300 or h < 300 or not (0.45 < w / h < 2.2):
            continue
        return ii["thumburl"], ii.get("descriptionurl", "")
    return None, None

def with_retry(fn, *a):
    delay = 2
    for i in range(4):
        try:
            return fn(*a)
        except Exception as e:
            if "429" in str(e) or "503" in str(e) or "timed out" in str(e):
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise RuntimeError("retry exhausted")

def make_square(path, data):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    im = Image.open(tmp)
    im = ImageOps.exif_transpose(im).convert("RGB")
    w, h = im.size
    side = min(w, h)
    im = im.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
    im = im.resize((512, 512), Image.LANCZOS)
    im.save(path, "PNG")
    os.remove(tmp)

def main():
    args = sys.argv[1:]
    offset = int(args[args.index("--offset") + 1]) if "--offset" in args else 0
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 10**9

    os.makedirs(IMGDIR, exist_ok=True)
    data = json.load(open(os.path.join(ROOT, "data", "words.json")))
    words, seen = [], set()
    for e in data["words"]:
        if e["word"] not in seen:
            seen.add(e["word"])
            words.append(e["word"])

    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    failed = json.load(open(FAILED)) if os.path.exists(FAILED) else {}

    todo = [w for w in words if slug(w) not in manifest and w not in SKIP and w not in failed]
    batch = todo[offset:offset + limit]
    print("total:", len(words), "| skip:", len([w for w in words if w in SKIP]),
          "| done:", len(manifest), "| failed:", len(failed), "| batch:", len(batch))

    ok, fail = 0, 0
    for i, w in enumerate(batch):
        s = slug(w)
        out = os.path.join(IMGDIR, s + ".png")
        try:
            url, src = with_retry(wiki_lead_image, HINTS.get(w, w.capitalize()))
            how = "wiki"
            if not url:
                url, src = with_retry(commons_search, HINTS.get(w, w))
                how = "commons"
            if not url:
                raise RuntimeError("no image found")
            make_square(out, with_retry(fetch_bytes, url))
            manifest[s] = {"word": w, "via": how, "source": src, "file": "images/%s.png" % s}
            ok += 1
            print("[%d/%d] OK(%s) %s" % (i + 1, len(batch), how, w))
        except Exception as e:
            failed[w] = str(e)[:150]
            fail += 1
            print("[%d/%d] FAIL %s: %s" % (i + 1, len(batch), w, str(e)[:80]))
        json.dump(manifest, open(MANIFEST, "w"), ensure_ascii=False, indent=1)
        json.dump(failed, open(FAILED, "w"), ensure_ascii=False, indent=1)
        time.sleep(1.0)
    print("done. ok=%d fail=%d manifest=%d failed_total=%d" % (ok, fail, len(manifest), len(failed)))

if __name__ == "__main__":
    main()
