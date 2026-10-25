# نشر RibhLab على GitHub لحساب univcours

1. افتح https://github.com/new واكتب `ribhlab-site` في Repository name. اختر **Public** ثم Create repository. يفضّل إنشاء مستودع فارغ بدون README لأن المشروع يتضمنه.
2. اربط ChatGPT / GitHub بالمستودع الجديد ومنح الوصول حسب طلب التطبيق، أو ارفع ملفات المصدر من هذا الأرشيف إلى جذر المستودع (ليس ZIP نفسه؛ فكّه أولا). **لا ترفع dist/ ولا node_modules/**.
3. إذا أردت GitHub Pages: انتقل إلى Repository **Settings > Pages > Build and deployment > Source: GitHub Actions**. بعدها workflow ينشر تلقائياً عند كل تحديث على main.
4. بعد نجاح النشر سيكون رابط التجربة المتوقع: https://univcours.github.io/ribhlab-site/ . **الرابط لا يصبح حقيقياً قبل إنشاء المستودع والرفع وتفعيل Pages ونجاح workflow**.
5. أعد بناء الموقع بعد إضافة عنوان بريد التواصل الحقيقي، والاسم القانوني للناشر والدومين المخصص عند توفره. عدّل SITE_URL في `.github/workflows/deploy-pages.yml` إذا اخترت دوميناً مخصصاً.
6. تحرير المقالات: `content/articles/*.json` ثم Commit على main؛ Actions تعيد بناء الموقع. لوحة `/admin/` تحتاج اعتماد GitHub مناسباً، ولا تتوقع الدخول قبل الإعداد.

**تنبيه:** Google AdSense يراجع الموقع بشكل مستقل؛ لا يوجد ضمان قبول. تعيين دومين مخصص وتوفير معلومات تواصل صحيحة، سياسة خصوصية محدثة وتجربة جيدة ضروريان للتجهيز الكامل.
