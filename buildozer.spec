[app]
title = Murshid Al-Talib
package.name = murshidtalib
package.domain = org.zyadtarek
source.dir = .
source.include_exts = py,png,jpg,ttf
source.include_patterns = fonts/*
source.exclude_dirs = .github,bin,.buildozer
version = 1.0.0
requirements = python3,kivy==2.3.0,arabic-reshaper==3.0.0,python-bidi==0.4.2,six,setuptools,pyjnius,android
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.permissions =
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
