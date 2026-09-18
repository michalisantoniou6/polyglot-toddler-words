# Polyglot Playroom

A phone-friendly multilingual collection of games for toddlers. The web game is
published with GitHub Pages and the Android app packages the same game in a
full-screen native shell.

## Tests

```sh
make test
```

## Android

The Android project lives in `android/`, targets Android 16 (API 36), and
supports Android 7 and newer. Opening that folder in Android Studio is the
easiest way to run it on a phone or prepare a signed Play Store bundle.

Every Android build automatically copies the current root `index.html` and
`assets/` into the app, so the website and native app stay on the same game
code.

```sh
cd android
./gradlew test lintDebug assembleDebug bundleRelease
```

The debug APK is written to
`android/app/build/outputs/apk/debug/app-debug.apk`. A Play Store upload requires
a private release upload key; do not commit that key or its passwords.
