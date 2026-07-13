package dev.mobileframework.hybriddemo;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.os.Bundle;
import android.view.ViewGroup;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public final class MainActivity extends Activity {
    @Override
    @SuppressLint("SetJavaScriptEnabled")
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WebView.setWebContentsDebuggingEnabled(true);
        WebView webView = new WebView(this);
        webView.setContentDescription("Hybrid Demo WebView");
        webView.setWebViewClient(new WebViewClient());

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);

        setContentView(
            webView,
            new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        );
        webView.loadDataWithBaseURL("https://hybrid.demo.local/", html(), "text/html", "UTF-8", null);
    }

    private String html() {
        return "<!doctype html>"
            + "<html lang='en'>"
            + "<head>"
            + "<meta charset='utf-8'>"
            + "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            + "<title>Hybrid Demo</title>"
            + "<style>"
            + "body{font-family:sans-serif;margin:24px;background:#f7f8fb;color:#172033;}"
            + "label,input,button,#status{display:block;margin-top:16px;font-size:18px;}"
            + "input,button{min-height:44px;width:100%;box-sizing:border-box;}"
            + "button{background:#1457a8;color:white;border:0;border-radius:6px;}"
            + "</style>"
            + "</head>"
            + "<body>"
            + "<h1>Hybrid Demo</h1>"
            + "<p id='mode'>Running inside a native WebView</p>"
            + "<label for='name'>Name</label>"
            + "<input id='name' autocomplete='off'>"
            + "<button id='greet' type='button'>Greet</button>"
            + "<p id='status' role='status'>Waiting</p>"
            + "<script>"
            + "document.getElementById('greet').addEventListener('click',function(){"
            + "var name=document.getElementById('name').value||'hybrid tester';"
            + "document.getElementById('status').textContent='Hello, '+name;"
            + "});"
            + "</script>"
            + "</body>"
            + "</html>";
    }
}
