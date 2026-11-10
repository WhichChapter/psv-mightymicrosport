# LEGO DC Mighty Micros — PS Vita (GPT branch)

This is the active Android-to-Vita port attempt. The original branch is left untouched.

## Target package

- Android package: LEGO DC Mighty Micros 1.7.1418
- Unity engine: 2017.2.1f1
- ABI: ARMv7 / armeabi-v7a
- Native libraries: `libmain.so`, `libunity.so`, and `libil2cpp.so`
- Vita title ID: `MTHM00001`

## Latest build

[Open GitHub Actions build #91](https://github.com/WhichChapter/psv-mightymicrosport/actions/runs/42905797908)

Build #91 successfully compiles the Vita loader, converts it to Sony ELF, and packages the VPK.

The `mighty-micros-port-build` artifact (7-day retention) contains:

- `mighty_micros.vpk` — Vita application (about 2.4 MB).
- `mighty-micros-data.zip` — Android assets, ARMv7 libraries and APK metadata (about 73 MB).
- `package.txt`, `exports.txt`, `imports.txt`, `java-entrypoints.txt`, `unity-strings.txt` — inspection reports.

A separate `mighty-micros-raw-elf` artifact contains the pre-SELF ELF and program-header report for build diagnostics. Commercial Android game files are downloaded during CI and are not committed to the repository.

## Port work implemented

- Integrates TheFloW's `so_util` Android ARM shared-object loader and FalsoJNI.
- Enables FalsoNDK for Android native-window, input, sensor, looper and asset APIs.
- Loads `libunity.so` and `libil2cpp.so` as dependencies, then loads `libmain.so`; assigns SONAMEs and resolves relocations across the modules.
- Captures Unity JNI `RegisterNatives` calls, including native method names, signatures and function addresses.
- Calls the JNI entry points from `libmain.so` and `libunity.so`.
- Attempts UnityPlayer startup in Android order: `libmain` JNI setup, Unity JNI setup, `initJni`, WWW/WebRequest registration, then graphics-state recreation, resume/focus and repeated `nativeRender` calls.
- Runs the graphics lifecycle and frame pump on a dedicated `UnityMain` Vita thread, rather than incorrectly driving Unity's render loop from the launcher thread.
- Writes FalsoJNI lookup warnings/errors to `ux0:data/mightymicros.log` as well as the console.
- Adds Android Surface-to-Vita-window and EGL compatibility shims.
- Uses the Android app icon and banner in the Vita LiveArea.
- Writes runtime diagnostics to `ux0:data/mightymicros.log`.
- Adjusts ELF segment placement so Vita SCE metadata can be inserted without overlapping the data segment.

## Important status: experimental, not confirmed playable

A successful VPK build proves that the loader compiles and packages; it does **not** prove that the Android game runs on Vita hardware.

The current JNI startup still uses placeholder Android `Context` and `Surface` objects. The EGL pbuffer function is currently an unsupported fallback. Java method/field behaviour, graphics, input, audio, assets and performance still need hardware testing and game-specific compatibility work.

The next milestone is to install the VPK with its data archive on a Vita, inspect `ux0:data/mightymicros.log`, and fix the first runtime failure. The dedicated UnityMain thread is a lifecycle correction based on UnityPlayer's Android startup model; it is not yet hardware-verified.

## Test installation

1. Download both files from the successful GitHub Actions artifact.
2. Extract the **contents** of `mighty-micros-data.zip` into `ux0:data/mightymicros/`. The resulting paths must include `ux0:data/mightymicros/assets/` and `ux0:data/mightymicros/lib/armeabi-v7a/`.
3. Ensure the Vita's kubridge kernel plugin is installed and loaded.
4. Install `mighty_micros.vpk` with VitaShell and launch **LEGO DC Mighty Micros**.
5. If it crashes or stays black, retrieve `ux0:data/mightymicros.log` from the Vita and share it for the next compatibility fixes.

## Build

Push to branch `GPT` or manually run **Mighty Micros Android-to-Vita port** in GitHub Actions.
