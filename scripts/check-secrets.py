"""인덱스/커밋의 브라우저 프로필과 Google 키를 바이너리까지 검사합니다.

키를 사용하거나 출력하지 않습니다. 다른 종류의 비밀은 Gitleaks로 검사합니다.
"""

import argparse
import re
import subprocess
import sys


PROFILE = re.compile(
    r"(^|/)(chrome-tmp[^/]*|edge-tmp[^/]*|cdp-profile)/"
    r"|(^|/)Default/(shared_proto_db/|Local Storage/leveldb/"
    r"|Network/Cookies(?:$|[-/])|Cookies(?:$|[-/])"
    r"|Login Data(?:$|[-/])|Web Data(?:$|[-/])|History(?:$|[-/]))"
)
GOOGLE_KEY = r"AIza[0-9A-Za-z_-]{35}"


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, check=False)


def check(staged=False, ref="HEAD"):
    if staged:
        paths = git("ls-files", "-z")
        target = ["--cached"]
    else:
        commit = git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
        if commit.returncode:
            print("검사할 커밋을 확인하지 못했습니다.", file=sys.stderr)
            return 2
        ref = commit.stdout.decode("ascii").strip()
        paths = git("ls-tree", "-r", "--name-only", "-z", ref)
        target = [ref]
    if paths.returncode:
        print("Git 파일 목록을 읽지 못했습니다.", file=sys.stderr)
        return 2
    blocked = [p for p in paths.stdout.split(b"\0")
               if p and PROFILE.search(p.decode("utf-8", "surrogateescape"))]
    # -a: 바이너리 LevelDB 로그도 텍스트로 검사합니다. -l: 내용 대신 경로만 출력합니다.
    found = git("grep", "--no-textconv", "-a", "-l", "-z", "-E",
                "-e", GOOGLE_KEY, *target, "--")
    if found.returncode not in (0, 1):
        print("Google 키 검사가 실패했습니다.", file=sys.stderr)
        return 2
    for path in blocked:
        print("브라우저 프로필 금지: " + repr(path.decode("utf-8", "replace")))
    for path in found.stdout.split(b"\0"):
        if path:
            print("Google 키 패턴 발견: " + repr(path.decode("utf-8", "replace")))
    if blocked or found.returncode == 0:
        return 1
    print("브라우저 프로필 및 Google 키 검사 통과")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--staged", action="store_true")
    selection.add_argument("--ref", default="HEAD")
    args = parser.parse_args()
    sys.exit(check(args.staged, args.ref))
