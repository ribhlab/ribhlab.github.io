package com.ribhlab.tinyturboracers;

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.activity.ComponentActivity;
import androidx.activity.OnBackPressedCallback;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

public final class MainActivity extends ComponentActivity {
    private WebView game;

    @SuppressLint("SetJavaScriptEnabled") // Needed only by our bundled offline Canvas game.
    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showImmersiveGame();
        game = new WebView(this);
        game.setBackgroundColor(0xFF75D6F8);
        game.setOverScrollMode(View.OVER_SCROLL_NEVER);
        WebSettings settings = game.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(false);
        // File URLs can access bundled assets but never other file-URL origins.
        // Both cross-file WebView access settings default to false for modern target SDKs.
        // Block remote loads: the game contains only bundled, trusted HTML/CSS/JS.
        settings.setBlockNetworkLoads(true);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setMediaPlaybackRequiresUserGesture(true);
        game.setWebChromeClient(new WebChromeClient());
        game.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !request.getUrl().toString().startsWith("file:///android_asset/");
            }

            // Android 6.0 (API 23) compatibility; modern WebView uses WebResourceRequest.
            @SuppressWarnings("deprecation")
            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return !url.startsWith("file:///android_asset/");
            }
        });
        setContentView(game);
        registerGameBackHandler();
        game.loadUrl("file:///android_asset/index.html");
    }

    private void showImmersiveGame() {
        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        WindowInsetsControllerCompat controller =
            WindowCompat.getInsetsController(getWindow(), getWindow().getDecorView());
        controller.hide(WindowInsetsCompat.Type.systemBars());
        controller.setSystemBarsBehavior(
            WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
    }

    // Intercept both system Back buttons and predictive back gestures.
    // Keeping the handler lifecycle-aware prevents callbacks leaking on rotation/exit.
    // Our HTML5 game owns its internal navigation (race pause / resume / menus).
    private void registerGameBackHandler() {
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override public void handleOnBackPressed() {
                if (game != null) {
                    game.evaluateJavascript(
                        "if (typeof window.kidsBack === 'function') window.kidsBack();",
                        null);
                } else {
                    setEnabled(false);
                    getOnBackPressedDispatcher().onBackPressed();
                }
            }
        });
    }

    @Override protected void onDestroy() {
        if (game != null) {
            game.loadUrl("about:blank");
            game.destroy();
            game = null;
        }
        super.onDestroy();
    }
}
