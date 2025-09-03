
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
