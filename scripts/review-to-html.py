#!/usr/bin/env python3
"""세무사 감수 review.md → 인쇄·서명용 review.html 변환기 (의존성 없음).

용법: python3 scripts/review-to-html.py work/<slug>-review.md [더 많은 파일...]
인자 없이 실행하면 work/*-review.md 전체를 변환한다.
출력은 같은 위치의 .html (예: work/<slug>-review.html).
"""
import sys, os, re, html, glob

def esc(s):
    return html.escape(s, quote=False)

def inline(s):
    s = esc(s)
    # PASS / FAIL 태그 색상
    s = s.replace("[PASS]", '<span class="pass">PASS</span>')
    s = s.replace("[FAIL]", '<span class="fail">FAIL</span>')
    # **굵게**
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    # [텍스트](링크)  — 괄호가 있는 진짜 링크만
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    # 기입 빈칸: 밑줄 3개 이상 → 채우는 칸
    s = re.sub(r"_{3,}", '<span class="blank"></span>', s)
    # 체크박스 [ ] / [x]
    s = s.replace("[ ]", '<input type="checkbox">')
    s = re.sub(r"\[[xX]\]", '<input type="checkbox" checked>', s)
    return s

def convert(md):
    out, lst, ltype, tbl = [], False, None, []
    def close_list():
        nonlocal lst, ltype
        if lst:
            out.append(f"</{ltype}>")
            lst, ltype = False, None
    def close_table():
        """버퍼에 모인 마크다운 표를 <table>로 방출. 구분선(|---|)은 헤더 경계."""
        if not tbl:
            return
        rows, is_head = [], True
        for row in tbl:
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            if re.match(r"^[\s:|-]+$", "|".join(cells)):
                is_head = False
                continue
            tag = "th" if is_head else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
        out.append('<div class="tblwrap"><table>' + "".join(rows) + "</table></div>")
        tbl.clear()
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("|"):
            close_list(); tbl.append(line); continue
        close_table()
        if not line.strip():
            close_list(); continue
        if re.match(r"^---+$", line):
            close_list(); out.append("<hr>"); continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            close_list(); lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>"); continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", line.strip())
        if m:
            close_list()
            out.append(f'<p><img src="{html.escape(m.group(2))}" alt="{html.escape(m.group(1))}"></p>'); continue
        if line.startswith(">"):
            close_list()
            out.append(f"<blockquote>{inline(line.lstrip('> ').rstrip())}</blockquote>"); continue
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m:
            if not lst or ltype != "ul":
                close_list(); out.append("<ul>"); lst, ltype = True, "ul"
            out.append(f"<li>{inline(m.group(1))}</li>"); continue
        m = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if m:
            if not lst or ltype != "ol":
                close_list(); out.append("<ol>"); lst, ltype = True, "ol"
            out.append(f"<li>{inline(m.group(1))}</li>"); continue
        close_list(); out.append(f"<p>{inline(line)}</p>")
    close_table()
    close_list()
    return "\n".join(out)

CSS = """
:root{--ink:#1a1a1a;--muted:#666;--line:#e0e0e0;--accent:#1a5276}
*{box-sizing:border-box}
body{font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;
  color:var(--ink);line-height:1.7;max-width:820px;margin:0 auto;padding:48px 32px}
h1{font-size:1.6rem;border-bottom:2px solid var(--accent);padding-bottom:.4em;margin-top:1.4em}
h2{font-size:1.25rem;color:var(--accent);margin-top:1.8em}
h3{font-size:1.05rem;margin-top:1.4em}
p{margin:.6em 0}
ul,ol{margin:.5em 0;padding-left:1.5em}
li{margin:.25em 0}
blockquote{border-left:3px solid var(--accent);margin:.8em 0;padding:.6em 1em;color:#333}
hr{border:none;border-top:1px solid var(--line);margin:1.6em 0}
a{color:var(--accent);word-break:break-all}
strong{font-weight:700}
img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.88rem}
th,td{border:1px solid var(--line);padding:.45em .6em;text-align:left;vertical-align:top}
th{font-weight:600}
.tblwrap{overflow-x:auto}
.pass{color:#1e7e34;font-weight:700}
.fail{color:#c0392b;font-weight:700}
input[type=checkbox]{width:1.05em;height:1.05em;vertical-align:-2px;margin-right:.3em}
.blank{display:inline-block;min-width:140px;border-bottom:1px solid #999;height:1.1em;vertical-align:bottom}
.docnote{background:#fffbe6;border:1px solid #f0d97a;border-radius:6px;padding:.6em 1em;font-size:.9rem;color:#7a5d00;margin-bottom:1.5em}
@media print{body{padding:0}.docnote{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""

def wrap(title, body):
    return (f"<!doctype html>\n<html lang=\"ko\"><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{esc(title)}</title><style>{CSS}</style></head><body>"
            f"<div class=\"docnote\">세무사 감수용 문서입니다. 브라우저에서 체크·기입 후 인쇄(서명)하실 수 있습니다.</div>"
            f"{body}</body></html>\n")

def main(args):
    files = args or glob.glob(os.path.join("work", "*-review.md"))
    if not files:
        print("변환할 review.md 파일이 없습니다.", file=sys.stderr); return 1
    for f in files:
        with open(f, encoding="utf-8") as fh:
            md = fh.read()
        title_m = re.search(r"^#\s+(.*)$", md, re.M)
        title = title_m.group(1) if title_m else os.path.basename(f)
        out_path = os.path.splitext(f)[0] + ".html"
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(wrap(title, convert(md)))
        print(f"생성: {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
