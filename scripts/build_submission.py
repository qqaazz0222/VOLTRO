#!/usr/bin/env python3
"""Build, align, sign, and verify a non-debuggable contest demo without storing signing secrets in Git."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--team", default="VOLTRO", help="filename team label; replace with your registered team name")
args = parser.parse_args()
if not re.fullmatch(r"[\w-]{1,48}", args.team):
    parser.error("Team name must contain only letters, digits, underscores, or hyphens (max 48 characters).")
env = dict(os.environ)
jdk = Path(env.get("JAVA_HOME", "/Applications/Android Studio.app/Contents/jbr/Contents/Home"))
if not (jdk / "bin/java").is_file():
    parser.error("Set JAVA_HOME to a supported JDK.")
env["JAVA_HOME"] = str(jdk)


def run(command, **kwargs):
    return subprocess.run([str(arg) for arg in command], check=True, env=env, **kwargs)


dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all", "--",
    "VOLTRO", "mock-data", "licenses", "scripts"], cwd=ROOT, text=True).strip()
if dirty:
    parser.error("Commit implementation and build scripts first so the APK has an exact source commit.")
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
sdk_env = env.get("ANDROID_HOME") or env.get("ANDROID_SDK_ROOT")
local_properties = ROOT / "VOLTRO/local.properties"
sdk_local = None
if local_properties.exists():
    sdk_local = next((line.removeprefix("sdk.dir=") for line in local_properties.read_text().splitlines() if line.startswith("sdk.dir=")), None)
sdk = Path(sdk_env or sdk_local or Path.home() / "Library/Android/sdk")
versions = [path for path in (sdk / "build-tools").iterdir() if re.fullmatch(r"\d+(\.\d+)+", path.name)]
tools = max(versions, key=lambda path: tuple(map(int, path.name.split("."))))

custom = [env.get(name) for name in ("VOLTRO_SIGNING_KEYSTORE", "VOLTRO_SIGNING_ALIAS", "VOLTRO_SIGNING_PASSWORD_FILE")]
if any(custom) and not all(custom):
    parser.error("Set all three VOLTRO_SIGNING_* variables for a custom key.")
demo_key = not all(custom)
if demo_key:
    # Kept outside the checkout, reusable for updates; never a Pleos production identity.
    key_dir = Path.home() / ".local/share/voltro/contest-signing"
    key_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(key_dir, 0o700)
    keystore = key_dir / "demo.p12"
    password_file = key_dir / "password"
    alias = "voltro-demo"
    if not keystore.exists():
        if not password_file.exists():
            with open(password_file, "x", opener=lambda path, flags: os.open(path, flags, 0o600)) as file:
                file.write(secrets.token_urlsafe(48))
        os.chmod(password_file, 0o600)
        run([jdk / "bin/keytool", "-genkeypair", "-keystore", keystore, "-storetype", "PKCS12",
             "-storepass:file", password_file, "-keypass:file", password_file, "-alias", alias,
             "-keyalg", "RSA", "-keysize", "3072", "-validity", "3650", "-dname", "CN=VOLTRO Contest Demo"])
        os.chmod(keystore, 0o600)
    if not password_file.exists():
        parser.error("Existing demo keystore has no password file; restore it or supply a custom key.")
else:
    keystore, alias, password_file = Path(custom[0]), custom[1], Path(custom[2])
    if not keystore.is_file() or not password_file.is_file():
        parser.error("Custom keystore and password file must exist.")

run(["./gradlew", ":app:assembleRelease", "--console=plain"], cwd=ROOT / "VOLTRO")
unsigned = ROOT / "VOLTRO/app/build/outputs/apk/release/app-release-unsigned.apk"
if not unsigned.is_file():
    raise SystemExit("Expected unsigned release APK was not generated.")
output_dir = ROOT / "apk"
output_dir.mkdir(exist_ok=True)
apk = output_dir / f"{args.team}_VOLTRO_release.apk"
with tempfile.TemporaryDirectory(prefix="voltro-sign-") as temporary:
    aligned = Path(temporary) / "aligned.apk"
    signed = Path(temporary) / "signed.apk"
    run([tools / "zipalign", "-f", "-p", "4", unsigned, aligned])
    run([tools / "apksigner", "sign", "--ks", keystore, "--ks-key-alias", alias,
         "--ks-pass", f"file:{password_file}",
         "--v1-signing-enabled", "false", "--v2-signing-enabled", "true", "--v3-signing-enabled", "true",
         "--v4-signing-enabled", "false", "--out", signed, aligned])
    verification = run([tools / "apksigner", "verify", "--verbose", "--print-certs", signed], capture_output=True, text=True).stdout
    # With minSdk 28, apksigner verifies the v3 path; v2 can be reported false because it is unused.
    if not re.search(r"Verified using v3 scheme[^\n]+true", verification):
        raise SystemExit("APK must verify with a v3 signature for all supported API 28+ devices.")
    run([tools / "zipalign", "-c", "-p", "4", signed])
    badging = run([tools / "aapt2", "dump", "badging", signed], capture_output=True, text=True).stdout
    if "application-debuggable" in badging or "testOnly='true'" in badging:
        raise SystemExit("Refusing to package a debuggable/testOnly APK.")
    package = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", badging)
    if package is None or package[1] != "com.qqaazz0222.voltro":
        raise SystemExit("Unexpected application ID.")
    fingerprint = re.search(r"Signer #1 certificate SHA-256 digest: (\w+)", verification)
    if fingerprint is None:
        raise SystemExit("No signing certificate fingerprint found.")
    apk.write_bytes(signed.read_bytes())

metadata = {"apk": apk.name, "application_id": package[1], "version_code": int(package[2]),
    "version_name": package[3], "source_commit": commit, "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
    "size_bytes": apk.stat().st_size, "certificate_sha256": fingerprint[1], "signing_identity": "local-contest-demo" if demo_key else "provided-key",
    "build_type": "release", "debuggable": False, "verified_signature_schemes": [3],
    "scope": "Mock routing/driving with optional Pleos Vehicle SDK snapshot; no real navigation or production certification"}
apk.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
apk.with_suffix(".sha256").write_text(f"{metadata['sha256']}  {apk.name}\n")
print(json.dumps(metadata, ensure_ascii=False, indent=2))
