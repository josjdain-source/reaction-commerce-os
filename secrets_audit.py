# -*- coding: utf-8 -*-
"""
secrets_audit.py — 공개 전 민감정보 감사 (generic).

이 저장소(repo) 안에 실제 키/토큰이 남아있는지, .env·미디어 원본이 gitignore 되는지 검사한다.
네트워크/실행 없음. deterministic. 공개 repo 커밋 전에 `verdict: SAFE` 를 확인하세요.

원칙: 변수 '이름'만 나오는 건 누설 아님. 실제 '값' 리터럴만 LEAK. 발견값은 마스킹만 저장.

CLI:  python secrets_audit.py   /   python secrets_audit.py --json
"""
import os
import re
import sys
import json
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "secrets_audit_report.json")

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
SKIP_FILES = {"secrets_audit_report.json"}
TEXT_EXT = {".py", ".json", ".md", ".html", ".js", ".txt", ".yml", ".yaml", ".env", ".cfg", ".ini"}
MEDIA_EXT = {".mp4", ".mov", ".mkv", ".webm", ".png", ".jpg", ".jpeg", ".gif", ".wav", ".mp3", ".m4a"}

SAFE_VALUE_HINTS = ("os.environ", "getenv", "env.get", "env[", "process.env", "${", "<",
                    "replace", "your_", "example", "여기", "xxxx", "mock", "placeholder",
                    "...", "***", "없음", "none")
SECRET_LIKE = re.compile(r"^[A-Za-z0-9._\-/=:,]{8,}$")
TOKEN_SIGNATURES = [
    ("Facebook/Graph 토큰", re.compile(r"\bEAA[A-Za-z0-9]{15,}\b")),
    ("Instagram 토큰", re.compile(r"\bIGA[A-Za-z0-9]{15,}\b")),
    ("Instagram 토큰(IGQV)", re.compile(r"\bIGQV[A-Za-z0-9_\-]{15,}\b")),
    ("Bearer 토큰", re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}")),
]
ASSIGN_RE = re.compile(
    r"""(?ix)(coupang_access_key|coupang_secret_key|ig_access_token|ig_user_id|
        access[_-]?key|secret[_-]?key|client_secret|api[_-]?key|auth[_-]?token|
        password|x-?api-?key)\s*["']?\s*[:=]\s*["']([^"']+)["']""")
AUTH_RE = re.compile(r"""(?i)authorization["']?\s*[:=]\s*["']([^"']{15,})["']""")
GITIGNORE_NEEDED = [".env", "*.mp4", "outputs/", "data/", "__pycache__/"]


def _mask(v):
    v = str(v)
    return (v[:2] + "***" + v[-2:]) if len(v) > 5 else "***"


def _is_safe_value(v):
    s = str(v).strip()
    if s == "":
        return True
    if any(h in s.lower() for h in SAFE_VALUE_HINTS):
        return True
    return not SECRET_LIKE.match(s)


def scan():
    leaks, media, n = [], [], 0
    for dp, dn, fn in os.walk(HERE):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f in SKIP_FILES:
                continue
            path = os.path.join(dp, f)
            ext = os.path.splitext(f)[1].lower()
            if ext in MEDIA_EXT:
                media.append(os.path.relpath(path, HERE))
                continue
            if ext not in TEXT_EXT and f != ".env":
                continue
            is_example = path.endswith(".env.example")
            n += 1
            try:
                lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
            except Exception:
                continue
            rel = os.path.relpath(path, HERE)
            for i, line in enumerate(lines, 1):
                for label, rx in TOKEN_SIGNATURES:
                    m = rx.search(line)
                    if m:
                        leaks.append({"file": rel, "line": i, "type": label,
                                      "severity": "HIGH", "masked": _mask(m.group(0))})
                for m in ASSIGN_RE.finditer(line):
                    name, val = m.group(1), m.group(2)
                    if is_example or _is_safe_value(val):
                        continue
                    leaks.append({"file": rel, "line": i, "type": f"{name} 값 하드코딩",
                                  "severity": "HIGH", "masked": _mask(val)})
                ma = AUTH_RE.search(line)
                if ma and not _is_safe_value(ma.group(1)):
                    leaks.append({"file": rel, "line": i, "type": "Authorization 값 하드코딩",
                                  "severity": "HIGH", "masked": _mask(ma.group(1))})
    return leaks, media, n


def _gitignore_status():
    gi = os.path.join(HERE, ".gitignore")
    present = set()
    if os.path.exists(gi):
        present = {l.strip() for l in open(gi, encoding="utf-8") if l.strip() and not l.startswith("#")}
    return {"present": sorted(present & set(GITIGNORE_NEEDED)),
            "missing": [x for x in GITIGNORE_NEEDED if x not in present]}


def audit():
    leaks, media, n = scan()
    gi = _gitignore_status()
    real = [l for l in leaks if l["severity"] == "HIGH"]
    env_ok = ".env" not in gi["missing"]
    rep = {"scanned_at": datetime.datetime.now().isoformat(timespec="seconds"),
           "summary": {"files_scanned": n, "leaks_high": len(real), "media_files": len(media)},
           "leaks": leaks, "gitignore": gi, "env_gitignored": env_ok, "media": media,
           "verdict": "SAFE" if (not real and env_ok) else "ACTION_NEEDED"}
    json.dump(rep, open(REPORT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return rep


def main():
    rep = audit()
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return
    s = rep["summary"]
    print(f"=== Secrets Audit — {rep['verdict']} ===")
    print(f"파일 {s['files_scanned']} 스캔 · HIGH 누설 {s['leaks_high']} · 미디어 {s['media_files']}\n")
    if [l for l in rep["leaks"] if l["severity"] == "HIGH"]:
        for l in rep["leaks"]:
            if l["severity"] == "HIGH":
                print(f"  HIGH  {l['type']}  {l['file']}:{l['line']}  ({l['masked']})")
    else:
        print("실제 키/토큰 값 없음 ✅")
    print(f"\ngitignore: 있음 {rep['gitignore']['present']} / 빠짐 {rep['gitignore']['missing']}")
    print("→", REPORT)


if __name__ == "__main__":
    main()
