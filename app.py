{% extends 'base.html' %}{% block content %}
<a class="btn gray" href="{{url_for('index')}}">الرئيسية</a>
<h2>الصفقات الخارجية</h2>
<div class="card">
  <h3>إضافة صفقة خارجية</h3>
  <form method="post">
    <div class="row">
      <input name="deal_name" placeholder="اسم الصفقة">
      <input name="company" placeholder="الشركة / المطور">
      <input name="deal_value" placeholder="قيمة الصفقة">
    </div>
    <div class="row">
      <input name="external_marketer" placeholder="اسم المسوق الخارجي">
      <input name="company_rate" placeholder="نسبة الشركة %">
      <input name="external_rate" placeholder="نسبة المسوق الخارجي %">
    </div>
    <textarea name="notes" placeholder="الأطراف / الموظفون / الملاحظات"></textarea>
    <button class="btn green">حفظ الصفقة</button>
  </form>
</div>
<div class="card">
  <b>ملاحظة:</b> هذه الصفحة جاهزة كرابط آمن حتى لا يظهر خطأ external_deals، ويمكن تطويرها لاحقاً لحساب النسب بالتفصيل.
</div>
{% endblock %}
