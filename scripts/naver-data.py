#!/usr/bin/env python3
"""네이버 API로 키워드 실측 데이터 수집.

  python3 scripts/naver-data.py trend  <키워드>...   # DataLab 월별 검색 트렌드 (기본 최근 19개월,
                                                    #   --from=YYYY-MM-DD --to=YYYY-MM-DD 로 오버라이드)
  python3 scripts/naver-data.py blog   <키워드>...   # 블로그 문서수 + 상위 발행일
  python3 scripts/naver-data.py volume <키워드>...   # 검색광고 월간 검색량
  python3 scripts/naver-data.py ac     <키워드>...   # 검색창 자동완성 = 실제 타이핑 쿼리
  python3 scripts/naver-data.py kin    <키워드>...   # 지식iN = 실제 질문 제목+본문
  python3 scripts/naver-data.py cafe   <키워드>...   # 카페글 = 실제 하소연·후기 제목+본문
  python3 scripts/naver-data.py acdeep <키워드>...   # 자동완성 2단계
  python3 scripts/naver-data.py exists <문구>...     # 문구 실존 판정 (광고·트렌드·자동완성·문서수 교차)

자격증명은 .env에서 읽는다.
"""
import base64
import datetime
import hashlib
import hmac
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ENV = {}
for line in (Path(__file__).parent.parent / ".env").read_text().splitlines():
    if line.strip() and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip()

OPENAPI_HEADERS = {
    "X-Naver-Client-Id": ENV["NAVER_CLIENT_ID"],
    "X-Naver-Client-Secret": ENV["NAVER_CLIENT_SECRET"],
}


def _default_range():
    """기본 구간 = 이번 달 포함 최근 19개월. 시즌 판정에 전년 동월이 필요하다."""
    today = datetime.date.today()
    y, m = today.year, today.month - 18
    while m < 1:
        y, m = y - 1, m + 12
    return f"{y}-{m:02d}-01", today.isoformat()


def trend(keywords, start=None, end=None):
    """DataLab 검색어 트렌드. 그룹 5개씩 끊어 호출, 월별 상대지수 반환."""
    d_start, d_end = _default_range()
    start, end = start or d_start, end or d_end
    out = {}
    for i in range(0, len(keywords), 5):
        chunk = keywords[i : i + 5]
        body = json.dumps(
            {
                "startDate": start,
                "endDate": end,
                "timeUnit": "month",
                "keywordGroups": [{"groupName": k, "keywords": [k]} for k in chunk],
            }
        ).encode()
        req = urllib.request.Request(
            "https://openapi.naver.com/v1/datalab/search",
            data=body,
            headers={**OPENAPI_HEADERS, "Content-Type": "application/json"},
        )
        for r in json.load(urllib.request.urlopen(req))["results"]:
            out[r["title"]] = {d["period"][:7]: d["ratio"] for d in r["data"]}
        time.sleep(0.2)
    return out


def blog(keyword):
    """블로그 문서수 + 상위 10건 발행일·블로거."""
    url = "https://openapi.naver.com/v1/search/blog.json?" + urllib.parse.urlencode(
        {"query": keyword, "display": 10, "sort": "sim"}
    )
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=OPENAPI_HEADERS)))
    return {
        "total": d["total"],
        "top": [(i["postdate"], i["bloggername"], i["title"]) for i in d["items"]],
    }


def ac(keyword):
    """네이버 검색창 자동완성 제안어. 사람들이 실제로 타이핑하는 확장 쿼리.

    공식 오픈API가 아니라 검색창이 쓰는 공개 엔드포인트다(읽기 전용).
    """
    url = "https://ac.search.naver.com/nx/ac?" + urllib.parse.urlencode(
        {"q": keyword, "st": 100, "r_format": "json", "r_enc": "UTF-8", "q_enc": "UTF-8"}
    )
    d = json.load(urllib.request.urlopen(url))
    return [x[0] for grp in d.get("items", []) for x in grp if x and x[0] != keyword]


def _strip(s):
    s = re.sub(r"<[^>]+>", "", s)
    for a, b in [("&quot;", '"'), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&nbsp;", " ")]:
        s = s.replace(a, b)
    return s.strip()


def ac_deep(keyword, expand=3):
    """자동완성 2단계. 1단계 제안어 상위 몇 개를 다시 펼쳐 더 깊은 롱테일을 얻는다."""
    lv1 = ac(keyword)
    out = {"lv1": lv1, "lv2": {}}
    for s in lv1[:expand]:
        try:
            sub = [x for x in ac(s) if x not in lv1]
            if sub:
                out["lv2"][s] = sub
        except Exception:
            pass
        time.sleep(0.15)
    return out


def kin(keyword, display=10):
    """지식iN 검색. 질문 제목 + 본문(description)을 함께 얻는다.

    본문이 '사람들이 실제로 궁금해하는 내용'의 원문이다. 제목만으로는 상황이 안 보인다.
    """
    url = "https://openapi.naver.com/v1/search/kin.json?" + urllib.parse.urlencode(
        {"query": keyword, "display": display, "sort": "sim"}
    )
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=OPENAPI_HEADERS)))
    return {
        "total": d["total"],
        "questions": [_strip(i["title"]) for i in d["items"]],
        "items": [{"q": _strip(i["title"]), "body": _strip(i["description"])} for i in d["items"]],
    }


