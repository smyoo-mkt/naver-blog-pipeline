#!/usr/bin/env python3
"""에디토리얼 플랜 md → html 변환기 (표·코드펜스 지원, 의존성 없음).

용법: python3 scripts/plan-to-html.py work/editorial-plan-2026-08.md
출력은 같은 위치의 .html.

review-to-html.py와 별개다. 저쪽은 세무사 감수용(체크박스·서명란·인쇄),
이쪽은 계획 문서용(표·다크모드)이다.
"""
import html
import os
import re
import sys

CSS = """
:root{--ink:#1a1a1a;--muted:#666;--line:#e0e0e0;--accent:#1a5276}
*{box-sizing:border-box}
body{font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;
  color:var(--ink);line-height:1.7;max-width:900px;margin:0 auto;padding:48px 32px}
h1{font-size:1.6rem;border-bottom:2px solid var(--accent);padding-bottom:.4em;margin-top:0}
h2{font-size:1.25rem;color:var(--accent);margin-top:2em;border-bottom:1px solid var(--line);padding-bottom:.3em}
h3{font-size:1.02rem;margin-top:1.5em}
p{margin:.6em 0}
ul,ol{margin:.5em 0;padding-left:1.4em}
li{margin:.3em 0}
blockquote{border-left:3px solid var(--accent);margin:.8em 0;padding:.6em 1em;color:#333;font-size:.93rem}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.88rem}
th,td{border:1px solid var(--line);padding:.45em .6em;text-align:left;vertical-align:top}
th{font-weight:600}
.wrap{overflow-x:auto}
code{padding:.1em .35em;border-radius:3px;font-size:.9em}
pre{border:1px solid var(--line);border-radius:5px;padding:.9em 1em;overflow-x:auto;font-size:.85rem;line-height:1.55}
pre code{background:none;padding:0}
strong{font-weight:700}
del{color:var(--muted)}
"""


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"<em>\1</em>", s)
    return s


def convert(md):
    out, lines, i, lst = [], md.splitlines(), 0, None

    def close():
        nonlocal lst
        if lst:
            out.append(f"</{lst}>")
            lst = None

    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith("```"):
            close()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i], quote=False))
                i += 1
            out.append("<pre>" + "\n".join(buf) + "</pre>")
            i += 1
            continue
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            close()
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows = ["<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>"]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cs = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cs) + "</tr>")
                i += 1
            out.append('<div class="wrap"><table>' + "".join(rows) + "</table></div>")
            continue
        if not ln.strip():
            close()
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            close()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if ln.startswith(">"):
            close()
            out.append(f"<blockquote>{inline(ln.lstrip('> ').rstrip())}</blockquote>")
            i += 1
            continue
        m = re.match(r"^\s*[-*]\s+(.*)$", ln)
        if m:
            if lst != "ul":
                close()
                out.append("<ul>")
                lst = "ul"
            out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue
        m = re.match(r"^\s*\d+\.\s+(.*)$", ln)
        if m:
            if lst != "ol":
                close()
                out.append("<ol>")
                lst = "ol"
            out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue
        close()
        out.append(f"<p>{inline(ln)}</p>")
        i += 1
    close()
    return "\n".join(out)


def main(args):
    if not args:
        print("용법: python3 scripts/plan-to-html.py <plan.md>", file=sys.stderr)
        return 1
    for src in args:
        md = open(src, encoding="utf-8").read()
        m = re.search(r"^#\s+(.*)$", md, re.M)
        title = m.group(1) if m else os.path.basename(src)
        dst = os.path.splitext(src)[0] + ".html"
        with open(dst, "w", encoding="utf-8") as f:
            f.write(
                f'<!doctype html>\n<html lang="ko"><head><meta charset="utf-8">'
                f'<meta name="viewport" content="width=device-width,initial-scale=1">'
                f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>\n"
                f"{convert(md)}\n</body></html>\n"
            )
        print("생성:", dst)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
