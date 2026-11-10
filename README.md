# LEGO DC Mighty Micros — PS Vita (GPT branch)

This branch is a clean rebuild of the earlier experimental project.

## What the workflow does

1. Installs VitaSDK and vitaGL on GitHub Actions.
2. Downloads the Android 1.7.1418 ZIP supplied for this build.
3. Extracts the APK contents and verifies the ARMv7 Unity/IL2CPP libraries.
4. Packages the extracted Android files into the VPK under the app's data directory.
5. Builds a VPK artifact named `mighty-micros-GPT-vpk`.

The commercial Android files are downloaded during the workflow and are **not committed to this repository**. The VPK artifact is retained for one day.

## Important status: not yet playable

The current VPK is a payload-packaging and diagnostic milestone, **not a working port**. It verifies that the expected Android libraries are installed and provides a minimal Vita application. It does not execute Unity, IL2CPP, or Android JNI.

The previous launcher called a nonexistent `kuBridgeLoadComponent()` function. kubridge does not provide a generic Android Unity/JNI runtime, so loading `libunity.so`, `libil2cpp.so`, and `libmain.so` as if they were ordinary Vita modules would not start this game.

A real port still needs a compatible ARM shared-object loader, Android/JNI compatibility layer, Unity platform glue, graphics translation, input/audio/filesystem replacements, and memory/performance work. This is a substantial reverse-engineering project; a successful VPK build alone does not prove the game runs.

## Install the diagnostic package

1. Download the VPK from the GitHub Actions artifact.
2. Transfer it to the Vita and install it with VitaShell.
3. Launch **LEGO DC Mighty Micros**. The screen colour indicates whether the three expected ARMv7 libraries were found.
4. Press START to exit.

## Build

Push to `GPT` or run **Build Mighty Micros Vita package** manually from Actions.
