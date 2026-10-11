#!/usr/bin/env python3
"""Convert Open Law Book (ספר החוקים הפתוח) wikitext pages to LawCodex Markdown.

Input:  _raw/il/pages/<pageid>.json   (written by il_fetch.py)
Output: <repo>/he/{basic-laws,laws/<year>,regulations/<year>,orders/<year>,other/<year>}/*.md

The Open Law Book marks up every law with a family of "ח:" templates
(ח:סעיף = section, ח:קטע1..4 = part/chapter/sign, ח:ת/ח:תת/... = paragraphs, etc.).
This script interprets that markup directly instead of scraping rendered HTML.

Usage: python il_convert.py [RAW_DIR] [REPO_DIR]
"""
import collections, datetime, html, json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "_raw", "il")
REPO = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..")
RETRIEVED = datetime.date.today().isoformat()
WS = "https://he.wikisource.org/wiki/"
UNKNOWN = collections.Counter()

# ---------------------------------------------------------------- template parsing

def find_close(s, i):
    """s[i:i+2] == '{{'; return index just after the matching '}}'."""
    depth = 0
    n = len(s)
    while i < n:
        if s.startswith("{{", i):
            depth += 1; i += 2; continue
        if s.startswith("}}", i):
            depth -= 1; i += 2
            if depth == 0:
                return i
            continue
        i += 1
    return -1


def split_params(body):
    """Split template body on top-level '|' (ignoring nested {{ }} and [[ ]])."""
    parts, cur, d1, d2, i = [], [], 0, 0, 0
    while i < len(body):
        if body.startswith("{{", i): d1 += 1; cur.append("{{"); i += 2; continue
        if body.startswith("}}", i): d1 -= 1; cur.append("}}"); i += 2; continue
        if body.startswith("[[", i): d2 += 1; cur.append("[["); i += 2; continue
        if body.startswith("]]", i): d2 -= 1; cur.append("]]"); i += 2; continue
        c = body[i]
        if c == "|" and d1 == 0 and d2 == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(c)
        i += 1
    parts.append("".join(cur))
    return parts


def parse_tpl(t):
    """'{{name|a|k=v}}' -> (name, [positional], {named})"""
    parts = split_params(t[2:-2])
    name = parts[0].strip()
    pos, named = [], {}
    for p in parts[1:]:
        m = re.match(r"^\s*([^=\[\]{}|<>\"]{1,20}?)\s*=(.*)$", p, re.S)
        if m and "{{" not in m.group(1):
            named[m.group(1).strip()] = m.group(2)
        else:
            pos.append(p)
    return name, pos, named


def arg(pos, i, default=""):
    return pos[i] if len(pos) > i else default


# ---------------------------------------------------------------- inline rendering

DROP_TPL = {"ח:מאגר2", "מיזמים", "ויקיפדיה", "מאגר חקיקה", "חוקי יסוד", "ריק", "ח:מאגר",
            "ח:התחלה", "ח:סוף", "ח:סוגר", "ח:מפריד", "ח:פתיח-התחלה", "ח:מבוא",
            "DEFAULTSORT", "ח:כותרת"}


