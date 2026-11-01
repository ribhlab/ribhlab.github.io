# RibhLab Etsy Publisher — الخطوات الباقية ديال الربط

✅ تطبيق Etsy ديالك **ribhlab-etsy-publisher** Approved. الصفحة ديال OAuth موجودة فموقعك على GitHub Pages.

## دابا شنو خاص يتدار؟

1. دخل لـ https://www.etsy.com/developers/your-apps وفتح التطبيق ديالك، ومن إعدادات **Redirect URIs** زيد هاد الرابط بالحرف:

   `https://ribhlab.github.io/ar/etsy-oauth-callback.html`

2. **مهم: ما ترسل حتى API Key أو Shared Secret أو Token أو URL فيه `code` فالشات.** احتافظ بها عندك.

3. خاصنا **مستودع GitHub خاص Private** ومفصول على موقع RibhLab العمومي. المنتجات الرقمية المدفوعة خاصها ما تكونش فمستودع Public حيث أي واحد يقدر يحملها مجانا. الرابط لإنشاء المستودع: https://github.com/new . سمّيه مثلا `ribhlab-etsy-publisher` واختار **Private**.

4. نزّل هاد الحزمة، حمّل ملفاتها للمستودع الخاص (تقدر تبدأ من PC). ثبّت Python 3.12 واكتب `pip install -r requirements.txt`، ثم نسخ `.env.example` لملف `.env` وعمر `ETSY_KEYSTRING` و`ETSY_SHARED_SECRET` و`ETSY_REDIRECT_URI` فيه عندك.

5. شغل `python -m etsy_publisher auth-start` وفتح رابط Etsy اللي كيطلع. وافق على الترخيص. من صفحة الرجوع ديال RibhLab اضغط على زر **نسخ رابط العودة بشكل خاص** (ما تشاركوش). رجع لـ Terminal وشغل `python -m etsy_publisher auth-finish` ولسق الرابط في الطلب الخاص. التوكن كيتحفظ محلياً في `.state/oauth_tokens.json`، والمشروع كيحاول يجيب `shop_id` تلقائياً.

6. على GitHub الخاص فقط، دخل **Settings → Secrets and variables → Actions** وزيد 4 secrets: `ETSY_KEYSTRING`, `ETSY_SHARED_SECRET`, `ETSY_SHOP_ID`, `ETSY_REFRESH_TOKEN`. `ETSY_REFRESH_TOKEN` تقدر تجيبو من الملف المحلي؛ ما تحطوش فشي ملف وسط GitHub.

7. كل منتج: حط `products/SKU/listing.json` مع صور معاينة وPDF/ZIP ديال الزبون (حتى 5 ملفات × 20MB للواحد). النشر الافتراضي Draft، إلا إذا طلبتي تفعيل `auto_publish` أو Workflow `publish_live`.

## شنو وجدت دابا؟

- الكود الكامل لرفع المنتجات الرقمية والصور والنشر عبر Etsy API.
- GitHub Actions للنشر من المستودع الخاص وحفظ معرف كل إعلان لتفادي التكرار.
- صفحة Redirect HTTPS على RibhLab للنسخ المحلي ديال رمز الرجوع.
- اختبارات محلية بدون استعمال الحساب الحقيقي.

⚠️ Seller App Approved ماشي معناها الربط OAuth كمل. مازال ما كاين حتى إعلان تنشر من الأداة حتى تكتمل الخطوات الشخصية 1 و3 و5 و6.
