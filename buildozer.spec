[app]

# (str) Title of your application
title = 健康监测手表

# (str) Package name
package.name = healthmonitor

# (str) Package domain (needed for android/ios packaging)
package.domain = org.healthmonitor

# (str) Source code where the main.py lives
source.dir = .

# (str) Main entry point
source.main_py = health_watch_app.py

# (list) Source files to include (let empty to include all files)
source.include_exts = py,png,jpg,kv,atlas,json

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy==2.3.0,kivy-deps.angle==0.3.3,kivy-deps.glew==0.3.1,kivy-deps.gstreamer==0.3.3,kivy-deps.sdl2==0.6.0,pyjnius==1.6.1,certifi,hostpython2

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

#
# Android specific
#

# (list) Permissions
android.permissions = INTERNET,ACCESS_WIFI_STATE,ACCESS_NETWORK_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,CHANGE_WIFI_MULTICAST_STATE

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK will support.
android.minapi = 24

# (int) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 24

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a,armeabi-v7a

# (bool) Enables Android NDK's GL backends
android.gl_backend = glew

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2
