# -*- coding: utf-8 -*-
# 抽象词 AI 生图：逐词调用 image_generation 插件 CLI，跳过已有图，可断点续跑
# 用法: python3 gen_images.py [--limit N]
import json, os, re, subprocess, sys

ROOT = "/Users/naeemo/Workspace/word_game"
IMGDIR = os.path.join(ROOT, "images")
TOOL = "/Users/naeemo/Library/Application Support/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/image_generation/scripts/image_generation_tool.py"
STYLE = ("cute flat cartoon illustration for a children's English word flashcard, "
         "simple bold rounded shapes, bright friendly colors, clean soft light background, "
         "no text, no letters, no words, centered composition, for 4-year-old kids")

GEN = {
 "a": "one single shiny red apple on a small table, spotlight",
 "an": "one single brown egg in a small nest",
 "the": "one special shiny red apple with a golden star above it, spotlight",
 "about": "an open picture book with a cute dinosaur popping out of the pages",
 "after": "a little duckling walking behind its mother duck in a line",
 "again": "an excited child climbing the slide ladder for another turn, circular arrow symbol",
 "age": "a birthday cake with colorful candles",
 "all": "a whole round pizza with all slices together",
 "also": "a little child raising hand high saying me too, eager face",
 "always": "a smiling sun rising over a little house every morning",
 "and": "a cute cat and a cute dog sitting together as friends",
 "angry": "a red-faced child with puffed cheeks and steam puffing from ears",
 "any": "a table with several different fruits, a child hand reaching to pick one",
 "at": "a child standing at a red front door of a house",
 "bad": "a frowning child showing thumbs down",
 "be": "a calm little child sitting cross-legged with eyes closed and peaceful smile",
 "beautiful": "a beautiful rainbow over a flower meadow with butterflies",
 "because": "a dropped ice cream cone melting on the ground and a sad child looking at it",
 "before": "a mother duck walking behind her little duckling walking first in line",
 "behind": "a cute cat hiding behind a box, peeking out",
 "beside": "a cute cat sitting beside a box",
 "between": "a cute cat sitting between two boxes",
 "big": None,  # 已有
 "but": "a child standing between a sunny side and a rainy side of the scene, contrast",
 "by": "a child standing next to a big tree",
 "can": "a confident child flexing a little arm muscle, determined smile",
 "careful": "a child carrying a full glass of water very carefully, concentrated face",
 "clean": "a shiny white plate with soap bubbles and sparkles",
 "cold": None,
 "cool": "a relaxed child in front of an electric fan with hair gently blowing, happy",
 "cute": "an extremely cute kitten with big round sparkling eyes",
 "dear": "a child gently hugging a kind grandmother, small heart above",
 "difficult": "a child sweating while pushing a big rock up a steep hill",
 "dirty": "a happy little pig playing in a mud puddle, mud splashes",
 "do": "a child focused on doing a jigsaw puzzle",
 "down": "a child sliding down a playground slide, motion lines",
 "early": "a rooster crowing at sunrise, a child waking up in bed stretching",
 "easy": "a relaxed child easily stacking two toy blocks, confident smile",
 "every": "a row of children, each one holding a red balloon",
 "excited": "a child jumping high with excitement, arms up, party confetti",
 "famous": "a superstar lion on a stage with spotlights, waving to fans",
 "far": "a child looking through a telescope at a tiny house far away on a hill",
 "fast": "a cheetah running very fast with speed lines",
 "favourite": "a child hugging a beloved teddy bear, a red heart above",
 "fine": "a calm child showing OK hand sign with a gentle smile",
 "for": "a gift box with a red heart tag",
 "free": "a little bird flying freely out of an open birdcage into the blue sky",
 "from": "a child waving while walking away from a little house",
 "go": None,
 "good": "a smiling child showing one thumb up",
 "goodbye": "a child walking away and waving goodbye, warm sunset",
 "great": "a grinning child showing two thumbs up, small fireworks around",
 "happy": None,
 "hard": "a big gray rock with a toy hammer bouncing off it",
 "have": "a child proudly holding a teddy bear in arms",
 "he": "a cheerful little boy waving",
 "heavy": "a child struggling to lift a huge heavy box, knees bent, sweat drop",
 "hello": "a smiling child waving hello with open hand",
 "helpful": "a child helping mother carry a grocery bag",
 "her": "a smiling little girl with pigtails",
 "here": "a child pointing down at the ground at own feet, excited",
 "hi": "a cheerful child raising one hand high waving",
 "him": "a child handing a ball to a little boy",
 "his": "a little boy proudly holding his toy car",
 "home": None,
 "hot": None,
 "how": "a child looking up at a tall block tower, finger on cheek, wondering",
 "hungry": "a child rubbing a rumbling tummy, looking at a table of food",
 "I": "a child pointing at self with thumb, bright smile",
 "idea": "a glowing light bulb shining above a child's head",
 "ill": "a child resting in bed with a thermometer and a tissue box, blanket",
 "in": "a cute cat sitting inside an open box",
 "interesting": "a wide-eyed child reading a pop-up book, amazed face",
 "it": "a cute little puppy sitting",
 "its": "a cat licking its own paw",
 "kind": "a gentle child softly holding a small bird in hands",
 "last": "one single last cookie left on a plate",
 "late": "a child with a backpack running fast past a wall clock",
 "light": "a child easily lifting a big feather with one finger, smiling",
 "long": "a very long green snake stretched across the ground",
 "lot": "a toy box overflowing with a big pile of toys",
 "lovely": "an adorable bunny sitting among small flowers",
 "many": "a huge pile of many red apples",
 "may": "a polite child raising hand asking for permission",
 "me": "a child pointing at own chest, happy smile",
 "Miss": "a friendly young lady teacher with a pointer",
 "Mr": "a kind man with a mustache and a necktie",
 "Mrs": "a warm smiling woman with glasses and a hair bun",
 "Ms": "a young professional woman with a briefcase",
 "much": "a big glass jar filled to the top with colorful candies",
 "must": "a determined child tying shoelaces with a serious focused face",
 "my": "a child hugging own teddy bear tightly, proud",
 "near": "a cat standing very close to its food bowl",
 "never": "a child shaking head firmly with arms crossed in an X gesture at a plate of broccoli",
 "new": "a pair of shiny brand-new red shoes with sparkles",
 "next": "a line of ducklings, the second duckling highlighted with a small flag",
 "nice": "a friendly smiling sun shining over happy flowers",
 "no": "a red prohibition circle sign over a cookie",
 "not": "a child shaking head and waving a finger, refusing gently",
 "now": "a ringing alarm clock and a child jumping up right now",
 "o'clock": "a big round wall clock showing exactly three o'clock, a child pointing at it",
 "of": "a full glass of fresh milk",
 "off": "a table lamp switched off in a dim cozy room",
 "often": "a child on a swing under a tree, gentle motion lines",
 "OK": "a winking child making an OK hand sign",
 "old": "a kind old grandfather with a white beard and a walking cane",
 "on": "a cute cat sitting on top of a box",
 "or": "a child choosing between an apple and a banana on two plates, finger on chin",
 "our": "a happy family of four holding hands",
 "out": "a playful cat jumping out of a box",
 "over": "a bird flying over a little house",
 "pair": "a pair of cute matching mittens",
 "PE": "children doing stretching exercises with a whistle and a ball",
 "please": "a child with palms together asking politely, hopeful puppy eyes",
 "right": "a big green check mark with a happy nodding child",
 "sad": "a child with droopy eyes and a small tear, sitting",
 "she": "a cheerful little girl waving",
 "short": "a very short little pencil next to its tall pencil box",
 "should": "a child tidying up toys into a box",
 "sit": None,
 "slow": "a slow sleepy snail crawling with a tiny yawn",
 "small": "a tiny little mouse standing alone, emphasizing its tiny size",
 "so": "a child spreading arms wide showing something is sooo big",
 "some": "three cookies on a small plate",
 "sometimes": "a sky half sunny and half rainy, a child holding a half-open umbrella",
 "sorry": "a child bowing head apologetically with sad puppy eyes",
 "strong": "a strong elephant lifting a heavy log with its trunk",
 "such": "an amazed child with hands on cheeks looking at a huge rainbow",
 "sure": "a confident child nodding with a firm thumbs up",
 "sweep": None,
 "tall": "a tall giraffe reaching high leaves on a tree",
 "thank": "a child giving a flower to mother gratefully, small heart",
 "that": "a child pointing at a kite far away in the sky",
 "the": None,
 "their": "children standing with their dog, group portrait",
 "them": "a group of children and a dog standing together",
 "then": "a calendar page flipping, a child pointing at it",
 "there": "a child pointing toward a tree far over there",
 "these": "a child pointing at several flowers right in front",
 "they": "a group of four happy children standing together",
 "thin": "a very thin tall cactus in a small pot",
 "think": None,
 "this": "a child pointing at an apple right in front of them",
 "those": "a child pointing at birds flying far away",
 "time": "an alarm clock and an hourglass side by side",
 "tired": "a sleepy yawning child rubbing eyes",
 "to": "a child handing a gift to another child",
 "today": "a wall calendar with one day circled in red, a child pointing at it",
 "tomorrow": "a child sleeping in bed with a dream bubble showing a sunrise and a kite",
 "too": "a child wearing giant adult shoes way too big, funny look",
 "under": "a cute cat hiding under a table",
 "up": "a red balloon floating up into the sky, a child pointing up",
 "us": "a mother hugging two children together",
 "very": "an extremely tall wobbling stack of ice cream scoops",
 "wake": "a child waking up stretching in bed, morning sunlight, ringing alarm clock",
 "want": "a child reaching up for a toy on a shelf, eager wanting face",
 "warm": "a child in a cozy sweater sitting by a warm fireplace",
 "way": "a little winding path through green hills",
 "we": "two happy children hugging as best friends",
 "welcome": "an open front door with a welcome doormat, a child opening arms",
 "well": "a proud child wearing a gold medal, well done pose",
 "what": "a child shrugging with palms up and a puzzled face",
 "when": "a curious child looking up at a big wall clock",
 "where": "a child searching around with a big magnifying glass",
 "which": "a child choosing between two cups, finger on chin, thinking",
 "who": "a curious child peeking at a slightly open door",
 "whose": "a child holding up a single lost shoe with a puzzled face",
 "why": "a curious child looking up at the night stars with big wondering eyes",
 "will": "a determined child in a little superhero cape pointing forward",
 "window": "a cozy window with curtains, sunlight streaming in, a plant on the sill",
 "wish": "a child blowing dandelion seeds making a wish, eyes closed",
 "with": "a child walking hand in hand with a friendly dog",
 "wonderful": "an amazed child watching colorful magic sparkles and fireworks",
 "worry": "a worried child biting lip with a small rain cloud above head",
 "wrong": "a big red X mark with a confused child scratching head",
 "year": "one tree shown in four seasons: spring blossom, summer green, autumn orange, winter snow",
 "yes": "a happy child nodding with a green check mark beside",
 "yesterday": "a child looking through a photo album, nostalgic warm light",
 "you": "a child pointing forward at the viewer, friendly smile",
 "young": "a fluffy baby chick hatching from an egg",
 "your": "a hand offering a cookie toward the viewer",
}

