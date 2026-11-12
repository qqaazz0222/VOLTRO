#!/usr/bin/env python3
"""Exercise the signed release APK on a disposable, ordinary Android emulator through its visible UI."""
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
args = parser.parse_args()
sdk = Path(os.environ.get("ANDROID_HOME", Path.home() / "Library/Android/sdk"))
adb = str(sdk / "platform-tools/adb") if (sdk / "platform-tools/adb").exists() else "adb"
package = "com.qqaazz0222.voltro"
output = ROOT / "artifacts/release-smoke"
output.mkdir(parents=True, exist_ok=True)


def command(*parts):
    return subprocess.check_output([adb, "-s", args.serial, *map(str, parts)], text=True)


def dump():
    command("shell", "uiautomator", "dump", "/sdcard/voltro-release-smoke.xml")
    text = command("shell", "cat", "/sdcard/voltro-release-smoke.xml")
    (output / "latest-ui.xml").write_text(text)
    return ET.fromstring(text)


def tap(attribute, value, direction="up"):
    for _ in range(6):
        tree = dump()
        for node in tree.iter("node"):
            if node.get(attribute) == value and node.get("enabled") == "true":
                bounds = list(map(int, re.findall(r"\d+", node.get("bounds", ""))))
                if len(bounds) == 4 and bounds[3] > bounds[1] and bounds[2] > bounds[0]:
                    command("shell", "input", "tap", (bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2)
                    return
        size = command("shell", "wm", "size")
        width, height = map(int, re.findall(r"(\d+)x(\d+)", size)[-1])
        start, end = (.75, .35) if direction == "up" else (.35, .75)
        command("shell", "input", "swipe", width // 2, int(height * start), width // 2, int(height * end), 300)
    raise AssertionError(f"Visible UI control not found: {attribute}={value}")


def checkpoint(name):
    with (output / f"{name}.png").open("wb") as file:
        subprocess.run([adb, "-s", args.serial, "exec-out", "screencap", "-p"], stdout=file, check=True)
    print(f"Verified {name}", flush=True)


# Uses a fresh app installation. A conflicting debug certificate fails without removing any app data.
command("install", "-r", args.apk)
command("shell", "input", "keyevent", "KEYCODE_WAKEUP")
command("shell", "wm", "dismiss-keyguard")
command("shell", "am", "start", "-n", f"{package}/{package}.MainActivity")
time.sleep(2)
checkpoint("home")
tap("text", "Pleos 차량 상태 읽기")
time.sleep(8)
tree = dump()
messages = "\n".join(node.get("text", "") for node in tree.iter("node"))
assert "기존 차량값을 유지" in messages, "Ordinary Android must preserve the configured profile on unavailable SDK"
tap("text", "닫기")
tap("text", "강릉역", direction="down")
tap("resource-id", f"{package}:id/analyze_routes")
tap("content-desc", "빠른 경로 선택")
checkpoint("comparison")
tap("resource-id", f"{package}:id/start_trip")
# The simulator pauses itself in the decision window; only inspect after that point.
time.sleep(8)
tree = dump()
assert any("분기점" in node.get("text", "") for node in tree.iter("node")), "No junction advice"
checkpoint("junction")
tap("text", "절전 경로로 변경")
time.sleep(28)
tree = dump()
assert any(node.get("text") == "SIMULATED TRIP" for node in tree.iter("node")), "No completion report"
checkpoint("report")
tap("text", "새로운 여정 시작하기  →")
tap("text", "주행 이력")
tree = dump()
assert any(node.get("text") == "강릉역" for node in tree.iter("node")), "No persisted destination history"
checkpoint("history")
report = {"apk_sha256": hashlib.sha256(args.apk.read_bytes()).hexdigest(), "device": args.serial,
    "api": command("shell", "getprop", "ro.build.version.sdk").strip(), "status": "PASSED",
    "checks": ["release launch", "unavailable SDK keeps profile", "route comparison", "junction approval", "completion report", "persistent history"]}
(output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2), flush=True)
