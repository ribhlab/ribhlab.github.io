# RibhLab — ربح لاب | العربية · English · Français

موقع نشر وتعليم بثلاث لغات يعمل فعلياً عبر **GitHub Pages** على https://ribhlab.github.io/ar/ (والنسختان /en/ و/fr/). الاستضافة على هذا العنوان مجانية حالياً، ولا يلزم دومين مدفوع للنشر. البريد الرسمي غير مضبوط بعد، وتوجد قناة تصحيحات عمومية عبر GitHub Issues. التوسع والتحقق من الجودة يجريان قبل أي طلب AdSense.

## ما الذي يضمّه المشروع؟

- **282 صفحة محتوى مولّدة بتاريخ 27/10/2026** موزعة على ثلاث لغات، وتشمل المقالات والأقسام والأدوات وصفحات الوظائف والهجرة والسياسات؛ العدد يتغير مع نشر مقالات جديدة.
- **43 مقالة أصلية × 3 لغات** (129 نسخة مترجمة) في محاور الربح، التداول، الذكاء الاصطناعي ونمط الحياة، مع صور مرخصة منفصلة ومصادر وروابط رسمية عند الحاجة.
- إدارة محتوى مبنية على **Sveltia CMS** في `/admin/` مع محرر JSON قابل للتحرير، يتطلب ربط GitHub والاعتماد المناسب.
- بحث سريع حسب اللغة، تصميم RTL بالعربية وLTR بالإنجليزية/الفرنسية، قائمة للهاتف وروابط لتغيير لغة المقال.
- أدوات تعمل محلياً: حاسبة ميزانية مخاطرة التداول، حاسبة تسعير العمل الحر، ومولّد برومبت.
- SEO: HTML جاهز للزحف، عناوين وأوصاف مختلفة، بيانات Article structured data و`robots.txt` و`sitemap.xml` وروابط canonical/hreflang على الدومين المستعمل حالياً **ribhlab.github.io**.
- صفحات: سياسة الخصوصية، شروط الاستخدام، من نحن، التواصل، إخلاء المسؤولية، السياسة التحريرية.
- **AdSense غير مفعّل افتراضياً.** التحقق عبر رقم الناشر وملف ads.txt جاهز شرط إضافة الرقم الحقيقي؛ انظر `docs/ADSENSE_READINESS.md`. لا توجد إعلانات فعلية ولا أدوات قياس الزوار من دون تهيئة حقيقية.


### صفحات جديدة ومصادر رسمية

- فرص عمل ومباريات المؤسسات العمومية: https://ribhlab.github.io/ar/opportunities/competitions/ (فقط الفرص التي اجتازت التحقق المصدرّي؛ أرشيف المنصة لا يعني أن جميع الإعلانات مفتوحة).
- فرص الشركات والهجرة وروابط السفارات: https://ribhlab.github.io/ar/opportunities/ . لا تمثل روابط حجز التأشيرات تأكيد توفر مواعيد.
- بيانات الزوار حسب الدولة: https://ribhlab.github.io/ar/audience/ — تظهر حالة «غير متصل» إلى حين ربط إحصائيات حقيقية.
- إرشادات إضافة رقم ناشر AdSense بعد إعداد المحتوى: `docs/ADSENSE_READINESS.md`.

## 1. تشغيل الموقع محلياً

يلزم **Node.js 20 أو أحدث**؛ لا توجد مكتبات npm ضرورية.

```bash
npm run build
npm run check
npm run dev
```

افتح `http://localhost:4173/ar/`، أو `/en/`، أو `/fr/`. أوقف الخادم بـ `Ctrl+C`.

يمكن أيضاً استضافة محتوى مجلد `dist/` على أي استضافة ثابتة. لا ترفع المشروع كاملاً كموقع جاهز؛ ارفع `dist` فقط بعد البناء.

## 2. إعدادات الموقع الحالي

هذا الموقع منشور بالفعل على GitHub Pages؛ لا تحتاج لاستضافة Netlify أو شراء دومين. ملف `site.config.json` الحالي يتضمن الدومين الصحيح. عند الحاجة إلى معلومات ناشر حقيقية ومعلنة، عدّل الإعدادات التالية فقط بعد التأكد من ملكيتها:

