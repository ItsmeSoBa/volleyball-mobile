
[app]
title = Volleyball
package.name = volleyball
package.domain = org.yourname
source.dir = .
source.include_exts = py,png
icon.filename = icon.png
version = 0.27
requirements = python3, pygame
orientation = landscape
fullscreen = 1
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# ✅ force stable build-tools so no preview license is needed
android.build_tools_version = 33.0.2
# ✅ auto-accept license (for stable packages)
android.accept_sdk_license = True

# ✅ tell Buildozer to use the SDK/NDK we install in the workflow
android.sdk_path = ./android-sdk
android.ndk_path = ./android-sdk/ndk/25.2.9519653


# p4a options
p4a.bootstrap = sdl2
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 0
