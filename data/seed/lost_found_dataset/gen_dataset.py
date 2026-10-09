"""
Synthetic Lost & Found dataset generator.
Everything is fictional: campus layout, users, items and reports are randomly generated.
Run:  python gen_dataset.py --out ./lost_found_dataset --items 700 --seed 42
"""
import argparse, json, math, os, random
import datetime as dt
import pandas as pd

# ----------------------------------------------------------------------------------
# Fictional campus (x, y in metres). Replace with your own campus coordinates if needed.
# ----------------------------------------------------------------------------------
PLACES = {
    "Library": (0, 0), "Canteen": (120, 40), "Main Gate": (-200, -150), "Bus Stop": (-250, -180),
    "CS Block": (80, -110), "ECE Block": (150, -90), "Mechanical Block": (260, -200),
    "Auditorium": (-60, 160), "Playground": (-180, 220), "Boys Hostel": (400, 300),
    "Girls Hostel": (350, -300), "Parking Lot": (-120, -60), "Admin Block": (-20, -200),
    "Gym": (200, 200), "Stationery Shop": (30, -60),
}
SECURITY_DESK = ("Security Desk", (-20, -190))
ORIGIN_LAT, ORIGIN_LON = 12.9000, 77.5000  # arbitrary origin, fictional campus


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def xy_to_latlon(x, y):
    return (ORIGIN_LAT + y / 111320.0, ORIGIN_LON + x / (111320.0 * math.cos(math.radians(ORIGIN_LAT))))


NEIGHBOURS = {}
for _p in PLACES:
    _near = sorted((q for q in PLACES if q != _p), key=lambda q: dist(PLACES[_p], PLACES[q]))
    _within = [q for q in _near if dist(PLACES[_p], PLACES[q]) <= 200]
    NEIGHBOURS[_p] = _within or _near[:2]

COLOR_ALT = {
    "black": ["black", "dark", "dark grey"], "navy blue": ["navy blue", "dark blue", "blue"],
    "grey": ["grey", "gray", "silver-grey"], "red": ["red", "maroon-ish red", "red"],
    "green": ["green", "olive green", "dark green"], "maroon": ["maroon", "dark red", "wine red"],
    "blue": ["blue", "light blue", "sky blue"], "white": ["white", "off-white", "cream"],
    "silver": ["silver", "grey", "metallic"], "brown": ["brown", "tan", "dark brown"],
    "pink": ["pink", "light pink", "rose"], "orange": ["orange", "dark yellow", "orange"],
}

