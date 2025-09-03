[app]
title = Volleyball
package.name = volleyball
package.domain = org.yourname
version = 0.27

source.dir = .
source.include_exts = py,png
icon.filename = icon.png

requirements = python3, pygame
orientation = landscape
fullscreen = 1

# python-for-android / Android
p4a.bootstrap = sdl2
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# Use stable build-tools & auto-accept license
android.build_tools_version = 33.0.2
android.accept_sdk_license = True

# Use the SDK/NDK we install in the workflow
android.sdk_path = ./android-sdk
android.ndk_path = ./android-sdk/ndk/25.2.9519653

[buildozer]
log_level = 2
warn_on_root = 0
