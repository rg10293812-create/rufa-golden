طريقة تشغيل نسخة روفا جولدن السحابية

الفكرة:
هذه النسخة تحفظ البيانات تلقائياً في قاعدة بيانات سحابية عبر DATABASE_URL.
أي جهاز يفتح نفس رابط النظام يشاهد نفس العقارات والأرقام والعروض والرسائل.

الملفات المهمة:
- app.py : كود النظام
- requirements.txt : مكتبات التشغيل
- Procfile : أمر التشغيل على Render

الطريقة المقترحة باستخدام Supabase + Render:

1) إنشاء قاعدة بيانات Supabase
- ادخل على supabase.com
- أنشئ مشروع جديد
- من Project Settings ثم Database انسخ رابط Connection string بصيغة URI
- الرابط يكون شبيه:
  postgresql://postgres.xxxxx:PASSWORD@aws-0-region.pooler.supabase.com:6543/postgres
- استبدل PASSWORD بكلمة مرور قاعدة البيانات.

2) رفع النظام على GitHub
- أنشئ Repository جديد باسم rufa-golden-cloud
- ارفع محتويات هذا المجلد بالكامل.

3) تشغيل النظام على Render
- ادخل render.com
- New ثم Web Service
- اربط Repository
- Build Command:
  pip install -r requirements.txt
- Start Command:
  gunicorn app:app

4) إضافة متغيرات البيئة Environment Variables في Render
- DATABASE_URL = رابط Supabase الذي نسخته
- SECRET_KEY = أي كلمة سر طويلة مثل: rufa-golden-2026-secure-key

5) بعد التشغيل
- Render يعطيك رابط مثل:
  https://rufa-golden-cloud.onrender.com
- افتح الرابط من الكمبيوتر أو الآيباد أو الآيفون.
- أي بيانات تضيفها تحفظ مباشرة وتظهر على كل الأجهزة.

طريقة وضعه على الآيباد أو الآيفون:
1) افتح رابط النظام من Safari.
2) اضغط زر المشاركة.
3) اختر إضافة إلى الشاشة الرئيسية.
4) يظهر النظام كتطبيق على الشاشة.

ملاحظات مهمة:
- الرسائل في واتساب تفتح جاهزة حسب الرقم والرسالة، وقد يحتاج المستخدم الضغط على إرسال داخل واتساب.
- الصور محفوظة داخل قاعدة البيانات حتى تظهر على جميع الأجهزة. لا ترفع صور كبيرة جداً؛ يفضل صور مضغوطة.
- الحقول تحفظ كمسودة تلقائية على الجهاز قبل الضغط على حفظ، وبعد الضغط على حفظ يتم التخزين في السحابة.
