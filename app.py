{% extends 'base.html' %}
{% block content %}
<h3>تسجيل بيع العقار وتوزيع السعي</h3>
<div class="card p-3 mb-3"><b>{{ prop.code }} - {{ prop.project_name }}</b><br>الحي: {{ prop.district }} | السعر: {{ prop.price|money }}</div>
<div class="card p-3"><form method="post">
  <label class="form-label">مبلغ السعي الفعلي</label><input class="form-control mb-3" name="commission_amount" placeholder="مثال: 50000" required>
  <h5>توزيع السعي على الموظفين أو الميدانيين</h5>
  <p class="text-muted">أضف من شارك فقط، والباقي يحسب للشركة تلقائيًا.</p>
  {% for i in range(5) %}
  <div class="row g-2 mb-2">
    <div class="col-md-8"><select class="form-select" name="user_id"><option value="">اختر موظف/ميداني</option>{% for u in users %}<option value="{{ u.id }}">{{ u.name }} - {{ u.role }}</option>{% endfor %}</select></div>
    <div class="col-md-4"><input class="form-control" name="percent" placeholder="النسبة %"></div>
  </div>
  {% endfor %}
  <button class="btn btn-gold">حفظ البيع وتوزيع السعي</button>
</form></div>
{% endblock %}
