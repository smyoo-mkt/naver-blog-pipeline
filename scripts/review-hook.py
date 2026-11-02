#!/usr/bin/env python3
"""PostToolUse 훅: review.md가 저장되면 review.html을 자동 생성한다.
stdin으로 받은 훅 JSON에서 파일 경로를 읽어, *-review.md면 변환기를 돌린다.
jq 불필요(파이썬으로 파싱). 어떤 경우에도 exit 0으로 끝나 도구 실행을 막지 않는다.
"""
import sys, os, json, subprocess

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

resp = data.get("tool_response") or {}
inp = data.get("tool_input") or {}
path = resp.get("filePath") or inp.get("file_path") or ""

if path.endswith("-review.md") and os.path.exists(path):
    here = os.path.dirname(os.path.abspath(__file__))
    converter = os.path.join(here, "review-to-html.py")
    try:
        subprocess.run([sys.executable, converter, path], timeout=30)
    except Exception:
        pass

sys.exit(0)