مثال عام (ليس البيانات الفعلية):

```json
{
  "brand": "RibhLab",
  "domain": "https://YOUR-REAL-DOMAIN.COM",
  "contactEmail": "YOUR-REAL-EMAIL@YOUR-DOMAIN.COM",
  "publisherName": "RibhLab Editorial Team",
  "adsensePublisherId": "",
  "social": {"youtube":"", "linkedin":""}
}
```

لا تخترع بريداً أو اسم شركة أو رقم ناشر AdSense. للدومين الحالي تستعمل عملية النشر إعداد GitHub Pages مباشرة. تغيير الفرع `main` يطلق البناء والاختبارات والنشر، و`dist/` يُنشأ تلقائياً داخل GitHub Actions.

## 3. لوحة إدارة المقالات (قابلة للتحديث)

1. المستودع الرئيسي موجود بالفعل: `ribhlab/ribhlab.github.io`.
2. تأكد أن ملف `admin/config.yml` يشير إلى `ribhlab/ribhlab.github.io` قبل استعمال واجهة التحرير.
3. افتح `https://ribhlab.github.io/admin/` بعد التأكد من إعدادات الصلاحيات.
4. لتسجيل الدخول كمالك مستودع GitHub، اختر **Sign In with Token** في Sveltia CMS واستعمل access token بحدود الوصول المناسبة إلى المستودع فقط. لا تشارك المفتاح مع أحد، ولا تضفه إلى ملفات الموقع.
5. بعد حفظ المقالة والالتزام ببنية ملفات المحتوى، يُعيد GitHub Actions بناء الموقع؛ النشر مشروط بنجاح الاختبارات. راجع أذونات المستودع قبل منح الوصول لأي محرر.

للفرق التي تفضّل دخولاً دون token، يمكن إعداد OAuth وفق توثيق Sveltia الرسمي. لوحة التحكم تعتمد على خدمة خارجية وقت التشغيل ولا تعمل بدون الربط والإنترنت.

### تحرير مباشر دون لوحة تحكم

كل مقالة ملف في `content/articles/*.json`. يمكنك فتحه وتعديل محتوى `translations.ar` و`translations.en` و`translations.fr` و`sections`. لنسخ مقال جديد، انسخ ملفاً، غيّر اسمه و`slug` والفئة والتواريخ واللغات الثلاث، ثم أعد البناء. سيظهر في الأقسام والبحث والخريطة تلقائياً. **تحتوي كل مقالة على اللغات الثلاث كاملة**؛ البناء يمنع النشر إذا نقصت ترجمة أو ثلاثة أقسام على الأقل. حافظ على استقلالية التحرير وجودة الترجمة.

## 4. AdSense: التجهيز ≠ الموافقة

تم تصميم التنقل والصفحات والمحتوى الأصلي والمراجعة لتسهيل استيفاء متطلبات شائعة، **لكن لا توجد أي طريقة تضمن القبول**؛ Google وحدها تقرر، وهي تتحقق من جودة الموقع الحقيقية وملاءمة المحتوى والالتزام بالسياسات. قبل تقديم الطلب:

