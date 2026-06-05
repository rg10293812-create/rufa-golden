import os, urllib.parse, base64
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'rufa-golden-change-me')

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///rufa_golden_cloud.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)

ROLE_LABELS = {
    'admin': 'مدير عام',
    'executive': 'مدير تنفيذي',
    'marketer': 'مسوق',
    'viewer': 'مشاهد'
}

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    full_name = db.Column(db.Text, default='')
    role = db.Column(db.String(20), default='viewer', index=True)
    is_active = db.Column(db.Boolean, default=True)
    can_delete = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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


def ensure_user_permission_columns():
    # create_all لا يضيف الأعمدة الجديدة للجداول القديمة، لذلك نضيفها آلياً عند التشغيل.
    try:
        inspector = db.inspect(db.engine)
        if 'users' not in inspector.get_table_names():
            return
        existing = {c['name'] for c in inspector.get_columns('users')}
        with db.engine.begin() as conn:
            dialect = db.engine.dialect.name
            if 'can_delete' not in existing:
                if dialect == 'postgresql':
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN IF NOT EXISTS can_delete BOOLEAN DEFAULT FALSE'))
                else:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN can_delete BOOLEAN DEFAULT 0'))
            if 'can_manage_users' not in existing:
                if dialect == 'postgresql':
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN IF NOT EXISTS can_manage_users BOOLEAN DEFAULT FALSE'))
                else:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN can_manage_users BOOLEAN DEFAULT 0'))
    except Exception as exc:
        print('Permission column migration warning:', exc)


