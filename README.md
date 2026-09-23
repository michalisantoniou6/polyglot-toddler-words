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

## Child-development design guardrails

Toddler Arcade is designed for meaningful play rather than maximum engagement.

- Each game should have one clear learning or creative purpose, large direct
  actions, immediate feedback, and as little unrelated stimulation as possible.
- Avoid variable-reward loops, endless feeds, autoplay, streak pressure, and
  controls that encourage rapid novelty-seeking.
- The surprise dice is a single transition into play. After choosing a game it
  quietly disappears for an age-aware calm-play window (1 minute at age 2, 3
  minutes at age 3, and 5 minutes at ages 4–5). A parent can choose 1, 3, or 5
  minutes, or turn the window off. These are product defaults, not a claim that
  children have a fixed age-based attention span.
- Do not trap a child in an activity: the parent-controlled game sheet remains
  available, and the child can disengage with adult help.
- Screen play should supplement hands-on play and is best when a caregiver can
  occasionally join, talk, imitate, or connect the activity to the real world.

These rules follow the [American Academy of Pediatrics guidance on digital
ecosystems](https://publications.aap.org/pediatrics/article/157/2/e2025075321/206128/Digital-Ecosystems-Children-and-Adolescents),
[NAEYC guidance for choosing high-quality apps](https://www.naeyc.org/resources/pubs/yc/winter2023/rocking-and-rolling),
and the [Harvard Center on the Developing Child's play-based executive-function
guidance](https://developingchild.harvard.edu/resources/handouts-tools/brainbuildingthroughplay/).

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