def render_tpl(name, pos, named, mode):
    r = lambda x: inline(x, mode)
    if name in DROP_TPL or name.startswith("DEFAULTSORT"):
        return ""
    if name == "ח:פנימי":
        return r(arg(pos, 1) or arg(pos, 0))
    if name == "ח:חיצוני":
        target, text = arg(pos, 0).strip(), arg(pos, 1) or arg(pos, 0)
        if re.match(r"https?://", target):
            return link(r(text), target, mode)
        return r(text)
    if name == "ח:הערה":
        t = r(arg(pos, 0)).strip()
        return ("<i>%s</i>" if mode == "html" else "*%s*") % t if t else ""
    if name == "ח:תיבה":
        cite, url = r(arg(pos, 0)).strip(), arg(pos, 2).strip()
        tip = clean_title(r(arg(pos, 1)))
        return link(cite, url, mode, tip) if url.startswith("http") else cite
    if name in ("ש",):
        return "<br>"
    if name == "=":
        return "="
    if name == "!":
        return "|"
    if name in ("מוקטן", "מוגדל", "ממורכז", "שמאל", "ימין", "נוסח", "גופן", "לא לתרגום",
                "קטן", "גדול", "מרכז", "מודגש"):
        return r(arg(pos, 0))
    if name.startswith("דוכיווני") or name.startswith("טורים שווים") or name == "טור לשמאל":
        vals = [r(p).strip() for p in pos if p.strip()]
        return " — ".join(vals) if name == "טור לשמאל" or name.startswith("טורים") else " / ".join(vals)
    if name == "עמודות":
        return r(arg(pos, 1))
    if name == "טקסט תחתי":
        a, b = r(arg(pos, 0)).strip(), r(arg(pos, 1)).strip()
        return "%s (%s)" % (a, b) if b else a
    if name == "שבר":
        return "(%s)/(%s)" % (r(arg(pos, 0)).strip(), r(arg(pos, 1)).strip())
    if name.startswith("ח:ת"):  # paragraph marker inside a table cell / inline
        lab = [r(p).strip() for p in pos if p.strip()]
        return (" ".join(lab) + " ") if lab else ""
    if name in ("ח:סעיף", "ח:סעיף*"):
        lab = " ".join(x for x in (r(arg(pos, 0)).strip(), r(arg(pos, 1)).strip()) if x)
        return lab + " " if lab else ""
    if name.startswith("ח:קטע"):
        return r(arg(pos, 1)).strip()
    if name in ("-", "כ", "עמודות־התחלה", "עמודות-התחלה", "סוף", "עמודות־סוף", "עמודות-סוף"):
        return ""
    if name == "@":
        return "@"
    if name == "טקסט עילי ותחתי":
        a, b = r(arg(pos, 0)).strip(), r(arg(pos, 1)).strip()
        return "%s (%s)" % (a, b) if b else a
    if "תוכן" in named and not pos:
        return r(named["תוכן"])
    if name in ("לועזית", "לשמאל", "קוד", "אפור", "בלוק", "ממורעז", "ממוכז", "ממרכז"):
        return r(arg(pos, 0))
    if name == "צבע גופן":
        return r(arg(pos, 1))
    if name == "ח:דברי הסבר":
        t = r(arg(pos, 0)).strip()
        return ("<i>%s</i>" if mode == "html" else "*%s*") % t if t else ""
    if not pos and (name.startswith("חוקי ") or name.startswith("חוק ")):
        return ""  # navigation boxes
    UNKNOWN[name] += 1
    return r(pos[-1]) if pos else ""


def link(text, url, mode, tip=""):
    if not text:
        text = url
    if mode == "html":
        t = ' title="%s"' % html.escape(tip, quote=True) if tip else ""
        return '<a href="%s"%s>%s</a>' % (html.escape(url, quote=True), t, text)
    url = url.replace(" ", "%20").replace("(", "%28").replace(")", "%29")
    t = ' "%s"' % tip.replace('"', "'") if tip else ""
    return "[%s](%s%s)" % (text.replace("[", "\\[").replace("]", "\\]"), url, t)


def expand(s, mode):
    out, i = [], 0
    while True:
        j = s.find("{{", i)
        if j < 0:
            out.append(s[i:]); break
        out.append(s[i:j])
        k = find_close(s, j)
        if k < 0:
            out.append(s[j:]); break
        name, pos, named = parse_tpl(s[j:k])
        out.append(render_tpl(name, pos, named, mode))
        i = k
    return "".join(out)


def wikilinks(s, mode):
    def rep(m):
        target, _, text = m.group(1).partition("|")
        if re.match(r"\s*(קטגוריה|Category)\s*:", target, re.I):
            return ""
        if re.match(r"\s*(קובץ|File|תמונה|Image)\s*:", target, re.I):
            return "[תמונה: %s]" % target.split(":", 1)[1].strip()
        return text or target.lstrip(":")
    s = re.sub(r"\[\[([^\[\]]*)\]\]", rep, s)
    # external [url text]
    def ext(m):
        return link(m.group(2) or m.group(1), m.group(1), mode)
    return re.sub(r"\[(https?://[^\s\]]+)\s*([^\]]*)\]", ext, s)


