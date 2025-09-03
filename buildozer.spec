[app]
# ----- App metadata -----
title = Volleyball
package.name = volleyball
package.domain = org.yourname
version = 0.27

# ----- Project files -----
source.dir = .
source.include_exts = py,png
icon.filename = icon.png

# ----- Python / recipes -----
# Primary toolchain (fast path): Python 3.11 + pygame 2.6.1
# (The workflow will auto-edit this line to try fallbacks if needed.)
requirements = python3, pygame==2.6.1

# ----- Window -----
orientation = landscape
fullscreen = 1

# ----- p4a / Android -----
p4a.bootstrap = sdl2
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# Force stable build-tools to avoid preview-license prompts
android.build_tools_version = 33.0.2
android.accept_sdk_license = True

# Use the SDK/NDK installed by the workflow
android.sdk_path = ./android-sdk
android.ndk_path = ./android-sdk/ndk/25.2.9519653

# Permissions (pygame/SDL audio/network harmless)
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 0