def cafe(keyword, display=10):
    """카페글 검색. 사업자가 실제 상황(매출·업종·견적)을 털어놓는 원문.

    지식iN이 '질문'이라면 카페글은 '하소연·후기'다. 니즈의 감정 온도가 여기 있다.
    """
    url = "https://openapi.naver.com/v1/search/cafearticle.json?" + urllib.parse.urlencode(
        {"query": keyword, "display": display, "sort": "sim"}
    )
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=OPENAPI_HEADERS)))
    return {
        "total": d["total"],
        "items": [{"q": _strip(i["title"]), "body": _strip(i["description"])} for i in d["items"]],
    }


def volume(keywords):
    """검색광고 키워드도구. 월간 PC/모바일 검색량·경쟁정도.

    hintKeywords는 공백을 허용하지 않으므로 제거해서 보낸다.
    """
    keywords = [k.replace(" ", "") for k in keywords]
    path = "/keywordstool"
    ts = str(int(time.time() * 1000))
    sig = base64.b64encode(
        hmac.new(ENV["NAVER_AD_SECRET"].encode(), f"{ts}.GET.{path}".encode(), hashlib.sha256).digest()
    ).decode()
    url = (
        "https://api.searchad.naver.com"
        + path
        + "?"
        + urllib.parse.urlencode({"hintKeywords": ",".join(keywords), "showDetail": "1"})
    )
    req = urllib.request.Request(
        url,
        headers={
            "X-Timestamp": ts,
            "X-API-KEY": ENV["NAVER_AD_API_KEY"],
            "X-Customer": ENV["NAVER_AD_CUSTOMER_ID"],
            "X-Signature": sig,
        },
    )
    return json.load(urllib.request.urlopen(req))["keywordList"]


def exists(keywords):
    """문구 실존 판정용 원자료. 4개 신호를 한 줄로 모은다(판정은 하지 않는다).

    광고 시스템이 그 문구를 모르고(relKeyword 부재) 자동완성도 비어 있고 DataLab이 전 구간
    결측이면, 그건 사람이 실제로 치는 검색어가 아니라 머릿속에서 만든 조합어다.
    """
    vol = {}
    for i in range(0, len(keywords), 5):  # keywordstool은 hintKeywords 5개까지
        for row in volume(keywords[i : i + 5]):
            vol[row["relKeyword"].replace(" ", "").upper()] = row
        time.sleep(0.2)
    tr = trend(keywords)
    out = []
    for k in keywords:
        v = vol.get(k.replace(" ", "").upper())
        months = tr.get(k, {})
        try:
            sug = ac(k)
        except Exception:
            sug = []
        out.append(
            {
                "keyword": k,
                "ad": (v["monthlyPcQcCnt"], v["monthlyMobileQcCnt"]) if v else None,
                "ac": sug,
                "trend_nonzero": sum(1 for r in months.values() if r > 0),
                "trend_months": len(months),
                "kin": kin(k, display=1)["total"],
                "blog": blog(k)["total"],
            }
        )
        time.sleep(0.2)
    return out


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "trend":
        dates = {a.split("=")[0]: a.split("=")[1] for a in args if a.startswith("--")}
        args = [a for a in args if not a.startswith("--")]
        for k, v in trend(args, dates.get("--from"), dates.get("--to")).items():
            print(k, json.dumps(v, ensure_ascii=False))
    elif cmd == "blog":
        for k in args:
            r = blog(k)
            print(f"\n### {k}  문서수={r['total']:,}")
            for d, b, t in r["top"]:
                print(f"  {d} | {b[:20]:20} | {t[:60]}")
    elif cmd == "ac":
        for k in args:
            print(f"\n### {k}")
            for s in ac(k):
                print("  ", s)
    elif cmd == "kin":
        for k in args:
            r = kin(k)
            print(f"\n### {k}  지식iN={r['total']:,}")
            for it in r["items"]:
                print("  Q:", it["q"])
                if it["body"]:
                    print("     ", it["body"][:180])
    elif cmd == "acdeep":
        for k in args:
            d = ac_deep(k)
            print(f"\n### {k}")
            for s in d["lv1"]:
                print("  ", s)
            for parent, subs in d["lv2"].items():
                print(f"   └ {parent}:")
                for s in subs:
                    print("       ", s)
    elif cmd == "volume":
        for k in volume(args):
            print(k["relKeyword"], k["monthlyPcQcCnt"], k["monthlyMobileQcCnt"], k["compIdx"])
    elif cmd == "cafe":
        for k in args:
            r = cafe(k)
            print(f"\n### {k}  카페글={r['total']:,}")
            for it in r["items"]:
                print("  T:", it["q"])
                if it["body"]:
                    print("     ", it["body"][:180])
    elif cmd == "exists":
        print(f"{'문구':28} {'광고(PC/모바일)':20} {'트렌드':10} {'자동완성':8} {'지식iN':>8} {'블로그':>10}")
        for r in exists(args):
            ad = f"{r['ad'][0]}/{r['ad'][1]}" if r["ad"] else "미인지"
            print(
                f"{r['keyword']:28} {ad:20} "
                f"{str(r['trend_nonzero']) + '/' + str(r['trend_months']):10} "
                f"{len(r['ac']):<8} {r['kin']:>8,} {r['blog']:>10,}"
            )
            if r["ac"]:
                print("   └ 자동완성:", " / ".join(r["ac"][:6]))