def quotes(s, mode):
    b, it = ("<b>", "</b>"), ("<i>", "</i>")
    if mode != "html":
        b, it = ("**", "**"), ("*", "*")
    s = re.sub(r"'''''(.+?)'''''", lambda m: b[0] + it[0] + m.group(1) + it[1] + b[1], s)
    s = re.sub(r"'''(.+?)'''", lambda m: b[0] + m.group(1).strip() + b[1], s)
    s = re.sub(r"''(.+?)''", lambda m: it[0] + m.group(1).strip() + it[1], s)
    return s


def tags(s, mode):
    s = re.sub(r"<math[^>]*>(.*?)</math>", lambda m: "$" + m.group(1).strip() + "$", s, flags=re.S)
    s = re.sub(r"</?(span|div|wbr|nowiki|font|center|small|big|t)\b[^>]*>", "", s)
    s = re.sub(r"<br\s*/?>", "<br>", s)
    s = re.sub(r"<i>(.*?)</i>", (lambda m: "*" + m.group(1) + "*") if mode != "html" else (lambda m: m.group(0)), s, flags=re.S)
    s = re.sub(r"<s>(.*?)</s>", (lambda m: "~~" + m.group(1) + "~~") if mode != "html" else (lambda m: m.group(0)), s, flags=re.S)
    s = s.replace("&nbsp;", " ")
    return s


def inline(s, mode="md"):
    s = expand(s, mode)
    s = wikilinks(s, mode)
    s = quotes(s, mode)
    s = tags(s, mode)
    return s


# ---------------------------------------------------------------- tables

