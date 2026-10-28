[app]
title = LuttzzGrox AI
package.name = luttzzgrox
package.domain = com.luttzzgrox
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 2.0.0
requirements = python3,kivy==2.3.0,requests,urllib3,chardet,idna,certifi,openssl,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