def init_db():
    db.create_all()
    ensure_user_permission_columns()
    if User.query.count() == 0:
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        admin = User(username=admin_username, full_name='مدير النظام', role='admin', is_active=True, can_delete=True, can_manage_users=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
    else:
        # تأكد أن كل مدير عام موجود لديه الصلاحيات الكاملة.
        changed = False
        for admin in User.query.filter_by(role='admin').all():
            if not getattr(admin, 'can_delete', False):
                admin.can_delete = True; changed = True
            if not getattr(admin, 'can_manage_users', False):
                admin.can_manage_users = True; changed = True
        if changed:
            db.session.commit()

with app.app_context():
    init_db()

@app.context_processor
def inject_user():
    user = None
    uid = session.get('user_id')
    if uid:
        user = User.query.get(uid)
    return dict(current_user=user, role_labels=ROLE_LABELS, can_delete_content=can_delete_content, can_manage_accounts=can_manage_accounts)

def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_active:
            session.clear()
            flash('يرجى تسجيل الدخول أولاً')
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper

def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user or not user.is_active:
                session.clear()
                flash('يرجى تسجيل الدخول أولاً')
                return redirect(url_for('login'))
            if user.role not in roles:
                flash('ليس لديك صلاحية لتنفيذ هذه العملية')
                return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def can_delete_content(user):
    return bool(user and user.is_active and (user.role == 'admin' or getattr(user, 'can_delete', False)))

def can_manage_accounts(user):
    return bool(user and user.is_active and (user.role == 'admin' or getattr(user, 'can_manage_users', False)))

def manage_users_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_active:
            session.clear()
            flash('يرجى تسجيل الدخول أولاً')
            return redirect(url_for('login'))
        if not can_manage_accounts(user):
            flash('ليس لديك صلاحية إدارة المستخدمين')
            return redirect(url_for('index'))
        return fn(*args, **kwargs)
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.is_active and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('تم تسجيل الدخول بنجاح')
            return redirect(url_for('index'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج')
    return redirect(url_for('login'))

@app.route('/users', methods=['GET', 'POST'])
@login_required
@manage_users_required
def users():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'viewer')
        if role not in ROLE_LABELS:
            role = 'viewer'
        if not username or not password:
            flash('اسم المستخدم وكلمة المرور مطلوبة')
            return redirect(url_for('users'))
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود مسبقاً')
            return redirect(url_for('users'))
        can_delete = request.form.get('can_delete') == 'on'
        can_manage_users = request.form.get('can_manage_users') == 'on'
        if role == 'admin':
            can_delete = True
            can_manage_users = True
        user = User(username=username, full_name=full_name, role=role, is_active=True, can_delete=can_delete, can_manage_users=can_manage_users)
        user.set_password(password)
        db.session.add(user); db.session.commit()
        flash('تم إضافة المستخدم بنجاح')
        return redirect(url_for('users'))
    rows = User.query.order_by(User.id.desc()).all()
    return render_template('users.html', rows=rows, roles=ROLE_LABELS)

@app.route('/users/delete/<int:uid>', methods=['POST'])
@login_required
@manage_users_required
def delete_user(uid):
    current = get_current_user()
    if current and current.id == uid:
        flash('لا يمكنك حذف حسابك الحالي')
        return redirect(url_for('users'))
    user = User.query.get_or_404(uid)
    db.session.delete(user); db.session.commit()
    flash('تم حذف المستخدم')
    return redirect(url_for('users'))

@app.route('/users/toggle/<int:uid>', methods=['POST'])
@login_required
@manage_users_required
def toggle_user(uid):
    current = get_current_user()
    if current and current.id == uid:
        flash('لا يمكنك تعطيل حسابك الحالي')
        return redirect(url_for('users'))
    user = User.query.get_or_404(uid)
    user.is_active = not user.is_active
    db.session.commit()
    flash('تم تحديث حالة المستخدم')
    return redirect(url_for('users'))

@app.route('/users/permissions/<int:uid>', methods=['POST'])
@login_required
@manage_users_required
def update_user_permissions(uid):
    current = get_current_user()
    user = User.query.get_or_404(uid)
    role = request.form.get('role', user.role)
    if role not in ROLE_LABELS:
        role = user.role
    # لا تجعل المدير الحالي يفقد صلاحياته بالخطأ.
    if current and current.id == uid and user.role == 'admin':
        role = 'admin'
    user.role = role
    user.can_delete = request.form.get('can_delete') == 'on'
    user.can_manage_users = request.form.get('can_manage_users') == 'on'
    user.is_active = request.form.get('is_active') == 'on'
    if user.role == 'admin':
        user.can_delete = True
        user.can_manage_users = True
        user.is_active = True
    db.session.commit()
    flash('تم تحديث صلاحيات المستخدم')
    return redirect(url_for('users'))

@app.route('/')
def landing():
    user = get_current_user()
    if user and user.is_active:
        return redirect(url_for('index'))
    return render_template('landing.html')

@app.route('/member')
def member_entry():
    return redirect(url_for('login'))

@app.route('/visitor')
def visitor_offers():
    offers_rows = Offer.query.order_by(Offer.id.desc()).all()
    return render_template('visitor_offers.html', offers=offers_rows)

@app.route('/dashboard')
@login_required
def index():
    return render_template('index.html')

@app.route('/properties', methods=['GET','POST'])
@login_required
def properties():
    user = get_current_user()
    if request.method == 'POST':
        if user.role not in ['admin', 'executive', 'marketer']:
            flash('ليس لديك صلاحية إضافة عقار')
            return redirect(url_for('properties'))
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
@login_required
def property_detail(pid):
    row = Property.query.get_or_404(pid)
    return render_template('property_detail.html', row=row)

@app.route('/properties/delete/<int:pid>', methods=['POST'])
@login_required
def delete_property(pid):
    if not can_delete_content(get_current_user()):
        flash('ليس لديك صلاحية الحذف')
        return redirect(url_for('properties'))
    row = Property.query.get_or_404(pid)
    db.session.delete(row); db.session.commit()
    flash('تم حذف العقار من السحابة')
    return redirect(url_for('properties'))

@app.route('/contacts/<category>', methods=['GET','POST'])
@login_required
def contacts(category):
    user = get_current_user()
    labels = {'marketers':'أرقام المسوقين','customers':'أرقام الزباين','developers':'أرقام المطورين'}
    if category not in labels: return redirect(url_for('index'))
    if request.method == 'POST':
        if user.role not in ['admin', 'executive', 'marketer']:
            flash('ليس لديك صلاحية إضافة رقم')
            return redirect(url_for('contacts', category=category))
        row = Contact(category=category, name=request.form.get('name',''), phone=request.form.get('phone',''), notes=request.form.get('notes',''))
        db.session.add(row); db.session.commit()
        flash('تم حفظ الرقم تلقائياً على السحابة')
        return redirect(url_for('contacts', category=category))
    rows = Contact.query.filter_by(category=category).order_by(Contact.id.desc()).all()
    return render_template('contacts.html', rows=rows, category=category, title=labels[category])

@app.route('/contacts/delete/<int:cid>/<category>', methods=['POST'])
@login_required
def delete_contact(cid, category):
    if not can_delete_content(get_current_user()):
        flash('ليس لديك صلاحية الحذف')
        return redirect(url_for('contacts', category=category))
    row = Contact.query.get_or_404(cid)
    db.session.delete(row); db.session.commit()
    flash('تم حذف الرقم من السحابة')
    return redirect(url_for('contacts', category=category))

@app.route('/send_whatsapp', methods=['POST'])
@login_required
def send_whatsapp():
    user = get_current_user()
    if user.role not in ['admin', 'executive', 'marketer']:
        flash('ليس لديك صلاحية إرسال رسائل واتساب')
        return redirect(url_for('index'))
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
@login_required
def offers():
    user = get_current_user()
    if request.method == 'POST':
        if user.role not in ['admin', 'executive', 'marketer']:
            flash('ليس لديك صلاحية إضافة عرض')
            return redirect(url_for('offers'))
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
@login_required
def messages():
    user = get_current_user()
    if user.role not in ['admin', 'executive', 'marketer']:
        flash('ليس لديك صلاحية حفظ رسائل العملاء')
        return redirect(url_for('offers'))
    row = CustomerMessage(customer_name=request.form.get('customer_name',''), phone=request.form.get('phone',''), message=request.form.get('message',''))
    db.session.add(row); db.session.commit()
    flash('تم حفظ رسالة العميل تلقائياً على السحابة')
    return redirect(url_for('offers'))

@app.route('/offers/delete/<int:oid>', methods=['POST'])
@login_required
def delete_offer(oid):
    if not can_delete_content(get_current_user()):
        flash('ليس لديك صلاحية الحذف')
        return redirect(url_for('offers'))
    row = Offer.query.get_or_404(oid)
    db.session.delete(row); db.session.commit()
    flash('تم حذف العرض من السحابة')
    return redirect(url_for('offers'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=False)
