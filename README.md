# LEGO DC Mighty Micros — PS Vita experiments

This repository is an experimental native wrapper for the Android ARMv7 release of LEGO DC Mighty Micros (Unity 2017.2 / IL2CPP).

## Current status

**Not playable yet.** The current branch is a first diagnostic build, not a completed Android compatibility layer.

The previous launcher called `kuBridgeLoadComponent()`, which is not a kubridge API and could not load these Android libraries. That call has been removed rather than leaving a launcher that cannot work.

The supplied APK's ARMv7 libraries were inspected:

- `libmain.so` exports `JNI_OnLoad`.
- `libunity.so` exports `JNI_OnLoad` and has a dynamic dependency on `libmain.so`.
- `libil2cpp.so` is the IL2CPP runtime/game code library and does not export `JNI_OnLoad`.

This means the libraries cannot simply be loaded independently in an arbitrary order. The next implementation stage is integrating an Android ELF loader (SoLoader/so_util), then resolving the Android/JNI imports and Unity startup requirements.

## Game files (not included)

Do not commit the APK, proprietary Unity assets, or extracted game libraries to this public repository.

Copy the extracted ARMv7 libraries and Unity data from your legally obtained APK to the Vita so the layout is:

```
ux0:data/mightymicros/
├── lib/armeabi-v7a/
│   ├── libmain.so
│   ├── libunity.so
│   └── libil2cpp.so
├── global-metadata.dat
└── assets/
    └── bin/Data/
        └── globalgamemanagers
```

The first diagnostic build checks for these files and writes its results to:

```
ux0:data/mightymicros/loader.log
```

It currently displays a blank diagnostic screen after checking the files. This is intentional: no Android library is executed yet.

## Build

GitHub Actions builds the Vita homebrew wrapper. The workflow no longer downloads an unrelated third-party `libil2cpp.so`; game binaries are supplied locally by the user and are never packaged into the public build.

A successful VPK build only confirms that the Vita wrapper compiles. It does **not** mean the Unity game is running.

## Target

Run the original Android game code on Vita with a compatibility layer, keeping the original Unity assets and gameplay. This is not a recreation of the game.
