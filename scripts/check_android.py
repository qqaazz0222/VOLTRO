#!/usr/bin/env python3
"""Run instrumented journeys and verify the runner output, even if Gradle reports false success."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--serial", required=True, help="adb device serial")
mode = parser.add_mutually_exclusive_group()
mode.add_argument("--backend", action="store_true", help="also test localhost:8000 FastAPI via emulator host")
mode.add_argument("--pleos-vehicle", action="store_true", help="only test real Vehicle SDK reads on a Pleos emulator")
mode.add_argument("--roads", action="store_true", help="one explicit live OSRM/map/replay test; requires internet")
mode.add_argument("--pleos-layout", action="store_true", help="only verify readable text and unwrapped controls on a wide Pleos window")
mode.add_argument("--capture-guide", action="store_true", help="capture the real Pleos app windows and live road flow; requires Pleos Vehicle service and internet")
args = parser.parse_args()
env = dict(os.environ)
jdk = Path("/Applications/Android Studio.app/Contents/jbr/Contents/Home")
if "JAVA_HOME" not in env and jdk.exists():
    env["JAVA_HOME"] = str(jdk)
sdk = Path(env.get("ANDROID_HOME", Path.home() / "Library/Android/sdk"))
adb = str(sdk / "platform-tools/adb") if (sdk / "platform-tools/adb").exists() else "adb"
subprocess.run(["./gradlew", ":app:assembleDebug", ":app:assembleDebugAndroidTest", "--console=plain"],
               cwd=ROOT / "VOLTRO", env=env, check=True)
for apk in ["debug/app-debug.apk", "androidTest/debug/app-debug-androidTest.apk"]:
    subprocess.run([adb, "-s", args.serial, "install", "-r", "-g", str(ROOT / "VOLTRO/app/build/outputs/apk" / apk)], check=True)
classes = ["com.qqaazz0222.voltro.MockJourneyTest", "com.qqaazz0222.voltro.DesignContrastTest", "com.qqaazz0222.voltro.ContestReadinessTest"]
if args.backend:
    classes.append("com.qqaazz0222.voltro.BackendJourneyTest")
if args.pleos_vehicle:
    classes = ["com.qqaazz0222.voltro.PleosVehicleIntegrationTest"]
if args.roads:
    classes = ["com.qqaazz0222.voltro.RoadJourneyTest"]
if args.pleos_layout:
    classes = ["com.qqaazz0222.voltro.WideLayoutTest"]
if args.capture_guide:
    classes = ["com.qqaazz0222.voltro.PleosGuideCaptureTest"]
user = subprocess.check_output([adb, "-s", args.serial, "shell", "am", "get-current-user"], text=True).strip()
command = [adb, "-s", args.serial, "shell", "am", "instrument", "--user", user, "-w", "-r", "-e", "class", ",".join(classes),
           "com.qqaazz0222.voltro.test/androidx.test.runner.AndroidJUnitRunner"]
result = subprocess.run(command, capture_output=True, text=True)
output = result.stdout + result.stderr
artifacts = ROOT / "artifacts"
artifacts.mkdir(exist_ok=True)
report = artifacts / f"instrumentation-{args.serial}.txt"
report.write_text(output)
print(output)
expected = 1 if args.pleos_vehicle or args.roads or args.pleos_layout or args.capture_guide else (9 if args.backend else 8)
match = re.search(r"OK \((\d+) tests?\)", output)
if result.returncode or not match or int(match[1]) != expected or "FAILURES!!!" in output:
    sys.exit(f"Android tests failed or did not run; inspect {report}")
print(f"Verified {expected} Android tests on {args.serial}")
