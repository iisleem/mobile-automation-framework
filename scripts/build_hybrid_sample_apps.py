from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANDROID_SAMPLE = PROJECT_ROOT / "sample_apps" / "hybrid" / "android"
IOS_SAMPLE = PROJECT_ROOT / "sample_apps" / "hybrid" / "ios"
BUILD_ROOT = PROJECT_ROOT / "build" / "hybrid"
APPS_DIR = PROJECT_ROOT / "apps"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local hybrid sample apps into apps/.")
    parser.add_argument("--android", action="store_true", help="Build apps/HybridDemo.apk.")
    parser.add_argument("--ios", action="store_true", help="Build apps/HybridDemo.app.zip for iOS simulators.")
    parser.add_argument("--all", action="store_true", help="Build Android and iOS hybrid samples.")
    parser.add_argument("--android-sdk", help="Android SDK path. Defaults to ANDROID_HOME/ANDROID_SDK_ROOT.")
    args = parser.parse_args()

    build_android = args.all or args.android or not (args.android or args.ios)
    build_ios = args.all or args.ios or not (args.android or args.ios)

    APPS_DIR.mkdir(parents=True, exist_ok=True)
    if build_android:
        build_android_sample(args.android_sdk)
    if build_ios:
        build_ios_sample()
    return 0


def build_android_sample(android_sdk: str | None = None) -> Path:
    sdk_root = _android_sdk_root(android_sdk)
    platform_jar = _latest_android_jar(sdk_root)
    build_tools = _latest_build_tools(sdk_root)
    aapt2 = build_tools / "aapt2"
    d8 = build_tools / "d8"
    zipalign = build_tools / "zipalign"
    apksigner = build_tools / "apksigner"

    build_dir = BUILD_ROOT / "android"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    gen_dir = build_dir / "gen"
    classes_dir = build_dir / "classes"
    dex_dir = build_dir / "dex"
    gen_dir.mkdir(parents=True)
    classes_dir.mkdir(parents=True)
    dex_dir.mkdir(parents=True)

    unsigned_apk = build_dir / "HybridDemo-unsigned.apk"
    aligned_apk = build_dir / "HybridDemo-aligned.apk"
    output_apk = APPS_DIR / "HybridDemo.apk"
    manifest = ANDROID_SAMPLE / "AndroidManifest.xml"
    package_name = "dev.mobileframework.hybriddemo"

    _run(
        [
            str(aapt2),
            "link",
            "-o",
            str(unsigned_apk),
            "-I",
            str(platform_jar),
            "--manifest",
            str(manifest),
            "--java",
            str(gen_dir),
            "--min-sdk-version",
            "23",
            "--target-sdk-version",
            _api_level(platform_jar),
        ]
    )

    java_sources = [
        *(ANDROID_SAMPLE / "src").rglob("*.java"),
        *(gen_dir / package_name.replace(".", "/")).rglob("*.java"),
    ]
    _run(
        [
            "javac",
            "-source",
            "8",
            "-target",
            "8",
            "-bootclasspath",
            str(platform_jar),
            "-classpath",
            str(platform_jar),
            "-d",
            str(classes_dir),
            *[str(source) for source in java_sources],
        ]
    )

    class_files = [str(path) for path in classes_dir.rglob("*.class")]
    _run([str(d8), "--lib", str(platform_jar), "--output", str(dex_dir), *class_files])
    with zipfile.ZipFile(unsigned_apk, "a") as apk:
        apk.write(dex_dir / "classes.dex", "classes.dex")

    _run([str(zipalign), "-f", "4", str(unsigned_apk), str(aligned_apk)])
    keystore = _debug_keystore(build_dir)
    _run(
        [
            str(apksigner),
            "sign",
            "--ks",
            str(keystore),
            "--ks-key-alias",
            "androiddebugkey",
            "--ks-pass",
            "pass:android",
            "--key-pass",
            "pass:android",
            "--out",
            str(output_apk),
            str(aligned_apk),
        ]
    )
    print(f"Built Android hybrid sample: {output_apk}")
    return output_apk


def build_ios_sample() -> Path:
    xcodebuild = shutil.which("xcodebuild")
    if not xcodebuild:
        raise SystemExit("xcodebuild was not found. Install full Xcode to build the iOS hybrid sample.")

    derived_data = BUILD_ROOT / "ios"
    if derived_data.exists():
        shutil.rmtree(derived_data)
    project = IOS_SAMPLE / "HybridDemo.xcodeproj"
    _run(
        [
            xcodebuild,
            "-project",
            str(project),
            "-scheme",
            "HybridDemo",
            "-configuration",
            "Debug",
            "-sdk",
            "iphonesimulator",
            "-derivedDataPath",
            str(derived_data),
            "CODE_SIGNING_ALLOWED=NO",
            "build",
        ]
    )

    app_path = derived_data / "Build" / "Products" / "Debug-iphonesimulator" / "HybridDemo.app"
    if not app_path.exists():
        raise SystemExit(f"iOS build did not produce {app_path}")

    output_zip = APPS_DIR / "HybridDemo.app.zip"
    if output_zip.exists():
        output_zip.unlink()
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in app_path.rglob("*"):
            archive.write(path, app_path.name + "/" + path.relative_to(app_path).as_posix())
    print(f"Built iOS hybrid sample: {output_zip}")
    return output_zip


def _android_sdk_root(override: str | None) -> Path:
    candidates = [
        override,
        os.getenv("ANDROID_HOME"),
        os.getenv("ANDROID_SDK_ROOT"),
        str(Path.home() / "Library" / "Android" / "sdk"),
        str(Path.home() / "Android" / "Sdk"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise SystemExit("Android SDK was not found. Set ANDROID_HOME or pass --android-sdk.")


def _latest_android_jar(sdk_root: Path) -> Path:
    jars = sorted((sdk_root / "platforms").glob("android-*/android.jar"), key=lambda path: int(path.parent.name[8:]))
    if not jars:
        raise SystemExit(f"No Android platforms found under {sdk_root / 'platforms'}")
    return jars[-1]


def _latest_build_tools(sdk_root: Path) -> Path:
    versions = sorted((sdk_root / "build-tools").iterdir(), key=lambda path: tuple(int(part) for part in path.name.split(".")))
    for candidate in reversed(versions):
        if all((candidate / tool).exists() for tool in ("aapt2", "d8", "zipalign", "apksigner")):
            return candidate
    raise SystemExit(f"No complete Android build-tools folder found under {sdk_root / 'build-tools'}")


def _api_level(platform_jar: Path) -> str:
    return platform_jar.parent.name.removeprefix("android-")


def _debug_keystore(build_dir: Path) -> Path:
    keystore = build_dir / "debug.keystore"
    if keystore.exists():
        return keystore
    _run(
        [
            "keytool",
            "-genkeypair",
            "-keystore",
            str(keystore),
            "-storepass",
            "android",
            "-alias",
            "androiddebugkey",
            "-keypass",
            "android",
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "10000",
            "-dname",
            "CN=Android Debug,O=Android,C=US",
        ]
    )
    return keystore


def _run(command: list[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