def render_table(t):
    t = inline(t, "html")
    t = re.sub(r"<(table|tr|td|th)\b([^>]*)>",
               lambda m: "<%s%s>" % (m.group(1), "".join(
                   " %s=\"%s\"" % (a, v) for a, v in re.findall(r'(colspan|rowspan)\s*=\s*"?(\d+)"?', m.group(2)))),
               t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    t = re.sub(r"\s*\n\s*(?=</?(td|th|tr|table|tbody|thead))", "\n", t)
    t = re.sub(r"(<(td|th)[^>]*>)\s+", r"\1", t)
    t = re.sub(r"\s+(</(td|th)>)", r"\1", t)
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    return "\n".join(lines)


# ---------------------------------------------------------------- block structure

def logical_lines(text):
    """Split into lines, merging lines inside unbalanced templates or <table> blocks."""
    out, buf, depth, tdepth = [], [], 0, 0
    for line in text.split("\n"):
        buf.append(line)
        depth += line.count("{{") - line.count("}}")
        tdepth += len(re.findall(r"<table\b", line)) - len(re.findall(r"</table>", line))
        if depth <= 0 and tdepth <= 0:
            out.append("\n".join(buf)); buf = []; depth = 0; tdepth = 0
    if buf:
        out.append("\n".join(buf))
    return out


LEAD = re.compile(r"^\s*\{\{\s*(ח:[^|}]+?)\s*(\||\}\})")


def lead_template(line):
    if not LEAD.match(line):
        return None
    j = line.find("{{")
    k = find_close(line, j)
    if k < 0:
        return None
    name, pos, named = parse_tpl(line[j:k])
    return name, pos, named, line[k:]


def clean_para(s):
    s = re.sub(r"[ \t]+", " ", s).strip()
    if re.match(r"^(#|>|[-+*] |=)", s):
        s = "\\" + s
    return s


def amend(named, pos, idx):
    a = arg(pos, idx).strip()
    if a.startswith("תיקון"):
        return a
    return ""


class Doc:
    def __init__(self):
        self.out = []
        self.levels = {}

    def emit(self, s):
        self.out.append(s)


def convert(text, title):
    meta = {"knesset_id": None, "sign_text": None}
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"</?(noinclude|includeonly|onlyinclude)>", "", text)
    text = re.sub(r"\[\[\s*(קטגוריה|Category)\s*:[^\]]*\]\]", "", text)
    text = re.sub(r"__[A-Zא-ת_]+__", "", text)
    m = re.search(r"\{\{ח:מאגר2?\|\s*(\d+)\s*\}\}", text)
    if m:
        meta["knesset_id"] = m.group(1)
    m = re.search(r"\{\{ח:כותרת\|(.*?)\}\}\n", text)
    if m:
        meta["title"] = clean_title(inline(m.group(1)))
    # remove table of contents (generated) -- heading plus law-toc div
    text = re.sub(r"\{\{ח:קטע\d\|\|תוכן עניינים\}\}\s*", "", text)
    text = remove_toc(text)
    # heading levels actually used
    used = sorted(set(int(x) for x in re.findall(r"\{\{ח:קטע(\d)\|", text)))
    hl = {lvl: min(2 + n, 6) for n, lvl in enumerate(used)}
    sec_level = min(2 + len(used), 6)

    out = []
    state = None  # 'pre' (publication box), 'intro'
    para = []

    def flush():
        if para:
            p = clean_para(" ".join(para))
            if p:
                out.append(p)
            para.clear()

    def handle(line):
        nonlocal state
        if not line.strip():
            flush(); return
        if "<table" in line and "</table>" in line:
            j = line.find("<table")
            k = line.rfind("</table>")
            handle(line[:j])
            flush()
            out.append(render_table(line[j:k + 8]))
            rest = line[k + 8:]
            if rest.strip():
                handle(rest)
            flush()
            return
        lt = lead_template(line)
        if lt:
            name, pos, named, rest = lt
            if name in ("ח:התחלה", "ח:סוף", "ח:מפריד", "ח:כותרת"):
                flush(); return
            if name == "ח:סוגר":
                flush(); state = None; return
            if name == "ח:פתיח-התחלה":
                flush(); state = "pre"
                if rest.strip():
                    para.append(inline(rest))
                return
            if name == "ח:מבוא":
                flush(); state = "intro"
                if rest.strip():
                    para.append(inline(rest))
                return
            if name.startswith("ח:קטע"):
                flush()
                lvl = int(name[-1]) if name[-1].isdigit() else 2
                ttl = inline(arg(pos, 1)).strip()
                am = amend(named, pos, 2)
                if not ttl or ttl.startswith("*"):
                    # note-only subtitle, e.g. "(סעיף 4א)"
                    if ttl: out.append(clean_para(ttl + ((" *(%s)*" % am) if am else "")))
                    return
                out.append("#" * hl.get(lvl, 6) + " " + re.sub(r"\s+", " ", ttl))
                if am:
                    out.append("*(%s)*" % am)
                if rest.strip():
                    para.append(inline(rest))
                return
            if name in ("ח:סעיף", "ח:סעיף*"):
                flush()
                num = inline(arg(pos, 0)).strip()
                ttl = inline(arg(pos, 1)).strip()
                am = amend(named, pos, 2)
                other = named.get("אחר", "").strip()
                head = " ".join(x for x in ((num + "." if num and not re.search(r"[.)]$", num) else num), ttl) if x)
                head = re.sub(r"\s+", " ", head)
                if head:
                    if sec_level < 6 or True:
                        out.append("#" * sec_level + " " + head)
                extra = " ".join(x for x in (inline(other).strip(), ("(%s)" % am) if am else "") if x)
                if extra:
                    out.append("*%s*" % extra)
                if rest.strip():
                    para.append(inline(rest))
                return
            if re.match(r"^ח:ת+$", name):
                flush()
                labels = [inline(p).strip() for p in pos if p.strip()]
                body = inline(rest).strip()
                para.append(" ".join(labels + [body]))
                return
            if name == "ח:חתימות":
                flush()
                meta["sign_text"] = arg(pos, 0)
                t = inline(arg(pos, 0)).strip()
                out.append("---")
                if t:
                    out.append(clean_para(t))
                if rest.strip():
                    para.append(inline(rest))
                return
        # list items (signatories etc.)
        m = re.match(r"^\s*([*#:]+)\s*(.*)$", line, re.S)
        if m and not line.lstrip().startswith("{{"):
            flush()
            item = inline(m.group(2)).strip()
            item = re.sub(r"\s*<br>\s*", " — ", item)
            if item:
                out.append("- " + re.sub(r"\s+", " ", item))
            return
        if re.match(r"^\s*-{4,}\s*$", line):
            flush(); out.append("---"); return
        para.append(inline(line))

    for line in logical_lines(text):
        handle(line)
    flush()
    # merge consecutive list items without blank lines
    md, prev_list = [], False
    for b in out:
        is_list = b.startswith("- ")
        if is_list and prev_list:
            md[-1] += "\n" + b
        else:
            md.append(b)
        prev_list = is_list
    body = "\n\n".join(md)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body, meta


