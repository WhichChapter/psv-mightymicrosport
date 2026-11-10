# LEGO DC Mighty Micros — PS Vita (GPT branch)

This branch is the active Android-to-Vita port attempt. The original branch is left untouched.

## Current target

- Android package: LEGO DC Mighty Micros 1.7.1418
- Unity engine: 2017.2.1f1
- ABI: ARMv7 / armeabi-v7a
- Native libraries: `libmain.so`, `libunity.so`, and `libil2cpp.so`
- Vita title ID: `MTHM00001`

## What CI builds

The GitHub Actions workflow downloads the supplied APK-content ZIP, extracts its assets and ARMv7 libraries, inspects the ELF dependencies and Java entry points, and builds the Vita loader using VitaSDK-softfp.

Each successful run uploads the artifact `mighty-micros-port-build` (7-day retention), containing:

- `mighty_micros.vpk` — the Vita application.
- `mighty-micros-data.zip` — Android assets, ARMv7 libraries and APK metadata.
- `package.txt`, `exports.txt`, `java-entrypoints.txt`, `unity-strings.txt` — inspection reports.

The Android game files are not committed to this repository.

## Port work implemented

- Integrates TheFloW's `so_util` Android ARM shared-object loader framework and FalsoJNI.
- Loads `libunity.so` and `libil2cpp.so` as dependencies, then loads `libmain.so`; assigns SONAMEs and resolves relocations across the loaded modules.
- Hooks FalsoJNI `RegisterNatives` so Unity's registered JNI function pointers and signatures are captured.
- Calls the JNI entry points from `libmain.so` and `libunity.so`.
- Attempts the UnityPlayer startup sequence: `initJni`, WWW/WebRequest registration, graphics-state recreation, resume/focus, and repeated `nativeRender` calls.
- Uses the original Android app icon and banner in the Vita LiveArea.
- Writes runtime diagnostics to `ux0:data/mightymicros.log`.

## Important status: experimental, not confirmed playable

A successful VPK build only proves that the Vita application compiles. The game has **not yet been confirmed running on Vita hardware**.

The current JNI startup still uses placeholder Android `Context` and `Surface` objects. Unity may therefore stop during initialization or graphics setup. FalsoJNI also needs game-specific Java method/field implementations, and Android input, audio, asset and EGL behaviour still need verification and fixes.

The next milestone is to run the VPK on hardware, inspect `ux0:data/mightymicros.log`, then implement the exact missing Java/Android calls and Unity surface lifecycle reported by the game.

## Test installation

1. Download both `mighty_micros.vpk` and `mighty-micros-data.zip` from a successful GitHub Actions artifact.
2. Extract the **contents** of `mighty-micros-data.zip` into `ux0:data/mightymicros/`. The resulting paths must include `ux0:data/mightymicros/assets/` and `ux0:data/mightymicros/lib/armeabi-v7a/`.
3. Ensure the Vita's kubridge kernel plugin is installed and loaded.
4. Install `mighty_micros.vpk` with VitaShell and launch **LEGO DC Mighty Micros**.
5. If it fails or displays a black screen, retrieve `ux0:data/mightymicros.log` from the Vita and use it to guide the next compatibility fixes.

## Build

Push to branch `GPT` or manually run **Mighty Micros Android-to-Vita port** in GitHub Actions.
