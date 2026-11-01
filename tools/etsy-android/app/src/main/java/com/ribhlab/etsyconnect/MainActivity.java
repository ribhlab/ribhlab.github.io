package com.ribhlab.etsyconnect;

import android.app.Activity;
import android.app.KeyguardManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

public class MainActivity extends Activity {
    private static final String REDIRECT = "https://ribhlab.github.io/ar/etsy-oauth-callback.html";
    private static final String PREFS = "oauth_local_v1";
    private static final String ALIAS = "ribhlab_etsy_token_v1";
    private final SecureRandom random = new SecureRandom();
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());
    private EditText keyField;
    private TextView status;
    private Button connectButton;
    private Button copyButton;
    private SharedPreferences prefs;
    private String freshRefreshToken;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        buildScreen();
        processIntent(getIntent());
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        processIntent(intent);
    }

    private void buildScreen() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(42, 62, 42, 42);
        root.setBackgroundColor(Color.rgb(250, 247, 242));
        scroll.addView(root);
        TextView title = text("RibhLab Etsy Connect", 26, true);
        root.addView(title);
        root.addView(text("ربط متجر Etsy باش يقدر برنامج النشر يخدم. هاد التطبيق غير للترخيص وما كينشر حتى منتج.", 17, false));
        root.addView(text("1. لصق Keystring من Etsy:", 17, true));
        keyField = new EditText(this);
        keyField.setHint("Etsy Keystring");
        keyField.setSingleLine(true);
        keyField.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        keyField.setText(prefs.getString("key", ""));
        root.addView(keyField);
        connectButton = new Button(this);
        connectButton.setText("2. فتح Etsy للموافقة");
        root.addView(connectButton);
        connectButton.setOnClickListener(v -> launchOAuth());
        status = text("منين توافق فـ Etsy، غادي ترجع لصفحة RibhLab. ضغط فيها على «رجوع للتطبيق».", 16, false);
        root.addView(status);
        copyButton = new Button(this);
        copyButton.setText("3. نسخ Refresh Token");
        root.addView(copyButton);
        copyButton.setEnabled(hasSavedToken());
        copyButton.setOnClickListener(v -> copyToken());
        Button github = new Button(this);
        github.setText("4. فتح GitHub Secrets");
        github.setOnClickListener(v -> startActivity(new Intent(Intent.ACTION_VIEW,
                Uri.parse("https://github.com/ribhlab/ribhlab.github.io/settings/secrets/actions"))));
        root.addView(github);
        root.addView(text("GitHub: New repository secret → ETSY_REFRESH_TOKEN → لسق الرمز → Add secret. " +
                "ممنوع تصيفط رمز الدخول أو الرابط فيه code لأي شخص أو لـ ChatGPT.", 14, false));
        setContentView(scroll);
    }

    private TextView text(String value, int size, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value); t.setTextSize(size); t.setTextColor(Color.rgb(41,34,28));
        t.setPadding(0, 0, 0, 24);
        t.setTextDirection(View.TEXT_DIRECTION_ANY_RTL);
        if (bold) t.setTypeface(null, 1);
        return t;
    }

    private static String base64Url(byte[] bytes) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }
    private String randomString() {
        byte[] bytes = new byte[32]; random.nextBytes(bytes); return base64Url(bytes);
    }

    private void launchOAuth() {
        String key = keyField.getText().toString().trim();
        if (!key.matches("[A-Za-z0-9_-]{12,128}")) {
            status.setText("تأكد من Keystring اللي خديتي من Etsy.");
            return;
        }
        try {
            String verifier = randomString();
            String state = randomString();
            String challenge = base64Url(MessageDigest.getInstance("SHA-256").digest(verifier.getBytes(StandardCharsets.US_ASCII)));
            prefs.edit().putString("key",key).putString("verifier",verifier)
                    .putString("state",state).putLong("timestamp",System.currentTimeMillis()).apply();
            Uri url = Uri.parse("https://www.etsy.com/oauth/connect").buildUpon()
                .appendQueryParameter("response_type","code")
                .appendQueryParameter("client_id",key)
                .appendQueryParameter("redirect_uri",REDIRECT)
                .appendQueryParameter("scope","listings_r listings_w shops_r")
                .appendQueryParameter("state",state)
                .appendQueryParameter("code_challenge",challenge)
                .appendQueryParameter("code_challenge_method","S256").build();
            status.setText("Chrome غادي يفتح Etsy. وافق وارجع من رابط RibhLab للتطبيق.");
            startActivity(new Intent(Intent.ACTION_VIEW,url));
        } catch(Exception e) {
            status.setText("تعذر بدء الترخيص: "+e.getClass().getSimpleName());
        }
    }

    private void processIntent(Intent intent) {
        if (intent == null || intent.getData() == null) return;
        Uri data = intent.getData();
        if (!"ribhlabetsy".equals(data.getScheme()) || !"oauth".equals(data.getHost())) return;
        // Never keep the authorization code in Activity intent history.
        setIntent(new Intent(this, MainActivity.class));
        if (data.getQueryParameter("error") != null) {
            status.setText("Etsy ما عطاش الموافقة. عاود من التطبيق.");
            return;
        }
        final String code = data.getQueryParameter("code");
        String incomingState = data.getQueryParameter("state");
        String expectedState = prefs.getString("state", "");
        String verifier = prefs.getString("verifier", "");
        String key = prefs.getString("key", "");
        long timestamp = prefs.getLong("timestamp",0L);
        if (code == null || incomingState == null || !incomingState.equals(expectedState)
                || verifier.isEmpty() || key.isEmpty()
                || System.currentTimeMillis() - timestamp > 20 * 60 * 1000L) {
            status.setText("رمز الحماية غير مطابق أو انتهى. رجع وعاود Connect من التطبيق.");
            return;
        }
        // Consume state before any network request to prevent replays.
        prefs.edit().remove("state").remove("verifier").remove("timestamp").apply();
        connectButton.setEnabled(false);
        status.setText("تقبل الترخيص. كنهضرو مع Etsy مباشرة لاستخراج Refresh Token...");
        executor.execute(() -> {
            try {
                String body = "grant_type=authorization_code&client_id=" + Uri.encode(key)
                    + "&redirect_uri=" + Uri.encode(REDIRECT)
                    + "&code=" + Uri.encode(code)
                    + "&code_verifier=" + Uri.encode(verifier);
                HttpURLConnection connection = (HttpURLConnection)
                        new URL("https://api.etsy.com/v3/public/oauth/token").openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(15000);
                connection.setReadTimeout(15000);
                connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
                connection.setDoOutput(true);
                try(OutputStream output=connection.getOutputStream()) {
                    output.write(body.getBytes(StandardCharsets.UTF_8));
                }
                int responseCode = connection.getResponseCode();
                if (responseCode != 200)
                    throw new IllegalStateException("Etsy HTTP " + responseCode);
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                try(InputStream in=connection.getInputStream()) {
                    byte[] block=new byte[4096]; int n;
                    while((n=in.read(block))!=-1) bytes.write(block,0,n);
                }
                JSONObject result = new JSONObject(bytes.toString("UTF-8"));
                String token = result.getString("refresh_token");
                if (token.isEmpty()) throw new IllegalStateException("Missing refresh token");
                encryptToken(token);
                ui.post(()->{
                    freshRefreshToken=token;
                    copyButton.setEnabled(true);
                    status.setText("✅ الترخيص نجح! دابا اضغط «نسخ Refresh Token» وزيدو فقط فـ GitHub Secret ETSY_REFRESH_TOKEN.");
                    connectButton.setEnabled(true);
                });
            } catch(Exception e) {
                ui.post(()->{
                    status.setText("وقع خطأ فإتمام الترخيص ("+e.getMessage()+"). ما ترسل لا code ولا token للشات. عاود من زر Etsy.");
                    connectButton.setEnabled(true);
                });
            }
        });
    }

    private SecretKey getKey() throws Exception {
        KeyStore store=KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (store.containsAlias(ALIAS)) return ((KeyStore.SecretKeyEntry)store.getEntry(ALIAS,null)).getSecretKey();
        KeyGenerator generator=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build());
        return generator.generateKey();
    }

    private void encryptToken(String token) throws Exception {
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE,getKey());
        byte[] encrypted=cipher.doFinal(token.getBytes(StandardCharsets.UTF_8));
        prefs.edit().putString("refresh_cipher", Base64.getEncoder().encodeToString(encrypted))
                    .putString("refresh_iv",Base64.getEncoder().encodeToString(cipher.getIV())).apply();
    }
    private boolean hasSavedToken() {
        return prefs!=null && prefs.contains("refresh_cipher") && prefs.contains("refresh_iv");
    }
    private String decryptToken() throws Exception {
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE,getKey(),
                new GCMParameterSpec(128,Base64.getDecoder().decode(prefs.getString("refresh_iv",""))));
        return new String(cipher.doFinal(Base64.getDecoder().decode(prefs.getString("refresh_cipher",""))), StandardCharsets.UTF_8);
    }
    private void copyToken() {
        try {
            String token=freshRefreshToken!=null?freshRefreshToken:decryptToken();
            ClipboardManager clipboard=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            clipboard.setPrimaryClip(ClipData.newPlainText("Etsy refresh token", token));
            status.setText("✅ تنسخ الرمز. دخل لـ GitHub Secrets، اختر New repository secret باسم ETSY_REFRESH_TOKEN، ولسق الرمز. ما ترسلش الرمز في الشات.");
        } catch(Exception e) {
            status.setText("تعذر استرجاع الرمز من التخزين الآمن. عاود الربط.");
        }
    }

    @Override protected void onDestroy() {
        executor.shutdown();
        super.onDestroy();
    }
}