def remove_toc(text):
    i = text.find('<div class="law-toc"')
    while i >= 0:
        depth, j = 0, i
        while True:
            a = text.find("<div", j); b = text.find("</div>", j)
            if b < 0:
                return text
            if 0 <= a < b:
                depth += 1; j = a + 4
            else:
                depth -= 1; j = b + 6
                if depth == 0:
                    break
        text = text[:i] + text[j:]
        i = text.find('<div class="law-toc"')
    return text


# ---------------------------------------------------------------- metadata helpers

MONTHS = {"ינואר": 1, "פברואר": 2, "מרס": 3, "מרץ": 3, "מארס": 3, "אפריל": 4, "מאי": 5, "יוני": 6,
          "יולי": 7, "אוגוסט": 8, "ספטמבר": 9, "אוקטובר": 10, "נובמבר": 11, "דצמבר": 12}


def greg_date(s):
    if not s:
        return None
    for m in re.finditer(r"(\d{1,2})\s+ב(%s)\s+(\d{4})" % "|".join(MONTHS), s):
        try:
            return datetime.date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1))).isoformat()
        except ValueError:
            pass
    return None


def clean_title(t):
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("**", "").replace("\\", "")
    return re.sub(r"\s+", " ", t).strip()


def title_year(t):
    m = re.findall(r"(?<!\d)(1[89]\d\d|20\d\d)(?!\d)", t)
    return int(m[-1]) if m else None


TRANS = {"א": "", "ב": "b", "ג": "g", "ד": "d", "ה": "h", "ו": "o", "ז": "z", "ח": "h", "ט": "t",
         "י": "i", "כ": "k", "ך": "k", "ל": "l", "מ": "m", "ם": "m", "נ": "n", "ן": "n", "ס": "s",
         "ע": "", "פ": "p", "ף": "f", "צ": "ts", "ץ": "ts", "ק": "k", "ר": "r", "ש": "sh", "ת": "t"}


def translit(t):
    t = re.sub(r"[֑-ׇ]", "", t)  # niqqud / cantillation
    t = re.sub(r",?\s*ה?תש[\"״׳'א-ת]*\s*[–-]\s*\d{4}", "", t)  # drop ", התשי״ח–1958"
    t = t.replace("וו", "v")
    t = re.sub(r"(^|[^\u05d0-\u05ea])ו", lambda m: m.group(1) + "v", t)
    t = re.sub(r"(^|[^\u05d0-\u05ea])י", lambda m: m.group(1) + "y", t)
    out = []
    for ch in t:
        if ch in TRANS:
            out.append(TRANS[ch])
        elif ch.isascii() and ch.isalnum():
            out.append(ch.lower())
        else:
            out.append("-")
    s = re.sub(r"-+", "-", "".join(out)).strip("-")
    return s


def classify(title):
    t = title.replace("־", "-")
    first = t.split()[0] if t.split() else ""
    if re.match(r"^חוק[- ]יסוד:", t):
        return "basic-law", "basic-laws"
    if first in ("חוק", "החוק"):
        return "law", "laws"
    if first == "פקודת" or first == "פקודה":
        return "ordinance", "laws"
    if first in ("דבר", "איחוד") or t.startswith("The Palestine") or t.startswith("The Termination"):
        return "order-in-council", "laws"
    if first.startswith("תקנות") or first in ("כללי", "כללים", "תקנון", "תקנה"):
        return "regulation", "regulations"
    if first in ("צו", "צווי"):
        return "order", "orders"
    return "other", "other"


