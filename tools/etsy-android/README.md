# RibhLab Etsy Connect — Android OAuth assistant

Mobile app to authorize **one Etsy seller app** using the user's browser, receive the callback through a custom URL, and exchange the authorization code natively over HTTPS with Etsy (avoids web browser CORS).

- No shared secret, Etsy password or GitHub token is requested by the app.
- The app stores the refresh token encrypted with Android Keystore and only copies it to the clipboard after an explicit tap.
- Register exactly: `https://ribhlab.github.io/ar/etsy-oauth-callback.html` in Etsy redirect URIs.
- Open the app, paste the Etsy Keystring, tap Connect and approve access on Etsy. On the callback page tap 'Return to Android app'.
- Once the token appears, tap Copy and paste only into GitHub Actions secret `ETSY_REFRESH_TOKEN` for the publisher's repository. Never paste into ChatGPT.
- The publisher still needs `ETSY_SHOP_ID` and should be moved to a private repository before product files are added.
- The debug APK is not Play Store signed, and Android will warn about installing apps outside the store. Only install it if you trust this source and inspected the code.
- If a browser refuses deep links, open the URL in Chrome and try again. OAuth codes are short-lived, so initiate a new authorization in the app if needed.
- No Etsy listing is created by this app. It only obtains authorization.
