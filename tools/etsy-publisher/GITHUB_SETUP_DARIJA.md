# RibhLab Etsy Publisher: GitHub setup (Darija)

## الحالة دابا
- Etsy seller app داز Approved.
- OAuth redirect مسجل من عند المستخدم:
  `https://ribhlab.github.io/ar/etsy-oauth-callback.html`
- source code only is hosted under `ribhlab/ribhlab.github.io/tools/etsy-publisher`.
- **هاد المستودع PUBLIC** حيث هو الموقع الرسمي، لذلك ممنوع ترفع ليه تصاميم للبيع، ملفات PDF الرقمية أو مفاتيح API.
- GitHub Actions workflow متوفر ولكن بلا Etsy secrets والملفات ما غادي ينشر والو.

## الخطوات اللي خاص يديرها صاحب الحساب مرة وحدة
1. جهّز GitHub repository مستقل PRIVATE للمنتجات. ما تحولش موقع `ribhlab.github.io` لـ Private إلا كنت فاهم أثرها على GitHub Pages.
2. انسخ المشروع من `tools/etsy-publisher` لهاد المستودع الخاص؛ في المستودع الخاص يمكن تحط `products/<slug>/images` و `products/<slug>/files` وترجع workflow للمسارات الجذرية حسب التصميم.
3. من جهاز موثوق: `python -m pip install -r requirements.txt`, وحط `ETSY_KEYSTRING`, `ETSY_SHARED_SECRET`, `ETSY_REDIRECT_URI` في ملف `.env` محلي. ما تشاركهمش فالشات.
4. شغّل `python -m etsy_publisher auth-start` ووافق على الصلاحيات من حساب Etsy.
5. صفحة الرجوع كتسمح تنسخ رابط حساس خاص، دخلو محلياً بــ `python -m etsy_publisher auth-finish` ومن بعد الصق الرابط في terminal، بلا ما ترسلو لChatGPT أو GitHub.
6. تلقى `shop_id` و`refresh_token` في `.state/oauth_tokens.json` محلياً. سجلهم كـ GitHub Actions Secrets في المستودع الخاص.
7. شغّل GitHub Actions يدوياً، وأول تجربة خلي `publish_live=false` باش ينشئ Draft؛ بعد مراجعة النتيجة شغّل `true` لنفس slug.

## تنبيه
النسخة الموجودة فالموقع عامة ومخصصة للكود فقط. ملفات المستخدم السرية تبقى محلية أو في private repo.
رموز OAuth قابلة للإلغاء من Etsy. ولا يمكننا نشر أي منتج بدون ترخيص نهائي من البائع.
