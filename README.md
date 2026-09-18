# Toddler Arcade

A phone-friendly multilingual collection of games for toddlers. The web game is
published with GitHub Pages and the Android app packages the same game in a
full-screen native shell.

## Install from the website

The GitHub Pages build is an installable Progressive Web App. On Android, open
the website in Chrome and choose **Install app**. On iPhone or iPad, open it in
Safari and choose **Share → Add to Home Screen**. After the first online visit,
the complete game and its local audio remain available offline. Opening the app
while online refreshes the cached game for the next offline session.

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
