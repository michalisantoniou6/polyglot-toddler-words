import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android"
MANIFEST = (ANDROID / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
ACTIVITY = (
    ANDROID
    / "app/src/main/java/com/michalisantoniou/polyglotplayroom/MainActivity.java"
).read_text(encoding="utf-8")
BUILD = (ANDROID / "app/build.gradle").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AndroidAppRegressionTests(unittest.TestCase):
    def test_android_package_is_play_store_ready(self) -> None:
        self.assertIn('applicationId "com.michalisantoniou.polyglotplayroom"', BUILD)
        self.assertIn("compileSdk 36", BUILD)
        self.assertIn("targetSdk 36", BUILD)
        self.assertIn("minSdk 24", BUILD)
        self.assertRegex(BUILD, r'versionCode\s+8\b')
        self.assertRegex(BUILD, r'versionName\s+"1\.0\.7"')

    def test_android_can_apply_an_explicit_per_device_language(self) -> None:
        self.assertIn('EXTRA_PRIMARY_LANGUAGE = "primaryLanguage"', ACTIVITY)
        self.assertIn("applyPrimaryLanguageOverride(view)", ACTIVITY)
        self.assertIn("window.applyInstalledOnboardingLanguage", ACTIVITY)
        self.assertIn('"es".equals(language)', ACTIVITY)

    def test_android_launcher_uses_the_toddler_arcade_mascot(self) -> None:
        icon = ANDROID / "app/src/main/res/drawable-nodpi/toddler_arcade_icon.png"
        self.assertIn('android:icon="@drawable/toddler_arcade_icon"', MANIFEST)
        self.assertIn('android:roundIcon="@drawable/toddler_arcade_icon"', MANIFEST)
        self.assertTrue(icon.is_file())
        self.assertTrue(icon.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_build_copies_the_same_web_game_into_the_app(self) -> None:
        self.assertIn('tasks.register("syncWebAssets", Sync)', BUILD)
        self.assertIn('include "index.html"', BUILD)
        self.assertIn('include "languages.js"', BUILD)
        self.assertIn('include "assets/**"', BUILD)
        self.assertIn('dependsOn("syncWebAssets")', BUILD)
        self.assertIn("file:///android_asset/www/index.html", ACTIVITY)

    def test_app_is_full_screen_rotatable_and_keeps_game_state(self) -> None:
        self.assertNotIn("android:screenOrientation", MANIFEST)
        self.assertIn('android:configChanges="keyboardHidden|orientation|screenLayout|screenSize|smallestScreenSize|uiMode"', MANIFEST)
        self.assertIn("FLAG_KEEP_SCREEN_ON", ACTIVITY)
        self.assertIn("BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE", ACTIVITY)
        self.assertIn("webView.saveState(outState)", ACTIVITY)
        self.assertIn("webView.restoreState(savedInstanceState)", ACTIVITY)
        on_create = ACTIVITY[ACTIVITY.index("protected void onCreate"):ACTIVITY.index("public void onInit")]
        self.assertLess(on_create.index("setContentView(webView)"), on_create.index("showImmersivePlayArea"))

    def test_android_back_gesture_uses_the_games_navigation_history(self) -> None:
        self.assertIn("registerOnBackInvokedCallback", ACTIVITY)
        self.assertIn("if (webView.canGoBack())", ACTIVITY)
        self.assertIn("webView.goBack()", ACTIVITY)
        self.assertIn("moveTaskToBack(true)", ACTIVITY)

    def test_native_speech_bridge_keeps_multilingual_prompts_working(self) -> None:
        self.assertIn('addJavascriptInterface(new AndroidSpeechBridge(), "AndroidSpeech")', ACTIVITY)
        self.assertIn("Locale.forLanguageTag(languageTag)", ACTIVITY)
        self.assertIn("TextToSpeech.QUEUE_FLUSH", ACTIVITY)
        self.assertIn("window.finishAndroidSpeech", ACTIVITY)
        self.assertIn("window.AndroidSpeech?.speak", HTML)
        self.assertIn("window.AndroidSpeech?.stop", HTML)
        self.assertIn("const androidSpeechCallbacks = new Map()", HTML)
        self.assertIn("TextToSpeech.Engine.KEY_PARAM_VOLUME", ACTIVITY)
        self.assertIn("float rate, float volume", ACTIVITY)

    def test_app_stays_inside_the_local_child_safe_game(self) -> None:
        self.assertIn('android:allowBackup="false"', MANIFEST)
        self.assertIn('android:dataExtractionRules="@xml/data_extraction_rules"', MANIFEST)
        self.assertIn('android:usesCleartextTraffic="false"', MANIFEST)
        self.assertIn('return !url.startsWith("file:///android_asset/www/")', ACTIVITY)
        self.assertIn("setOnLongClickListener(view -> true)", ACTIVITY)


if __name__ == "__main__":
    unittest.main()