# ----------------------------------------------------------------------------------
# Category specs: public features (paraphrase lists) and hidden verification details
# ----------------------------------------------------------------------------------
CATS = {
    "backpack": dict(group="bags", words=["bag", "backpack", "sports bag", "rucksack"],
        brands=["Nike", "Adidas", "Puma", "Wildcraft", "American Tourister", "Skybags", "Safari"],
        colors=["black", "navy blue", "grey", "red", "green", "maroon"],
        feats=[["white logo", "logo in white on the front"], ["one side pocket", "a pocket on the side"],
               ["laptop compartment", "padded laptop section"], ["two front zips", "double zip on the front"],
               ["reflective strip", "reflective strip on the straps"], ["slightly torn near the strap", "small tear by the strap"]],
        hidden={"front_pocket_contents": ("What is inside the front pocket?", ["a blue pen and a charger", "two notebooks", "a water bottle", "a pair of earphones", "a calculator and a ruler", "a lunch box", "an umbrella", "tissues and a comb"]),
                "keychain": ("Describe the keychain attached to it.", ["a small panda keychain", "a metal bottle-opener keychain", "a red heart keychain", "no keychain", "a football keychain", "a brass ring with a bell"]),
                "inner_lining_color": ("What is the colour of the inner lining?", ["red", "black", "grey", "blue", "orange", "green"]),
                "tag_or_sticker": ("Is there any tag or sticker on it?", ["a name tag with initials", "a Spiderman sticker", "a bus pass holder", "no sticker", "a college fest tag", "a yellow ribbon on the zip"])}),
    "phone": dict(group="electronics", words=["phone", "mobile", "smartphone"],
        brands=["Samsung", "Redmi", "iPhone", "OnePlus", "Realme", "Vivo", "Motorola"],
        colors=["black", "blue", "white", "green", "silver", "red"],
        feats=[["transparent case", "clear back cover"], ["cracked screen corner", "crack on the top corner"], ["pop socket on the back", "ring holder on the back"], ["dual camera", "two cameras at the back"]],
        hidden={"wallpaper": ("What wallpaper is on the phone?", ["a mountain sunset", "a cricket player photo", "a family photo", "plain black", "an anime character", "a car photo", "a beach photo", "a cat photo"]),
                "back_sticker": ("What is stuck to the back of the phone?", ["a small smiley sticker", "no sticker", "a band logo sticker", "a ring holder", "a metro card in the cover", "a heart sticker"]),
                "case_type": ("What kind of case does it have?", ["transparent case", "black silicone case", "flip cover", "blue hard case", "green case with raised corners", "no case"]),
                "screen_damage": ("Is there any screen damage?", ["crack at top-left corner", "no cracks", "scratched tempered glass", "small chip on the bottom edge", "a dead pixel line"])}),
    "wallet": dict(group="accessories", words=["wallet", "purse", "card holder"],
        brands=["Fastrack", "Wildcraft", "Hidesign", "Woodland", "Puma"],
        colors=["black", "brown", "navy blue", "maroon", "grey"],
        feats=[["leather finish", "looks like leather"], ["metal logo", "small metal logo"], ["zip coin pocket", "zipper coin section"], ["worn edges", "frayed at the edges"]],
        hidden={"card_in_first_slot": ("Which card is in the first slot?", ["a bus pass", "a debit card", "a library card", "a college ID", "a metro card", "a gym membership card"]),
                "cash_range": ("Roughly how much cash is inside?", ["under 100 rupees", "100 to 500 rupees", "500 to 2000 rupees", "over 2000 rupees", "no cash"]),
                "photo_inside": ("Is there a photo inside?", ["a passport-size photo", "a family photo", "no photo", "a small deity picture", "a polaroid"]),
                "other_item": ("What other small item is inside?", ["a folded receipt", "a coin", "a movie ticket", "a visiting card", "a small key", "a library slip"])}),
    "water bottle": dict(group="drinkware", words=["bottle", "flask", "water bottle"],
        brands=["Milton", "Cello", "Borosil", "Decathlon", "Tupperware"],
        colors=["blue", "silver", "black", "green", "pink", "orange"],
        feats=[["steel body", "stainless steel"], ["flip cap", "flip-top lid"], ["1 litre size", "one litre bottle"], ["scratched paint", "paint worn off in places"]],
        hidden={"sticker": ("What sticker is on the bottle?", ["a football sticker", "no sticker", "a fest sticker", "a name label", "a cartoon sticker", "an NGO logo sticker"]),
                "dent_location": ("Where is the dent or scratch?", ["dent near the bottom", "dent on the cap", "no dent", "scratch on the side", "dent near the neck"]),
                "content": ("What is inside the bottle?", ["empty", "half filled with water", "a tea bag inside", "a lemon slice inside"]),
                "strap": ("What kind of strap or handle does it have?", ["a black strap", "no strap", "a loop on the cap", "a rope handle"])}),
    "laptop": dict(group="electronics", words=["laptop", "notebook computer"],
        brands=["Dell", "HP", "Lenovo", "Asus", "MacBook", "Acer"],
        colors=["black", "silver", "grey", "blue"],
        feats=[["15 inch screen", "fifteen inch display"], ["sticker on the lid", "stickers on the top cover"], ["backlit keyboard", "keyboard lights up"], ["black sleeve", "in a black laptop sleeve"]],
        hidden={"lid_sticker": ("What sticker is on the lid?", ["a GitHub sticker", "no sticker", "a Python sticker", "a band sticker", "a college club sticker", "a cartoon sticker"]),
                "wallpaper": ("What is the desktop wallpaper?", ["a mountain sunset", "a cricket player photo", "a family photo", "plain black", "an anime character", "a car photo", "a beach photo", "a cat photo"]),
                "charger_included": ("Was a charger with it?", ["yes, with a black adapter", "no charger", "yes, with an extension cord", "only the cable"]),
                "scratch": ("What marks does it have?", ["scratch on the left corner", "no visible scratch", "dent on the lid", "worn keys near the touchpad"])}),
    "earbuds case": dict(group="electronics", words=["earbuds case", "charging case", "airpods case", "small case"],
        brands=["boAt", "Realme", "AirPods", "Noise", "OnePlus"],
        colors=["white", "black", "blue", "pink"],
        feats=[["silicone cover", "rubber cover"], ["small LED light", "tiny indicator light"], ["lanyard hook", "hook for a lanyard"], ["scuffed lid", "scratches on the lid"]],
        hidden={"cover": ("What cover does the case have?", ["a plain case", "a silicone cover with a hook", "a cartoon silicone cover", "a glitter cover", "a leather pouch"]),
                "engraved": ("Is there any marking on it?", ["initial A", "initial S", "no marking", "a heart drawn with marker", "initial R", "a name label"]),
                "buds_present": ("Which earbuds are inside?", ["both buds present", "only the left bud", "only the right bud", "no buds"]),
                "charm": ("Is there a charm attached?", ["a tiny bear charm", "no charm", "a metal ring", "a beaded charm"])}),
    "keys": dict(group="accessories", words=["keys", "key bunch", "keychain"], brands=[""],
        colors=["silver", "black", "brown", "red"],
        feats=[["bike key with a rubber cover", "two-wheeler key with cover"], ["small padlock key", "tiny lock key"], ["steel ring", "metal ring"], ["plastic tag", "tag hanging from it"]],
        hidden={"key_count": ("How many keys are there?", ["two keys", "three keys", "four keys", "one key", "five keys"]),
                "charm": ("What charm is on the keychain?", ["a bell charm", "a plastic football", "a small torch", "a leather tag", "a bottle opener", "a cartoon figure"]),
                "tag_text": ("What is written on the tag?", ["a room number", "no tag", "a hostel name", "a red key cover", "a cycle lock key attached"]),
                "ring_type": ("What kind of ring holds the keys?", ["a steel ring", "a carabiner", "a plastic ring", "a split ring with a loop"])}),
    "umbrella": dict(group="accessories", words=["umbrella"], brands=["Popy", "Lifelong", "Fastrack", ""],
        colors=["black", "navy blue", "red", "green", "pink", "grey"],
        feats=[["folding type", "foldable umbrella"], ["automatic open button", "push-button opening"], ["printed edges", "pattern on the border"], ["bent rib", "one bent rib"]],
        hidden={"handle": ("What does the handle look like?", ["a curved wooden handle", "a black plastic handle", "a straight handle", "a handle with a rubber grip"]),
                "print": ("What is inside the canopy?", ["floral print inside", "plain inside", "a company logo", "a checked pattern", "a polka dot pattern"]),
                "damage": ("Is there any damage?", ["a bent rib", "no damage", "a torn edge", "a missing button"]),
                "strap_color": ("What strap does it have?", ["a red strap", "no strap", "a blue strap", "a black Velcro strap"])}),
    "calculator": dict(group="stationery", words=["calculator", "scientific calculator"], brands=["Casio", "Casio", "Citizen"],
        colors=["black", "blue", "grey"],
        feats=[["scientific type", "scientific calculator"], ["slide cover", "hard slide-on cover"], ["solar panel", "solar strip on top"], ["faded keys", "some keys faded"]],
        hidden={"model": ("What is the model number?", ["fx-991EX", "fx-82MS", "fx-991ES Plus", "fx-570ES"]),
                "name_marking": ("Is anything written on it?", ["name written on the back", "initials on the cover", "no marking", "a sticker with a roll number"]),
                "cover": ("What cover does it have?", ["a black slide cover", "no cover", "a scratched cover", "a blue flip cover"]),
                "damage": ("Is any key damaged?", ["a missing key cap", "no damage", "a cracked corner", "a faded 7 key"])}),
    "spectacles case": dict(group="accessories", words=["spectacle case", "glasses case", "specs box"], brands=["", "Titan", "Lenskart"],
        colors=["black", "brown", "blue", "red", "grey"],
        feats=[["hard shell", "hard case"], ["zip closure", "zippered"], ["soft pouch", "cloth pouch type"], ["small logo", "tiny logo on the front"]],
        hidden={"frame_color": ("What colour is the frame inside?", ["black frame", "silver frame", "brown frame", "transparent frame", "gold frame"]),
                "case_inside": ("What else is inside the case?", ["a cleaning cloth", "a spare nose pad", "no cloth", "a screwdriver kit", "a visiting card"]),
                "lens_condition": ("What is the lens condition?", ["a scratch on the right lens", "no scratches", "an anti-glare coating", "a slightly loose screw"]),
                "case_print": ("What is printed on the case?", ["a logo of an optical shop", "no logo", "a floral print", "a name label"])}),
    "power bank": dict(group="electronics", words=["power bank", "battery pack", "charger bank"],
        brands=["Mi", "Ambrane", "Realme", "Anker", "Syska"], colors=["black", "white", "blue", "silver"],
        feats=[["slim body", "thin power bank"], ["LED indicator", "four indicator lights"], ["USB-C port", "type-C input"], ["rubber finish", "matte rubber finish"]],
        hidden={"capacity": ("What capacity is printed on it?", ["10000 mAh", "20000 mAh", "5000 mAh", "10000 mAh slim", "20000 mAh with display"]),
                "cable": ("Is a cable attached?", ["a short white cable attached", "no cable", "a type-C cable", "a lightning cable"]),
                "sticker": ("Is there a sticker on it?", ["a name sticker", "no sticker", "a cartoon sticker", "a price sticker"]),
                "damage": ("Is there any damage?", ["a dent on one corner", "no damage", "a scratched back", "a loose port"])}),
    "smartwatch": dict(group="electronics", words=["watch", "smartwatch", "fitness band"],
        brands=["Noise", "boAt", "Fire-Boltt", "Apple Watch", "Amazfit"], colors=["black", "blue", "pink", "green", "white"],
        feats=[["square dial", "rectangular screen"], ["silicone strap", "rubber strap"], ["round dial", "circular screen"], ["scratch on the glass", "glass slightly scratched"]],
        hidden={"strap_color": ("What colour is the strap?", ["a black strap", "a blue strap", "an olive strap", "a pink strap", "a white strap", "a metal strap"]),
                "watch_face": ("What watch face is set?", ["a cricket watch face", "a digital face with steps", "an analog face", "a family photo face", "a plain black face"]),
                "damage": ("Is there any damage?", ["a scratch on the glass", "no damage", "a scuffed corner", "a loose strap"]),
                "extras": ("What else was with it?", ["the charging dock in a pouch", "no dock", "a spare strap in a pouch"])}),
    "notebook": dict(group="stationery", words=["notebook", "book", "record book"], brands=["Classmate", "Navneet", "Camlin", ""],
        colors=["blue", "red", "green", "orange", "black"],
        feats=[["spiral bound", "spiral notebook"], ["hard cover", "thick cover"], ["200 pages", "about two hundred pages"], ["sticky notes inside", "coloured sticky notes sticking out"]],
        hidden={"cover_doodle": ("What is on the cover?", ["a doodle of a cat", "a name label", "subject name only", "no marking", "a sticker of a planet", "a coffee stain"]),
                "subject": ("Which subject is it for?", ["Data Structures", "Operating Systems", "Engineering Maths", "DBMS", "Physics", "Machine Learning"]),
                "first_page": ("What is on the first page?", ["a timetable", "a name and roll number", "a cartoon", "an empty first page"]),
                "loose_item": ("Is there anything loose inside?", ["a loose sheet inside", "a pen clipped inside", "a sticky note inside", "nothing inside"])}),
    "charger": dict(group="electronics", words=["charger", "adapter with cable"], brands=["Samsung", "Apple", "Mi", "Realme", "Dell"],
        colors=["white", "black"],
        feats=[["long cable", "about 1.5 m cable"], ["fast charging type", "fast charger"], ["braided cable", "cloth braided cable"], ["two-pin plug", "two-pin adapter"]],
        hidden={"type": ("What kind of charger is it?", ["a 65W laptop charger", "a 20W phone charger", "a 33W fast charger", "a USB cable with adapter"]),
                "cable_wrap": ("How is the cable wrapped?", ["a velcro wrap", "a rubber band around the cable", "tape on the cable", "no wrap"]),
                "marking": ("Is there any marking?", ["a name written in marker", "initials", "no marking", "coloured tape on the cable"]),
                "damage": ("Is there any damage?", ["a frayed cable near the pin", "no damage", "a bent pin", "a cracked adapter body"])}),
}
CAT_NAMES = list(CATS)
GROUP_OF = {c: v["group"] for c, v in CATS.items()}
GROUP_MEMBERS = {}
for c, v in CATS.items():
    GROUP_MEMBERS.setdefault(v["group"], []).append(c)

