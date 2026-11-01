# RibhLab Etsy Publisher — تجهيز GitHub ديال univcours

الحساب اللي مرتبط بـ ChatGPT هو **univcours**. هذا المستودع خاصو يكون **Private** حيث غادي تكون فيه الملفات الرقمية المعروضة للبيع.

## خطوة ضرورية كيديرها صاحب الحساب مرة وحدة

1. دخل إلى https://github.com/new وأنت داخل حساب `univcours`.
2. اختار Owner = `univcours` و Repository name = `ribhlab-etsy-publisher`.
3. اختار **Private** ثم **Create repository**. يمكن تخليه فارغ: بلا README وبلا gitignore (حيت المشروع فيه هاد الملفات).
4. رجع لـ ChatGPT وقل غير "تصاوب الريبو" أو أعطي الرابط `https://github.com/univcours/ribhlab-etsy-publisher`. ما تصيفط لا password لا API key.

ما يمكنش لمساعد ChatGPT فهاد الربط ينشئ repository جديد أو يكتب GitHub Actions Secrets مباشرة، حتى لو عنده وصول للمستودعات الموجودة. بعد إنشاء المستودع، يقدر يضيف ملفات المشروع باستخدام GitHub connector المتصل.

## مفاتيح خزنها فقط داخل GitHub

داخل **المستودع الخاص الجديد**: Settings → Secrets and variables → Actions → New repository secret.

الأسماء المطلوبة: `ETSY_KEYSTRING`, `ETSY_SHARED_SECRET`, `ETSY_SHOP_ID`, `ETSY_REFRESH_TOKEN`.

- `ETSY_KEYSTRING` و `ETSY_SHARED_SECRET`: من Seller App approved عند Etsy.
- `ETSY_SHOP_ID`: رقم المتجر Etsy، يتحدد أثناء OAuth إذا أمكن.
- `ETSY_REFRESH_TOKEN`: يتم استخراجه بعد موافقتك على OAuth من أداة Python محلية (هاتف عبر Termux أو كمبيوتر). **لا يمكن توليده من API key وحده**.
- Redirect URI اللي سبق تسجّل في Etsy: `https://ribhlab.github.io/ar/etsy-oauth-callback.html`.

**مهم:** تسجيل redirect URL في Etsy أو زيارة الصفحة ماشي ربط OAuth. خاص استكمال ترخيص Etsy من خلال auth-start / auth-finish وإعداد الأسرار. ما تسيفطش أي كلمة سر أو Authorization Code/Redirect URL فيه `code` للشات أو GitHub public.

## شنو يقدر يدير ChatGPT بعد الربط؟

كيوجد `listing.json` للمنتجات، ويضيف الصور/الملفات القابلة للوصول عبر GitHub connector للمستودع الخاص؛ GitHub Actions يقدر ينشئ Draft وينشره عند `auto_publish:true` أو بطلب صريح. Etsy ممكن تحسب رسوم الإدراج، والتحكم النهائي كيكون في حسابك.

## التحقق السريع محليا

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

اختبارات البرنامج ما كتثبتش أن OAuth أو Etsy Live Publishing خدامين، وهذا مازال معلق بالربط الحقيقي.