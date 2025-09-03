[app]
# ----- App metadata -----
title = Volleyball
package.name = volleyball
package.domain = org.yourname
version = 0.27
# (optional, purely cosmetic)
# numeric_version = 27

# ----- Project files -----
source.dir = .
source.include_exts = py,png
icon.filename = icon.png

# ----- Python / p4a requirements -----
requirements = python3, pygame

# ----- Orientation / window -----
orientation = landscape
fullscreen = 1

# ----- python-for-android (p4a) / Android -----
p4a.bootstrap = sdl2
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# Use a stable Build-Tools so no preview license prompt
android.build_tools_version = 33.0.2
# Auto-accept stable SDK licenses
android.accept_sdk_license = True

# Tell Buildozer to use the SDK/NDK installed by the GitHub Action
android.sdk_path = ./android-sdk
android.ndk_path = ./android-sdk/ndk/25.2.9519653

# (optional) permissions used by pygame/SDL for audio etc.
android.permissions = INTERNET

# ----- (optional) keep logs smaller -----
# logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 0