def slug(w):
    return re.sub(r"[^a-z0-9]+", "_", w.lower()).strip("_")

def main():
    args = sys.argv[1:]
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 10**9
    todo = [w for w in sorted(GEN) if GEN[w] and not os.path.exists(os.path.join(IMGDIR, slug(w) + ".png"))]
    batch = todo[:limit]
    print("todo:", len(todo), "| batch:", len(batch))
    ok, fail = 0, []
    for i, w in enumerate(batch):
        out = os.path.join(IMGDIR, slug(w) + ".png")
        cmd = [sys.executable, TOOL, "generate",
               "--description", GEN[w] + ", " + STYLE,
               "--ratio", "1:1", "--resolution", "1K", "--output", out]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if r.returncode == 0 and os.path.exists(out):
                ok += 1
                print("[%d/%d] OK %s" % (i + 1, len(batch), w), flush=True)
            else:
                fail.append(w)
                print("[%d/%d] FAIL %s: %s" % (i + 1, len(batch), w, (r.stdout + r.stderr)[-200:]), flush=True)
        except Exception as e:
            fail.append(w)
            print("[%d/%d] FAIL %s: %s" % (i + 1, len(batch), w, str(e)[:120]), flush=True)
    print("done. ok=%d fail=%d remaining=%d" % (ok, len(fail), len(todo) - ok - len(fail)))
    if fail:
        print("failed words:", " ".join(fail))

if __name__ == "__main__":
    main()