- الموقع منشور عبر HTTPS على `ribhlab.github.io`. حدّد بريداً حقيقياً للاتصال إن رغبت في عرضه للزوار، وحافظ على قناة تصحيحات عمومية وتعريف صادق بالناشر.
- راجع جميع المقالات وأضف محتوى أصلياً من خبرتك، أمثلة أو اختبارات حقيقية، روابط مرجعية موثوقة، وتحديثات منتظمة حيث يلزم. المحتوى الحالي نقطة بداية، وليس ضماناً للجودة المطلوبة.
- أصلح أي صفحات ناقصة أو مكررة، وأبقِ روابط التنقل والفهرسة فعّالة؛ أرسل sitemap إلى Search Console.
- لا تعرض وعوداً بتحقيق أرباح مضمونة أو نتائج تداول مضللة، ولا تشجّع النقر على الإعلانات.
- أضف الإفصاحات المناسبة لأي روابط تسويق بالعمولة وشروط المنتجات قبل إطلاقها.
- **لربط الموقع قبل طلب المراجعة** أدخل معرف الناشر الحقيقي `ca-pub-XXXXXXXXXXXXXXXX` في متغير GitHub Actions `RIBHLAB_ADSENSE_PUBLISHER_ID` (أو إعداد محلي خاص بك)، ثم انشر لتحصل على علامة التحقق و`ads.txt`. بعدها أرسل الموقع للمراجعة من لوحة AdSense. لا تنتظر القبول لإضافة علامة ملكية الموقع.
- **لا تفعّل تحميل سكربت الإعلانات قبل إعداد الموافقات المطلوبة.** لخدمة إعلانات مخصّصة للمستخدمين في EEA/UK/سويسرا، تتطلب Google منصة إدارة موافقة معتمدة من Google ومتكاملة مع IAB TCF. استخدم Google Privacy & messaging أو مزوداً معتمداً. هذا المشروع لا يحتوي CMP معتمدة؛ ولا يُعد أي إشعار كوكيز عادي بديلاً عنها.
- **بعد موافقة Google** وإعداد الموافقات المطلوبة، فعّل `RIBHLAB_ENABLE_ADSENSE=true` صراحة ضمن GitHub Actions Variables وأعد النشر. سياسة الخصوصية تتضمن إفصاح إعلانات Google تلقائياً عند تفعيلها.

الوثائق الرسمية:

- Google AdSense eligibility: https://support.google.com/adsense/answer/9724
- Page readiness: https://support.google.com/adsense/answer/7299563
- Certified consent platforms: https://support.google.com/adsense/answer/13554116
- Sveltia CMS GitHub: https://sveltiacms.app/en/docs/backends/github

## 5. حدود النسخة الحالية

- الموقع منشور بالفعل على الدومين المجاني GitHub Pages. ربط حساب Google AdSense، التحقق من أهلية الدومين وتقديم المراجعة يحتاج حساب الناشر الحقيقي وإجراءه من لوحة Google.
- الإدارة تحتاج إعداد GitHub مرة واحدة. المستخدم النهائي يرى موقعاً ثابتاً سريعاً؛ التحديثات ليست تلقائية من مصادر الأخبار، بل تتم بالنشر والتحرير والتحقق.
- لا يوجد نموذج اتصال خاص؛ يمكن التواصل عبر GitHub Issues، أو إضافة بريد عمومي حقيقي حين يتوفر. لا تنشر أي بيانات تعريف شخصية من دون موافقة.
- أدوات التداول تعليمية ولا تقدم حساب حجم عقد فعلي أو إشارات تداول.
- صفحة `privacy` تصف الإعداد الفعلي، وتتغير إفصاحات Umami وGoogle AdSense تلقائياً عند تنشيطهما. يجب مراجعة القواعد المحلية واشتراطات الموافقة قبل تفعيل إعلانات الجمهور الأوروبي.

---

**EN**: Live at https://ribhlab.github.io/. Push changes to GitHub to test and deploy automatically. Ads are OFF until the authentic publisher ID, Google review and compliant consent workflow are completed.

**FR** : Site publié sur https://ribhlab.github.io/. Les modifications GitHub déclenchent les tests et le déploiement. AdSense reste désactivé sans véritable identifiant, examen Google et recueil du consentement applicable.

## Sharing and Google Search

Every article has share links for WhatsApp, Facebook, X, LinkedIn, Telegram, Pinterest, Reddit and email. Native device sharing and copy-link also support Instagram/TikTok/Snapchat manually (they do not offer universal web prefilled sharing links). Metadata includes Open Graph image, Twitter/X card, canonical, hreflang and Article JSON-LD. Sitemap and robots.txt are produced from `SITE_URL` during builds. After deployment, submit `https://univcours.github.io/ribhlab-site/sitemap.xml` to Google Search Console and verify ownership. Indexation is determined by search engines, not guaranteed.
