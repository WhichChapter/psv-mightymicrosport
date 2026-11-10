#!/usr/bin/env python3
import os, sys, zipfile, shutil, io
from pathlib import Path

archive, out_dir, report_path = map(Path, sys.argv[1:4])
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "assets").mkdir(exist_ok=True)
(out_dir / "lib" / "armeabi-v7a").mkdir(parents=True, exist_ok=True)
lines = [f"Outer archive: {archive.name}"]
with zipfile.ZipFile(archive) as outer:
    entries = outer.namelist()
    apks = [n for n in entries if n.lower().endswith(".apk")]
    lines.append(f"Outer entries: {len(entries)}")
    lines.append("APK members: " + (", ".join(apks) if apks else "(none; treating ZIP as extracted APK contents)"))
    if not apks:
        for info in outer.infolist():
            if info.is_dir(): continue
            target = (out_dir / info.filename).resolve()
            if out_dir.resolve() not in target.parents:
                raise RuntimeError("Unsafe archive path: " + info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            with outer.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
    else:
        for apk_name in apks:
            lines.append(f"Inspecting {apk_name}")
            with outer.open(apk_name) as apk_bytes:
                with zipfile.ZipFile(io.BytesIO(apk_bytes.read())) as apk:
                    for info in apk.infolist():
                        if info.is_dir(): continue
                        name = info.filename.replace("\\", "/")
                        if name.startswith("/") or ".." in Path(name).parts:
                            raise RuntimeError("Unsafe APK path: " + name)
                        if name.startswith("lib/armeabi-v7a/") and name.endswith(".so"):
                            target = out_dir / name
                        elif name.startswith("assets/"):
                            target = out_dir / "assets" / name[len("assets/"):]
                        elif name in ("AndroidManifest.xml", "classes.dex") or name.startswith("META-INF/"):
                            target = out_dir / "apk-metadata" / Path(apk_name).stem / name
                        else:
                            target = out_dir / "assets" / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with apk.open(info) as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        if name.endswith(".so"):
                            lines.append(f"  native library: {name} ({info.file_size} bytes)")
so_files = sorted((out_dir / "lib" / "armeabi-v7a").glob("*.so"))
lines.append(f"ARMv7 shared libraries extracted: {len(so_files)}")
for so in so_files:
    lines.append(f"  {so.name}: {so.stat().st_size} bytes")
if not so_files:
    raise RuntimeError("No ARMv7 .so files found; check the APK ABI and ZIP contents.")
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(report_path.read_text())
