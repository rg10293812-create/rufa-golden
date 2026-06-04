import os, urllib.parse, base64
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'rufa-golden-change-me')

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///rufa_golden_cloud.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, default='')
    location = db.Column(db.Text, default='')
    price = db.Column(db.Text, default='')
    specs = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.Text, index=True)
    name = db.Column(db.Text, default='')
    phone = db.Column(db.Text, default='')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Offer(db.Model):
    __tablename__ = 'offers'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, default='')
    description = db.Column(db.Text, default='')
    price = db.Column(db.Text, default='')
    image_data = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CustomerMessage(db.Model):
    __tablename__ = 'customer_messages'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.Text, default='')
    phone = db.Column(db.Text, default='')
    message = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/properties', methods=['GET','POST'])
def properties():
    if request.method == 'POST':
        row = Property(name=request.form.get('name',''), location=request.form.get('location',''), price=request.form.get('price',''), specs=request.form.get('specs',''))
        db.session.add(row); db.session.commit()
        flash('تم حفظ العقار تلقائياً على السحابة')
        return redirect(url_for('properties'))
    q = request.args.get('q','').strip()
    query = Property.query
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Property.name.ilike(like), Property.location.ilike(like), Property.price.ilike(like), Property.specs.ilike(like)))
    rows = query.order_by(Property.id.desc()).all()
    return render_template('properties.html', rows=rows, q=q)

@app.route('/properties/<int:pid>')
def property_detail(pid):
    row = Property.query.get_or_404(pid)
    return render_template('property_detail.html', row=row)

@app.route('/properties/delete/<int:pid>', methods=['POST'])
def delete_property(pid):
    row = Property.query.get_or_404(pid)
    db.session.delete(row); db.session.commit()
    flash('تم حذف العقار من السحابة')
    return redirect(url_for('properties'))

@app.route('/contacts/<category>', methods=['GET','POST'])
def contacts(category):
    labels = {'marketers':'أرقام المسوقين','customers':'أرقام الزباين','developers':'أرقام المطورين'}
    if category not in labels: return redirect(url_for('index'))
    if request.method == 'POST':
        row = Contact(category=category, name=request.form.get('name',''), phone=request.form.get('phone',''), notes=request.form.get('notes',''))
        db.session.add(row); db.session.commit()
        flash('تم حفظ الرقم تلقائياً على السحابة')
        return redirect(url_for('contacts', category=category))
    rows = Contact.query.filter_by(category=category).order_by(Contact.id.desc()).all()
    return render_template('contacts.html', rows=rows, category=category, title=labels[category])

@app.route('/contacts/delete/<int:cid>/<category>', methods=['POST'])
def delete_contact(cid, category):
    row = Contact.query.get_or_404(cid)
    db.session.delete(row); db.session.commit()
    flash('تم حذف الرقم من السحابة')
    return redirect(url_for('contacts', category=category))

@app.route('/send_whatsapp', methods=['POST'])
def send_whatsapp():
    ids = request.form.getlist('selected')
    message = request.form.get('message','')
    category = request.form.get('category','marketers')
    if not ids:
        flash('حدد رقم واحد على الأقل')
        return redirect(url_for('contacts', category=category))
    rows = Contact.query.filter(Contact.id.in_([int(x) for x in ids])).all()
    links = []
    for r in rows:
        phone = ''.join(ch for ch in (r.phone or '') if ch.isdigit())
        if phone.startswith('0'):
            phone = '966' + phone[1:]
        elif phone and not phone.startswith('966'):
            phone = '966' + phone
        if phone:
            links.append({'name': r.name, 'phone': phone, 'url': f'https://wa.me/{phone}?text={urllib.parse.quote(message)}'})
    return render_template('whatsapp_links.html', links=links, message=message)

@app.route('/offers', methods=['GET','POST'])
def offers():
    if request.method == 'POST':
        image_data = ''
        file = request.files.get('image')
        if file and file.filename:
            raw = file.read()
            mime = file.mimetype or 'image/jpeg'
            image_data = f'data:{mime};base64,' + base64.b64encode(raw).decode('utf-8')
        row = Offer(title=request.form.get('title',''), description=request.form.get('description',''), price=request.form.get('price',''), image_data=image_data)
        db.session.add(row); db.session.commit()
        flash('تم إضافة العرض وحفظه تلقائياً على السحابة')
        return redirect(url_for('offers'))
    offers_rows = Offer.query.order_by(Offer.id.desc()).all()
    msg_rows = CustomerMessage.query.order_by(CustomerMessage.id.desc()).all()
    return render_template('offers.html', offers=offers_rows, messages=msg_rows)

@app.route('/messages', methods=['POST'])
def messages():
    row = CustomerMessage(customer_name=request.form.get('customer_name',''), phone=request.form.get('phone',''), message=request.form.get('message',''))
    db.session.add(row); db.session.commit()
    flash('تم حفظ رسالة العميل تلقائياً على السحابة')
    return redirect(url_for('offers'))

@app.route('/offers/delete/<int:oid>', methods=['POST'])
def delete_offer(oid):
    row = Offer.query.get_or_404(oid)
    db.session.delete(row); db.session.commit()
    flash('تم حذف العرض من السحابة')
    return redirect(url_for('offers'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=False)