REPEAL = re.compile(r"(בוטל|בוטלה|בוטלו|הוחלף|הוחלפה|הוחלפו|פקע|פקעה|פקעו|בטל|בטלה|בטלו)\b")


def detect_status(text, title):
    m = re.search(r"\{\{ח:מבוא\}\}(.*?)\{\{ח:סוגר\}\}", text, re.S)
    if m:
        intro = m.group(1)
        for note in re.findall(r"\{\{ח:הערה\|'''(.*?)'''", intro, re.S):
            plain = clean_title(inline(note))
            if REPEAL.search(plain[:400]):
                key = re.sub(r"[־\-–\s]", "", title)[:12]
                if re.sub(r"[־\-–\s]", "", plain).startswith(key) or re.match(r"^(חוק|תקנות|צו|פקודה|פקודת)\s+(זה|זו|אלה)", plain):
                    return "repealed", plain
    return "in_force", None


def yq(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------- main

def main():
    pdir = os.path.join(RAW, "pages")
    files = sorted(os.listdir(pdir), key=lambda f: int(f.split(".")[0]))
    stats = collections.Counter()
    used_paths = {}
    index = []
    for fn in files:
        pg = json.load(open(os.path.join(pdir, fn)))
        rev = pg["revisions"][0]
        text = rev["slots"]["main"]["content"]
        if not text.strip() or "{{ח:" not in text:
            stats["skipped-nonlaw"] += 1
            continue
        pagetitle = pg["title"]
        body, meta = convert(text, pagetitle)
        title = meta.get("title") or pagetitle
        typ, top = classify(title if classify(title)[0] != "other" else pagetitle)
        status, note = detect_status(text, title)
        date = greg_date(meta.get("sign_text"))
        year = title_year(title) or (int(date[:4]) if date else None) or title_year(pagetitle)
        kid = meta["knesset_id"]
        ident = kid or "ws%d" % pg["pageid"]
        slug = translit(pagetitle)[:80].strip("-") or "law"
        name = "%s-%s.md" % (ident, slug)
        if top == "basic-laws":
            rel = os.path.join("he", top, name)
        else:
            rel = os.path.join("he", top, str(year) if year else "undated", name)
        if rel in used_paths:
            rel = rel[:-3] + "-ws%d.md" % pg["pageid"]
        used_paths[rel] = 1
        fm = ["---",
              "title: " + yq(title),
              "identifier: " + yq(ident)]
        if kid:
            fm.append("knesset_law_id: " + yq(kid))
        fm += ["type: " + typ, "jurisdiction: il", "language: he"]
        if date:
            fm.append("date: " + date)
        if year:
            fm.append("year: %d" % year)
        fm.append("consolidation_date: " + rev["timestamp"][:10])
        fm.append("status: " + status)
        if note:
            fm.append("status_note: " + yq(note[:300]))
        fm.append("source: " + yq(WS + pagetitle.replace(" ", "_")))
        fm.append("source_revision: " + yq("https://he.wikisource.org/w/index.php?oldid=%d" % rev["revid"]))
        if kid:
            fm.append("official_record: " + yq(
                "https://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawPrimary.aspx?lawitemid=%s" % kid))
        fm += ["consolidation: unofficial",
               "license: " + yq("CC BY-SA 4.0 (Wikisource contributors); statutory text public domain (Copyright Act 2007 s.6)"),
               "retrieved: " + RETRIEVED, "---", ""]
        md = "\n".join(fm) + "\n# " + title + "\n\n" + body.strip() + "\n"
        md = unicodedata.normalize("NFC", md)
        path = os.path.join(REPO, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        stats[top] += 1
        stats["status:" + status] += 1
        index.append((rel, title, typ, status))
    json.dump(index, open(os.path.join(RAW, "index.json"), "w"), ensure_ascii=False)
    print(dict(stats))
    print("unknown templates:", UNKNOWN.most_common(40))


if __name__ == "__main__":
    main()
