package com.michalisantoniou.polyglotplayroom;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.ActivityManager;
import android.os.Build;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.view.View;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.util.Locale;

public final class MainActivity extends Activity implements TextToSpeech.OnInitListener {
    private static final String START_URL = "file:///android_asset/www/index.html";
    private static final String EXTRA_PRIMARY_LANGUAGE = "primaryLanguage";

    private WebView webView;
    private TextToSpeech textToSpeech;
    private boolean textToSpeechReady;
    private boolean languageOverrideApplied;

    @Override
    @SuppressLint("SetJavaScriptEnabled")
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        webView = new WebView(this);
        webView.setBackgroundColor(0xFFF7FBFF);
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        webView.setOnLongClickListener(view -> true);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);

        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new LocalGameWebViewClient());
        webView.addJavascriptInterface(new AndroidSpeechBridge(), "AndroidSpeech");
        webView.addJavascriptInterface(new AndroidChildLockBridge(), "AndroidChildLock");
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);

        setContentView(webView);
        webView.post(this::showImmersivePlayArea);
        textToSpeech = new TextToSpeech(getApplicationContext(), this);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                this::handleBack
            );
        }

        if (savedInstanceState == null) {
            webView.loadUrl(START_URL);
        } else {
            webView.restoreState(savedInstanceState);
        }
    }

    @Override
    public void onInit(int status) {
        textToSpeechReady = status == TextToSpeech.SUCCESS;
        if (!textToSpeechReady) {
            return;
        }

        textToSpeech.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override
            public void onStart(String utteranceId) {
            }

            @Override
            public void onDone(String utteranceId) {
                finishWebSpeech(utteranceId);
            }

            @Override
            public void onError(String utteranceId) {
                finishWebSpeech(utteranceId);
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        showImmersivePlayArea();
        webView.onResume();
        notifyChildLockState();
    }

    @Override
    protected void onPause() {
        webView.onPause();
        super.onPause();
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        webView.saveState(outState);
        super.onSaveInstanceState(outState);
    }

    @Override
    protected void onDestroy() {
        if (textToSpeech != null) {
            textToSpeech.stop();
            textToSpeech.shutdown();
        }
        webView.removeJavascriptInterface("AndroidSpeech");
        webView.removeJavascriptInterface("AndroidChildLock");
        webView.destroy();
        super.onDestroy();
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        handleBack();
    }

    private void handleBack() {
        if (webView.canGoBack()) {
            webView.goBack();
            return;
        }

        if (isChildLockActive()) {
            return;
        }

        moveTaskToBack(true);
    }

    private void finishWebSpeech(String utteranceId) {
        if (utteranceId == null || !utteranceId.startsWith("web-")) {
            return;
        }

        String generation = utteranceId.substring(4);
        webView.post(() -> webView.evaluateJavascript(
            "window.finishAndroidSpeech && window.finishAndroidSpeech(" + generation + ")",
            null
        ));
    }

    private void showImmersivePlayArea() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            getWindow().setDecorFitsSystemWindows(false);
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.hide(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
                controller.setSystemBarsBehavior(
                    WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
                );
            }
            return;
        }

        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
        );
    }

    private boolean isChildLockActive() {
        ActivityManager activityManager = (ActivityManager) getSystemService(ACTIVITY_SERVICE);
        return activityManager != null
            && activityManager.getLockTaskModeState() != ActivityManager.LOCK_TASK_MODE_NONE;
    }

    private void notifyChildLockState() {
        if (webView == null) {
            return;
        }

        boolean isActive = isChildLockActive();
        webView.post(() -> webView.evaluateJavascript(
            "window.updateAndroidChildLock && window.updateAndroidChildLock(" + isActive + ")",
            null
        ));
    }

    private final class AndroidSpeechBridge {
        @JavascriptInterface
        public void speak(String text, String languageTag, int generation, float rate, float volume) {
            runOnUiThread(() -> {
                if (!textToSpeechReady) {
                    webView.evaluateJavascript(
                        "window.finishAndroidSpeech && window.finishAndroidSpeech(" + generation + ")",
                        null
                    );
                    return;
                }

                textToSpeech.stop();
                textToSpeech.setLanguage(Locale.forLanguageTag(languageTag));
                textToSpeech.setSpeechRate(Math.max(0.5f, Math.min(rate, 1.25f)));
                Bundle speechParameters = new Bundle();
                speechParameters.putFloat(
                    TextToSpeech.Engine.KEY_PARAM_VOLUME,
                    Math.max(0.0f, Math.min(volume, 1.0f))
                );
                textToSpeech.speak(
                    text,
                    TextToSpeech.QUEUE_FLUSH,
                    speechParameters,
                    "web-" + generation
                );
            });
        }

        @JavascriptInterface
        public void stop() {
            runOnUiThread(() -> {
                if (textToSpeech != null) {
                    textToSpeech.stop();
                }
            });
        }
    }

    private final class AndroidChildLockBridge {
        @JavascriptInterface
        public void start() {
            runOnUiThread(() -> {
                try {
                    startLockTask();
                } catch (IllegalArgumentException | IllegalStateException | SecurityException ignored) {
                    // Android or the device policy may decline pinning; the UI receives the real state below.
                }
                showImmersivePlayArea();
                notifyChildLockState();
            });
        }

        @JavascriptInterface
        public void stop() {
            runOnUiThread(() -> {
                try {
                    stopLockTask();
                } catch (IllegalArgumentException | IllegalStateException | SecurityException ignored) {
                    // Already unlocked or controlled by the device owner.
                }
                showImmersivePlayArea();
                notifyChildLockState();
            });
        }

        @JavascriptInterface
        public boolean isActive() {
            return isChildLockActive();
        }
    }

    private final class LocalGameWebViewClient extends WebViewClient {
        @Override
        public void onPageFinished(WebView view, String url) {
            super.onPageFinished(view, url);
            applyPrimaryLanguageOverride(view);
            notifyChildLockState();
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            String url = request.getUrl().toString();
            return !url.startsWith("file:///android_asset/www/");
        }

        private void applyPrimaryLanguageOverride(WebView view) {
            if (languageOverrideApplied) {
                return;
            }

            String language = getIntent().getStringExtra(EXTRA_PRIMARY_LANGUAGE);
            if (!isSupportedLanguage(language)) {
                return;
            }

            languageOverrideApplied = true;
            view.evaluateJavascript(
                "window.applyInstalledOnboardingLanguage && window.applyInstalledOnboardingLanguage('"
                    + language
                    + "')",
                null
            );
        }

        private boolean isSupportedLanguage(String language) {
            return "el".equals(language)
                || "en".equals(language)
                || "enUS".equals(language)
                || "es".equals(language)
                || "esES".equals(language)
                || "fr".equals(language)
                || "de".equals(language)
                || "it".equals(language)
                || "tr".equals(language)
                || "ptBR".equals(language)
                || "nl".equals(language)
                || "pl".equals(language);
        }
    }
}