HOURS_W = {7: 2, 8: 5, 9: 7, 10: 8, 11: 8, 12: 9, 13: 8, 14: 8, 15: 7, 16: 6, 17: 5, 18: 3, 19: 2, 20: 1}
START, END = dt.datetime(2026, 7, 20), dt.datetime(2026, 10, 4)


# ----------------------------------------------------------------------------------
def typo(rng, s):
    words = s.split()
    idx = [i for i, w in enumerate(words) if len(w) > 4 and w.isalpha()]
    if not idx:
        return s
    i = rng.choice(idx)
    w = words[i]
    j = rng.randrange(len(w) - 1)
    words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2:]
    return " ".join(words)


def pick_color(rng, color, noise):
    if rng.random() < noise:
        return rng.choice(COLOR_ALT.get(color, [color]))
    return color


def make_item(rng, item_id, cat=None, twin_of=None):
    if twin_of is None:
        cat = cat or rng.choice(CAT_NAMES)
        spec = CATS[cat]
        brand = rng.choice(spec["brands"])
        color = rng.choice(spec["colors"])
        nfeat = rng.randint(2, 3)
        feats = [rng.randrange(len(spec["feats"])) for _ in range(30)]
        feat_idx = list(dict.fromkeys(feats))[:nfeat]
        place = rng.choice(list(PLACES))
    else:
        cat, brand, color = twin_of["category"], twin_of["brand"], twin_of["color"]
        spec = CATS[cat]
        keep = twin_of["feat_idx"][:1]  # twin keeps one feature, differs in the rest
        others = [i for i in range(len(spec["feats"])) if i not in twin_of["feat_idx"]]
        rng.shuffle(others)
        feat_idx = keep + others[: max(1, len(twin_of["feat_idx"]) - 1)]
        place = twin_of["place"] if rng.random() < 0.6 else rng.choice([twin_of["place"]] + NEIGHBOURS[twin_of["place"]])
    hidden = {k: rng.choice(v[1]) for k, v in spec["hidden"].items()}
    return dict(item_id=item_id, category=cat, group=spec["group"], brand=brand, color=color,
                feat_idx=feat_idx, hidden=hidden, place=place)


