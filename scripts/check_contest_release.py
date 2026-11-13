#!/usr/bin/env python3
"""Verify contest scenarios and real process-death recovery through signed-release UI.

Use a dedicated emulator with no conflicting debug certificate. Never clears app data.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--serial", required=True)
parser.add_argument("--apk", type=Path, default=ROOT / "apk/VOLTRO_VOLTRO_release.apk")
parser.add_argument("--record", action="store_true", help="record the actual emulator display as MP4")
args = parser.parse_args()
adb = str(Path(os.environ.get("ANDROID_HOME", Path.home() / "Library/Android/sdk")) / "platform-tools/adb")
package = "com.qqaazz0222.voltro"
output = ROOT / "artifacts/contest-release-smoke"
output.mkdir(parents=True, exist_ok=True)


def command(*parts):
    return subprocess.check_output([adb, "-s", args.serial, *map(str, parts)], text=True, timeout=30)


def dump():
    receipt = command("shell", "uiautomator", "dump", "/sdcard/voltro-contest.xml")
    if "dumped to" not in receipt:
        raise AssertionError("UI hierarchy was not refreshed; refusing to read a stale dump")
    content = command("shell", "cat", "/sdcard/voltro-contest.xml")
    (output / "latest-ui.xml").write_text(content)
    return ET.fromstring(content)


def texts(tree):
    return "\n".join(node.get("text", "") for node in tree.iter("node"))


def wait_text(value, timeout=40):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        tree = dump()
        if value in texts(tree):
            return tree
        time.sleep(.3)
    raise AssertionError(f"UI did not show {value}: {texts(tree)}")


def tap(value, attribute="text", direction="up"):
    width, height = map(int, re.findall(r"(\d+)x(\d+)", command("shell", "wm", "size"))[-1])
    for _ in range(9):
        for node in dump().iter("node"):
            if node.get(attribute) != value or node.get("enabled") != "true":
                continue
            bounds = list(map(int, re.findall(r"\d+", node.get("bounds", ""))))
            if len(bounds) == 4 and bounds[2] > bounds[0] and bounds[3] > bounds[1]:
                command("shell", "input", "tap", (bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2)
                return
        start, end = (.75, .35) if direction == "up" else (.35, .75)
        command("shell", "input", "swipe", width // 2, int(height * start), width // 2, int(height * end), 250)
    raise AssertionError(f"Missing enabled control: {attribute}={value}")


def screenshot(name):
    with (output / f"{name}.png").open("wb") as stream:
        subprocess.run([adb, "-s", args.serial, "exec-out", "screencap", "-p"], check=True, stdout=stream)
    print(f"Verified {name}", flush=True)


def prepare(label):
    tap("심사 시연 시나리오")
    tap(label)
    tap("시나리오 준비")
    wait_text("추천의 근거")


command("install", "-r", args.apk)
command("shell", "input", "keyevent", "KEYCODE_WAKEUP")
command("shell", "wm", "dismiss-keyguard")
command("shell", "am", "force-stop", package)
command("shell", "am", "start", "-n", f"{package}/.MainActivity")
wait_text("에너지 경로 도우미")
recording = None
checks = []
try:
    if args.record:
        recording = subprocess.Popen([adb, "-s", args.serial, "shell", "screenrecord", "--size", "720x1600",
            "--bit-rate", "2500000", "--time-limit", "0", "/sdcard/voltro-contest.mp4"])
    prepare("절전 전환 · 약 2.9 kWh 절약")
    screenshot("recommendation")
    checks.append("saving scenario and recommendation rationale")
    tap(f"{package}:id/start_trip", "resource-id")
    # Replay updates the hierarchy every 500ms; inspect once its decision pauses it.
    time.sleep(8)
    wait_text("절전 경로로 변경")
    screenshot("decision-before-restart")
    command("shell", "am", "force-stop", package)
    command("shell", "am", "start", "-n", f"{package}/.MainActivity")
    wait_text("중단된 주행 재생이 있습니다")
    tap("이전 재생 복구")
    wait_text("재생 일시정지")
    screenshot("recovered-paused-decision")
    checks.append("force-stop, relaunch, explicit recovery paused at pending decision")
    tap("절전 경로로 변경")
    time.sleep(29)
    wait_text("SIMULATED TRIP")
    tap("출발 경로 대비 계산상 변화")
    wait_text("2.9 kWh 감소")
    screenshot("simulated-saving-report")
    checks.append("approved switch and report: 2.9 kWh less, 15 extra minutes")
    tap("새로운 여정 시작하기  →")
    prepare("배터리 부족 · 출발 차단")
    tree = dump()
    start = next(n for n in tree.iter("node") if n.get("resource-id") == f"{package}:id/start_trip")
    assert start.get("enabled") == "false", "Low SOC must block replay"
    tap("출발 SOC 최소 60.4% 필요 · 배터리 에너지 28.3 kWh 추가 필요")
    screenshot("insufficient-soc-guidance")
    checks.append("low SOC blocks start and explains required departure charge")
    tap("← 목적지 다시 선택")
    prepare("경로 변경 실패 · 기존 경로 유지")
    tap(f"{package}:id/start_trip", "resource-id")
    time.sleep(8)
    wait_text("절전 경로로 변경")
    tap("절전 경로로 변경")
    time.sleep(1)
    # A failed change keeps the active route and pauses for explicit continuation.
    tree = wait_text("재생 일시정지")
    assert "빠른 경로" in texts(tree), texts(tree)
    assert "미지원" in texts(tree) or "실패" in texts(tree), texts(tree)
    screenshot("failed-switch-keeps-original")
    checks.append("failed route change preserves original route")
    tap("주행 취소")
    # Dialog has another cancellation action with the same label; next dump resolves it.
    tap("주행 취소")
    wait_text("에너지 경로 도우미")
    screenshot("cancelled-without-completion")
    checks.append("explicit cancellation returns Home")
    report = {"status": "PASSED", "apk_sha256": hashlib.sha256(args.apk.read_bytes()).hexdigest(),
        "device": args.serial, "api": command("shell", "getprop", "ro.build.version.sdk").strip(),
        "checks": checks, "video": "demo.mp4" if args.record else None}
    (output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
finally:
    if recording is not None:
        pids = subprocess.run([adb, "-s", args.serial, "shell", "pidof", "screenrecord"],
            capture_output=True, text=True).stdout.strip().split()
        if pids:
            command("shell", "kill", "-2", *pids)
        recording.wait(timeout=15)
        command("pull", "/sdcard/voltro-contest.mp4", output / "demo.mp4")