def describe(rng, item, side):
    spec = CATS[item["category"]]
    owner = side == "lost"
    style = rng.choices(["detailed", "medium", "brief"], weights=[0.45, 0.35, 0.20] if owner else [0.30, 0.40, 0.30])[0]
    color = pick_color(rng, item["color"], 0.15 if owner else 0.35)
    word = item["category"] if (owner and rng.random() < 0.7) else rng.choice(spec["words"])
    if not owner and rng.random() < 0.4:
        word = rng.choice(spec["words"])
    brand_p = {"detailed": 0.85, "medium": 0.5, "brief": 0.1}[style] if owner else {"detailed": 0.7, "medium": 0.4, "brief": 0.05}[style]
    brand = item["brand"] if (item["brand"] and rng.random() < brand_p) else ""
    # owners sometimes misremember brand
    if owner and brand and rng.random() < 0.05:
        brand = rng.choice([b for b in spec["brands"] if b] or [brand])
    nf = {"detailed": 3, "medium": 1, "brief": 0}[style]
    feats = [rng.choice(spec["feats"][i]) for i in item["feat_idx"]]
    rng.shuffle(feats)
    feats = feats[:nf]
    core = " ".join(x for x in [color, brand, word] if x)
    if owner:
        text = f"I lost my {core}."
        if style == "brief":
            text = rng.choice([f"Lost {core}", f"{core} lost", f"Lost my {word}, it is {color}."])
    else:
        text = f"Found a {core}."
        if style == "brief":
            text = rng.choice([f"Found {core}", f"{core} found", f"Found a {word}."])
    if feats:
        text += " " + rng.choice(["It has", "Details:", "Features:"]) + " " + ", ".join(feats) + "."
    if owner and style == "detailed" and rng.random() < 0.4:
        text += " Please contact me if found."
    if not owner and style == "detailed" and rng.random() < 0.4:
        text += " Kept safely with me."
    lang = "en"
    if rng.random() < 0.08:
        lang = "hinglish"
        text = (rng.choice(["Mera {t} kho gaya hai.", "Kisi ko mila ho toh batao: {t}"]) if owner
                else rng.choice(["Mujhe mila hai: {t}", "Ye mila hai, owner ko batao: {t}"])).format(t=text[0].lower() + text[1:])
    if rng.random() < 0.10:
        text = typo(rng, text)
    return text, lang, style


def caption(rng, item):
    spec = CATS[item["category"]]
    f = rng.choice(spec["feats"][rng.choice(item["feat_idx"])])
    surf = rng.choice(["on a bench", "on a table", "on the floor", "on a desk"])
    brand = (item["brand"] + " ") if item["brand"] and rng.random() < 0.5 else ""
    return f"a {pick_color(rng, item['color'], 0.2)} {brand}{item['category']} {surf}, {f}"


def rand_time(rng):
    days = (END - START).days
    while True:
        d = START + dt.timedelta(days=rng.randrange(days))
        if d.weekday() == 6 and rng.random() < 0.8:
            continue
        break
    h = rng.choices(list(HOURS_W), weights=list(HOURS_W.values()))[0]
    return d.replace(hour=h, minute=rng.randrange(60))


def found_delay_hours(rng):
    r = rng.random()
    if r < 0.55:
        return rng.uniform(0.25, 4)
    if r < 0.85:
        return rng.uniform(4, 24)
    return rng.uniform(24, 96)


def generate(n_items, seed, out):
    rng = random.Random(seed)
    users = [f"U{i:04d}" for i in range(1, 801)]
    items, nid = [], 1
    for _ in range(n_items):
        it = make_item(rng, f"I{nid:04d}"); nid += 1
        it["twin_group"] = it["item_id"]
        items.append(it)
        if rng.random() < 0.25:  # hard-negative twin
            tw = make_item(rng, f"I{nid:04d}", twin_of=it); nid += 1
            tw["twin_group"] = it["item_id"]
            items.append(tw)
    groups = sorted({i["twin_group"] for i in items})
    rng.shuffle(groups)
    split_of = {g: ("train" if k < 0.70 * len(groups) else "val" if k < 0.85 * len(groups) else "test") for k, g in enumerate(groups)}

    lost_rows, found_rows, match_rows, item_rows = [], [], [], []
    li = fi = 1
    for it in items:
        twin = it["item_id"] != it["twin_group"]
        r = rng.random()
        fate = ("matched" if r < (0.85 if twin else 0.70) else "lost_only" if r < (0.93 if twin else 0.85) else "found_only")
        if twin and fate == "found_only":
            fate = "lost_only"
        owner, finder = rng.sample(users, 2)
        t_true = rand_time(rng)
        base_place = it["place"]
        lost_id = found_id = None
        if fate in ("matched", "lost_only"):
            lost_id = f"L{li:04d}"; li += 1
            text, lang, style = describe(rng, it, "lost")
            reported_place = base_place if rng.random() < 0.75 else rng.choice(NEIGHBOURS[base_place])
            conf = rng.choice(["high", "medium"]) if reported_place == base_place else "low"
            window = rng.choice([0.5, 1, 2, 4])
            t_rep = t_true + dt.timedelta(hours=rng.uniform(-window / 2, window / 2))
            cat_rep = it["category"] if rng.random() < 0.90 else rng.choice(GROUP_MEMBERS[it["group"]] + ["other"])
            has_img = rng.random() < 0.35
            lost_rows.append(dict(
                report_id=lost_id, user_id=owner, item_id=it["item_id"], split=split_of[it["twin_group"]],
                category_reported=cat_rep, group_reported=it["group"], description=text, language=lang, style=style,
                place_reported=reported_place, place_confidence=conf,
                latitude=round(xy_to_latlon(*PLACES[reported_place])[0], 6), longitude=round(xy_to_latlon(*PLACES[reported_place])[1], 6),
                lost_time_reported=t_rep.strftime("%Y-%m-%d %H:%M"), time_window_hours=window,
                report_time=(t_true + dt.timedelta(hours=rng.uniform(0.3, 10))).strftime("%Y-%m-%d %H:%M"),
                has_image=has_img, image_file="", image_caption=caption(rng, it) if has_img else ""))
        if fate in ("matched", "found_only"):
            found_id = f"F{fi:04d}"; fi += 1
            text, lang, style = describe(rng, it, "found")
            x = rng.random()
            if x < 0.08:
                found_place, handed = SECURITY_DESK[0], True
                coords = SECURITY_DESK[1]
            else:
                found_place = base_place if x < 0.78 else rng.choice(NEIGHBOURS[base_place])
                handed, coords = False, PLACES[found_place]
            delay = found_delay_hours(rng) if fate == "matched" else rng.uniform(0.25, 48)
            t_found = t_true + dt.timedelta(hours=delay)
            if t_found > END + dt.timedelta(days=2):
                t_found = END + dt.timedelta(days=rng.uniform(0, 2))
            keys = rng.sample(list(it["hidden"]), 3)
            hidden_found = {k: it["hidden"][k] for k in keys}
            cat_rep = it["category"] if rng.random() < 0.88 else rng.choice(GROUP_MEMBERS[it["group"]] + ["other"])
            has_img = rng.random() < 0.80
            found_rows.append(dict(
                report_id=found_id, user_id=finder, item_id=it["item_id"], split=split_of[it["twin_group"]],
                category_reported=cat_rep, group_reported=it["group"], description=text, language=lang, style=style,
                place_reported=found_place, handed_to_security=handed,
                latitude=round(xy_to_latlon(*coords)[0], 6), longitude=round(xy_to_latlon(*coords)[1], 6),
                found_time=t_found.strftime("%Y-%m-%d %H:%M"), report_time=(t_found + dt.timedelta(minutes=rng.randint(2, 180))).strftime("%Y-%m-%d %H:%M"),
                has_image=has_img, image_file="", image_caption=caption(rng, it) if has_img else "",
                hidden_details_json=json.dumps(hidden_found, ensure_ascii=False)))
        if fate == "matched":
            match_rows.append(dict(lost_id=lost_id, found_id=found_id, item_id=it["item_id"], split=split_of[it["twin_group"]]))
        item_rows.append(dict(item_id=it["item_id"], twin_group=it["twin_group"], is_twin=twin, split=split_of[it["twin_group"]],
                              category=it["category"], brand=it["brand"], color=it["color"],
                              public_features=" | ".join(CATS[it["category"]]["feats"][i][0] for i in it["feat_idx"]),
                              true_place=base_place, fate=fate, owner_user_id=owner if lost_id else "", lost_id=lost_id or "", found_id=found_id or "",
                              hidden_details_json=json.dumps(it["hidden"], ensure_ascii=False)))

    lost = pd.DataFrame(lost_rows); found = pd.DataFrame(found_rows)
    matches = pd.DataFrame(match_rows); items_df = pd.DataFrame(item_rows)

    # -------------------------- candidate pairs (for training/evaluating a ranker) --------------------------
    twin_of_item = {i["item_id"]: i["twin_group"] for i in items}
    found_by_split = {s: found[found.split == s] for s in ("train", "val", "test")}
    true_found = dict(zip(matches.lost_id, matches.found_id))

    def pair_row(l, f, label, neg_type, has_match):
        pl, pf = PLACES[l.place_reported], (SECURITY_DESK[1] if f.handed_to_security else PLACES[f.place_reported])
        tl = dt.datetime.strptime(l.lost_time_reported, "%Y-%m-%d %H:%M"); tf = dt.datetime.strptime(f.found_time, "%Y-%m-%d %H:%M")
        return dict(lost_id=l.report_id, found_id=f.report_id, label=label, negative_type=neg_type, lost_has_true_match=has_match,
                    category_match=l.category_reported == f.category_reported, group_match=l.group_reported == f.group_reported,
                    distance_m=round(dist(pl, pf), 1), time_diff_hours=round((tf - tl).total_seconds() / 3600, 2),
                    lost_text=l.description, found_text=f.description, split=l.split)

    pair_rows = []
    for l in lost.itertuples():
        pool = found_by_split[l.split]
        tf_id = true_found.get(l.report_id)
        used = set()
        if tf_id:
            f = found[found.report_id == tf_id].iloc[0]
            pair_rows.append(pair_row(l, f, 1, "positive", True)); used.add(tf_id)
        has = tf_id is not None
        tg = twin_of_item[l.item_id]
        twins = pool[(pool.item_id.map(twin_of_item) == tg) & (pool.item_id != l.item_id)]
        for f in twins.itertuples():
            pair_rows.append(pair_row(l, f, 0, "twin_hard_negative", has)); used.add(f.report_id)
        tl = dt.datetime.strptime(l.lost_time_reported, "%Y-%m-%d %H:%M")
        near = pool[(pool.group_reported == l.group_reported) & (~pool.report_id.isin(used))]
        near = near[near.found_time.map(lambda s: abs((dt.datetime.strptime(s, "%Y-%m-%d %H:%M") - tl).total_seconds()) < 72 * 3600)]
        near = near[near.place_reported.map(lambda p: p == SECURITY_DESK[0] or dist(PLACES[p], PLACES[l.place_reported]) < 350)]
        for f in near.sample(min(3, len(near)), random_state=rng.randrange(10**6)).itertuples():
            pair_rows.append(pair_row(l, f, 0, "same_group_nearby", has)); used.add(f.report_id)
        rest = pool[~pool.report_id.isin(used)]
        for f in rest.sample(min(2, len(rest)), random_state=rng.randrange(10**6)).itertuples():
            pair_rows.append(pair_row(l, f, 0, "random", has))
    pairs = pd.DataFrame(pair_rows)

    # -------------------------- ownership verification claims --------------------------
    item_hidden = {i["item_id"]: i["hidden"] for i in items}
    claim_rows, cid = [], 1

    def answer_text(v):
        return rng.choice([v, v, v.lower(), "I think " + v, v.replace("a ", "", 1) if v.startswith("a ") else v])

    for f in found.itertuples():
        hidden = json.loads(f.hidden_details_json)
        keys = list(hidden)
        cat = items_df.loc[items_df.item_id == f.item_id, "category"].iloc[0]
        owner = items_df.loc[items_df.item_id == f.item_id, "owner_user_id"].iloc[0]
        claimants = []
        if owner:
            claimants.append(("genuine_full" if rng.random() < 0.75 else "genuine_partial", owner))
        n_imp = (1 if rng.random() < 0.5 else 0) if owner else (1 if rng.random() < 0.6 else 0)
        for _ in range(n_imp):
            claimants.append(("impostor", rng.choice([u for u in users if u != owner and u != f.user_id])))
        for ctype, uid in claimants:
            row = dict(claim_id=f"C{cid:05d}", found_id=f.report_id, claimant_user_id=uid, claim_type=ctype, split=f.split)
            cid += 1
            ncorrect = 0
            bad_idx = rng.randrange(3) if ctype == "genuine_partial" else -1
            for n, k in enumerate(keys, 1):
                q, opts = CATS[cat]["hidden"][k]
                truth = hidden[k]
                if ctype == "impostor":
                    ans = rng.choice(opts)
                elif n - 1 == bad_idx:
                    ans = rng.choice(["I don't remember", rng.choice([o for o in opts if o != truth])])
                else:
                    ans = truth
                correct = ans == truth
                ncorrect += correct
                row[f"q{n}"] = q
                row[f"a{n}"] = answer_text(ans) if ans != "I don't remember" else ans
                row[f"correct{n}"] = correct
            row["n_correct"] = ncorrect
            row["decision_label"] = "approve" if ncorrect == 3 else "manual_review" if ncorrect == 2 else "reject"
            claim_rows.append(row)
    claims = pd.DataFrame(claim_rows)

    os.makedirs(out, exist_ok=True)
    items_df.to_csv(f"{out}/items_ground_truth.csv", index=False)
    lost.to_csv(f"{out}/lost_reports.csv", index=False)
    found.to_csv(f"{out}/found_reports.csv", index=False)
    matches.to_csv(f"{out}/matches_ground_truth.csv", index=False)
    pairs.to_csv(f"{out}/candidate_pairs.csv", index=False)
    claims.to_csv(f"{out}/verification_claims.csv", index=False)
    pd.DataFrame([dict(place=p, x_m=x, y_m=y, latitude=round(xy_to_latlon(x, y)[0], 6), longitude=round(xy_to_latlon(x, y)[1], 6))
                  for p, (x, y) in {**PLACES, SECURITY_DESK[0]: SECURITY_DESK[1]}.items()]).to_csv(f"{out}/campus_places.csv", index=False)
    return items_df, lost, found, matches, pairs, claims


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="lost_found_dataset"); ap.add_argument("--items", type=int, default=700); ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    res = generate(a.items, a.seed, a.out)
    names = ["items", "lost", "found", "matches", "pairs", "claims"]
    for n, d in zip(names, res):
        print(f"{n:8s} rows={len(d)}")
