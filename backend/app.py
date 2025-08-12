from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
from sqlalchemy import func, delete
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
import jwt
from datetime import datetime, timedelta
from io import BytesIO
import json
import pandas as pd
import pytz

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["https://final-project-al-furqan.vercel.app"])

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://db_al_furqan_final_project_user:i8nLtHzu95NBWsLngEBFLHxOpUCpvY4q@dpg-d2ds0dq4d50c73bj3kfg-a/db_al_furqan_final_project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'furqan-secret-key'

db = SQLAlchemy(app)

# ==================== نموذج الجهات (Tenants) ====================
class Tenant(db.Model):
    __tablename__ = 'tenant'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TenantMixin:
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False, index=True)

# ====== النماذج ======
class Resident(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    husband_name = db.Column(db.String(100), nullable=True)
    husband_id_number = db.Column(db.String(20), nullable=True)
    wife_name = db.Column(db.String(100), nullable=True)
    wife_id_number = db.Column(db.String(20), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    num_family_members = db.Column(db.Integer, nullable=True)
    injuries = db.Column(db.String(200), nullable=True)
    diseases = db.Column(db.String(200), nullable=True)
    damage_level = db.Column(db.String(200), nullable=True)
    neighborhood = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.String(300), nullable=True)
    has_received_aid = db.Column(db.Boolean, default=False)

    aids = db.relationship('Aid', backref='resident', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'husband_name': self.husband_name,
            'husband_id_number': self.husband_id_number,
            'wife_name': self.wife_name,
            'wife_id_number': self.wife_id_number,
            'phone_number': self.phone_number,
            'num_family_members': self.num_family_members,
            'injuries': self.injuries,
            'diseases': self.diseases,
            'damage_level': self.damage_level,
            'neighborhood': self.neighborhood,
            'notes': self.notes,
            'has_received_aid': self.has_received_aid,
            'tenant_id': self.tenant_id
        }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="admin")
    permissions = db.Column(db.Text, nullable=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)

    def check_password(self, password, check_fn=None):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(password)

class Aid(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey('resident.id'), nullable=False)
    aid_type = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'resident_id': self.resident_id,
            'aid_type': self.aid_type,
            'date': self.date,
            'tenant_id': self.tenant_id,
            'resident': {
                'husband_name': self.resident.husband_name if self.resident else None,
                'husband_id_number': self.resident.husband_id_number if self.resident else None
            }
        }

# ==================== نموذج الأطفال ====================
class Child(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    id_number = db.Column(db.String(50), nullable=False)
    birth_date = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    benefit_type = db.Column(db.String(100), nullable=False)
    benefit_count = db.Column(db.Integer, default=0)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'id_number': self.id_number,
            'birth_date': self.birth_date,
            'age': self.age,
            'phone': self.phone,
            'gender': self.gender,
            'benefit_type': self.benefit_type,
            'benefit_count': self.benefit_count,
            'tenant_id': self.tenant_id
        }

class Assistance(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    help_type = db.Column(db.String(100), nullable=False)
    other_help = db.Column(db.String(255), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    child = db.relationship('Child', backref=db.backref('assistance', lazy=True))

# ==================== المسارات ====================

# -- مساعدة توكين بسيط (بدون مكتبة خارجية)
def generate_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'tenant_id': user.tenant_id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token مطلوب'}), 401
        token = token.replace("Bearer ", "")
        user_data = verify_token(token)
        if not user_data:
            return jsonify({'error': 'Token غير صالح أو منتهي'}), 401
        request.user = user_data
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'user') or request.user.get('role') != 'admin':
            return jsonify({'error': 'صلاحيات المدير فقط'}), 403
        return f(*args, **kwargs)
    return decorated

# ====== المسارات: أطفال ======
@app.route('/api/children', methods=['GET'])
@login_required
def get_all_children():
    tenant_id = request.user['tenant_id']
    children = Child.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([child.serialize() for child in children])

@app.route('/api/children', methods=['POST'])
@login_required
def add_child():
    tenant_id = request.user['tenant_id']
    data = request.get_json()

    if not all([data.get('name'), data.get('id_number'), data.get('birth_date'),
                data.get('age'), data.get('phone'), data.get('gender'), data.get('benefit_type')]):
        return jsonify({"message": "Missing required fields!"}), 422

    existing = Child.query.filter_by(id_number=data['id_number'], tenant_id=tenant_id).first()
    if existing:
        return jsonify({"message": "الطفل موجود بالفعل!"}), 400

    new_child = Child(
        name=data['name'],
        id_number=data['id_number'],
        birth_date=data['birth_date'],
        age=int(data['age']),
        phone=data['phone'],
        gender=data['gender'],
        benefit_type=data['benefit_type'],
        benefit_count=int(data.get('benefit_count', 0)),
        tenant_id=tenant_id
    )

    db.session.add(new_child)
    db.session.commit()

    log_action({
        'user_id': request.user['user_id'],
        'username': request.user['username'],
        'tenant_id': tenant_id
    }, f"تم إضافة الطفل {new_child.name}", target_name=new_child.name)

    return jsonify(new_child.serialize()), 201

@app.route('/api/children/<int:id>', methods=['PUT'])
@login_required
def update_child(id):
    tenant_id = request.user['tenant_id']
    child = Child.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()

    data = request.get_json()
    child.name = data.get("name", child.name)
    child.id_number = data.get("id_number", child.id_number)
    child.birth_date = data.get("birth_date", child.birth_date)
    child.age = int(data.get("age", child.age))
    child.phone = data.get("phone", child.phone)
    child.gender = data.get("gender", child.gender)
    child.benefit_type = data.get("benefit_type", child.benefit_type)
    child.benefit_count = int(data.get("benefit_count", child.benefit_count))

    db.session.commit()

    log_action({
        'user_id': request.user['user_id'],
        'username': request.user['username'],
        'tenant_id': tenant_id
    }, f"تم تعديل بيانات الطفل {child.name}", target_name=child.name)

    return jsonify(child.serialize())

@app.route('/api/children/<string:id_number>', methods=['DELETE'])
@login_required
def delete_child(id_number):
    tenant_id = request.user['tenant_id']
    child = Child.query.filter_by(id_number=id_number, tenant_id=tenant_id).first()

    if not child:
        return jsonify({"message": "الطفل غير موجود!"}), 404

    db.session.delete(child)
    db.session.commit()

    log_action({
        'user_id': request.user['user_id'],
        'username': request.user['username'],
        'tenant_id': tenant_id
    }, f"تم حذف الطفل {child.name}", target_name=child.name)

    return jsonify({"message": "تم حذف السجل بنجاح!"}), 200

# إضافة مساعدة لطفل (Assistance)
@app.route('/api/assistance', methods=['POST'])
@login_required
def add_assistance():
    tenant_id = request.user['tenant_id']
    data = request.get_json()

    if not all([data.get('child_id'), data.get('help_type')]):
        return jsonify({"message": "Missing required fields!"}), 422

    child = Child.query.filter_by(id=data['child_id'], tenant_id=tenant_id).first()
    if not child:
        return jsonify({"message": "الطفل غير موجود!"}), 404

    new_assistance = Assistance(
        child_id=child.id,
        help_type=data['help_type'],
        other_help=data.get('other_help'),
        tenant_id=tenant_id
    )

    child.benefit_count = (child.benefit_count or 0) + 1
    db.session.add(new_assistance)
    db.session.commit()

    log_action({
        'user_id': request.user['user_id'],
        'username': request.user['username'],
        'tenant_id': tenant_id
    }, f"تم إضافة مساعدة {data['help_type']} للطفل {child.name}", target_name=child.name)

    return jsonify({"message": "تم إضافة المساعدة بنجاح!"}), 201

@app.route('/api/children/<int:id>/last_assistance', methods=['GET'])
@login_required
def get_last_assistance(id):
    tenant_id = request.user['tenant_id']
    child = Child.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()

    last_assistance = Assistance.query.filter_by(
        child_id=id, tenant_id=tenant_id
    ).order_by(Assistance.date_added.desc()).first()

    if not last_assistance:
        return jsonify({"message": "الطفل لم يستفد من أي مساعدة بعد"}), 404

    return jsonify({
        "child_id": child.id,
        "child_name": child.name,
        "last_assistance": {
            "help_type": last_assistance.help_type,
            "other_help": last_assistance.other_help,
            "date_added": last_assistance.date_added.isoformat()
        }
    })

# تصدير بيانات الأطفال
@app.route('/api/export_children', methods=['GET'])
@login_required
def export_children():
    tenant_id = request.user['tenant_id']
    children = Child.query.filter_by(tenant_id=tenant_id).all()
    children_data = [child.serialize() for child in children]
    df = pd.DataFrame(children_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Children')
    output.seek(0)

    return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     download_name="children.xlsx", as_attachment=True)

# استيراد بيانات الأطفال (من ملف إكسل)
@app.route('/api/import_children', methods=['POST'])
@login_required
def import_children():
    tenant_id = request.user['tenant_id']
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400

    file = request.files['file']
    imported_count, ignored_count = 0, 0

    try:
        df = pd.read_excel(file)
        required_cols = ['name', 'id_number', 'birth_date', 'age', 'phone', 'gender', 'benefit_type']
        # تأكد وجود الأعمدة المطلوبة
        for col in required_cols:
            if col not in df.columns:
                return jsonify({'message': f'Missing required column: {col}'}), 400

        for _, row in df.iterrows():
            if not all(pd.notnull(row[c]) for c in required_cols):
                ignored_count += 1
                continue

            existing = Child.query.filter_by(
                id_number=str(row['id_number']).strip(),
                tenant_id=tenant_id
            ).first()
            if existing:
                ignored_count += 1
                continue

            new_child = Child(
                name=str(row['name']).strip(),
                id_number=str(row['id_number']).strip(),
                birth_date=str(row['birth_date']),
                age=int(row['age']),
                phone=str(row['phone']).strip(),
                gender=str(row['gender']).strip(),
                benefit_type=str(row['benefit_type']).strip(),
                benefit_count=int(row.get('benefit_count', 0) or 0),
                tenant_id=tenant_id
            )
            db.session.add(new_child)
            imported_count += 1

        db.session.commit()

        log_action({
            'user_id': request.user['user_id'],
            'username': request.user['username'],
            'tenant_id': tenant_id
        }, f"تم استيراد {imported_count} طفلًا وتجاهل {ignored_count} بسبب بيانات غير مكتملة", target_name=None)

        return jsonify({'message': f'Data imported successfully! Imported: {imported_count}, Ignored: {ignored_count}'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred during import: {str(e)}'}), 500

# ====== نموذج الإشعارات ======
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    action = db.Column(db.String(300), nullable=False)
    target_name = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(pytz.timezone('Asia/Gaza'))
    )

    def serialize(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'target_name': self.target_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

def log_action(user_info, action, target_name=None):
    try:
        notification = Notification(
            tenant_id=user_info['tenant_id'],
            user_id=user_info['user_id'],
            username=user_info['username'],
            action=action,
            target_name=target_name
        )
        db.session.add(notification)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()

# ====== نماذج Import & Export ======
class Import(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'source': self.source,
            'name': self.name,
            'date': self.date,
            'type': self.type,
            'amount': self.amount
        }

class Export(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'description': self.description,
            'amount': self.amount,
            'date': self.date
        }

with app.app_context():
    db.create_all()

# ====== مسارات تسجيل الدخول وإدارة المستخدم ======
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Bad request'}), 400
    user = User.query.filter_by(username=data.get('username')).first()
    if user and user.check_password(data.get('password')):
        token = generate_token(user)
        permissions = {}
        try:
            permissions = json.loads(user.permissions or '{}')
        except Exception:
            permissions = {}

        log_action({
        'user_id': user.id,
        'username': user.username,
        'tenant_id': user.tenant_id
        }, "تم تسجيل دخول المستخدم")


        return jsonify({
            'success': True,
            'token': token,
            'role': user.role,
            'permissions': permissions
        })
    return jsonify({'success': False, 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401


@app.route('/api/user/update_credentials', methods=['PUT'])
@login_required
def update_credentials():
    user = User.query.get(request.user['user_id'])
    data = request.get_json()
    if 'username' in data:
        user.username = data['username']
    if 'password' in data:
        user.set_password(data['password'])
    db.session.commit()
    log_action(request.user, "تحديث بيانات الدخول", request.user['username'])
    return jsonify({'message': 'تم تحديث البيانات بنجاح'})

@app.route('/api/user/update_permissions/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_permissions(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.permissions = json.dumps(data.get('permissions', {}))
    db.session.commit()
    log_action(request.user, f"تحديث صلاحيات المستخدم {user.username}", user.username)
    return jsonify({'message': 'تم تحديث الصلاحيات بنجاح'})

# ====== إدارة المستفيدين ======
@app.route('/api/residents', methods=['GET'])
@login_required
def get_residents():
    residents = Resident.query.filter_by(tenant_id=request.user['tenant_id']).all()
    return jsonify([r.serialize() for r in residents])

@app.route('/api/residents', methods=['POST'])
@login_required
def add_resident():
    data = request.get_json() or {}
    existing = Resident.query.filter(
        Resident.tenant_id == request.user['tenant_id'],
        ((Resident.husband_id_number == data.get('husband_id_number')) |
         (Resident.wife_id_number == data.get('wife_id_number')) |
         (Resident.phone_number == data.get('phone_number')))
    ).first()
    if existing:
        return jsonify({'error': 'مستفيد بنفس البيانات موجود بالفعل'}), 400

    data['tenant_id'] = request.user['tenant_id']
    resident = Resident(**data)
    db.session.add(resident)
    db.session.commit()

    log_action(request.user, "أضاف مستفيد جديد", f"{resident.husband_name} / {resident.wife_name}")
    return jsonify({'message': 'تمت الإضافة بنجاح'})

@app.route('/api/residents/<int:resident_id>', methods=['PUT'])
@login_required
def update_resident(resident_id):
    resident = Resident.query.filter_by(id=resident_id, tenant_id=request.user['tenant_id']).first_or_404()
    for key, value in (request.get_json() or {}).items():
        setattr(resident, key, value)
    db.session.commit()

    log_action(request.user, "حدث بيانات المستفيد", f"{resident.husband_name} / {resident.wife_name}")
    return jsonify({'message': 'تم التحديث بنجاح'})

@app.route('/api/residents/<int:resident_id>', methods=['DELETE'])
@login_required
def delete_resident(resident_id):
    resident = Resident.query.filter_by(id=resident_id, tenant_id=request.user['tenant_id']).first_or_404()
    name = f"{resident.husband_name} / {resident.wife_name}"
    db.session.delete(resident)
    db.session.commit()

    log_action(request.user, "حذف مستفيد", name)
    return jsonify({'message': 'تم الحذف بنجاح'})

@app.route('/api/residents/delete_all', methods=['DELETE'])
@login_required
@admin_required
def delete_all_residents():
    Resident.query.filter_by(tenant_id=request.user['tenant_id']).delete()
    db.session.commit()
    log_action(request.user, "حذف جميع المستفيدين")
    return jsonify({'message': 'تم حذف جميع المستفيدين'})

# ====== إدارة المساعدات (Aids) ======
@app.route('/api/aids', methods=['GET', 'POST'])
@login_required
def manage_aids():
    if request.method == 'POST':
        data = request.get_json() or {}
        resident = Resident.query.filter_by(id=data.get('resident_id'), tenant_id=request.user['tenant_id']).first()
        if not resident:
            return jsonify({'error': 'المستفيد غير موجود'}), 404

        aid = Aid(resident_id=resident.id, aid_type=data.get('aid_type'), date=data.get('date'), tenant_id=request.user['tenant_id'])
        resident.has_received_aid = True

        db.session.add(aid)
        db.session.commit()

        log_action(request.user, f"اضافة مساعدة ({aid.aid_type}) للمستفيد", resident.husband_name)
        return jsonify({'message': 'تمت إضافة المساعدة بنجاح'})

    aids = Aid.query.join(Resident).filter(Resident.tenant_id == request.user['tenant_id']).all()
    return jsonify([a.serialize() for a in aids])

# ====== استيراد ملف اكسل المساعدات (مُحسّن باستخدام pandas) ======
@app.route('/importt_excel', methods=['POST'])
@login_required
def importt_excel():
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400

    file = request.files['file']
    try:
        df = pd.read_excel(file)
    except Exception as e:
        return jsonify({'message': f'Failed to read Excel file: {str(e)}'}), 400

    required_cols = ['husband_name', 'husband_id_number', 'aid_type', 'date']
    # حاول قبول أعمدة بأسماء عربية أو إنجليزية : إذا لم تكن موجودة، حاول البحث عن أسماء شائعة
    # لكن هنا نتحقق مباشرة
    for col in required_cols:
        if col not in df.columns:
            return jsonify({'message': f'Missing required column: {col}'}), 400

    new_aids_count = 0
    skipped_aids_count = 0

    for _, row in df.iterrows():
        husband_name = str(row['husband_name']).strip()
        husband_id_number = str(row['husband_id_number']).strip()
        aid_type = str(row['aid_type']).strip()
        date = str(row['date']).strip()

        resident = Resident.query.filter_by(
            husband_name=husband_name,
            husband_id_number=husband_id_number,
            tenant_id=request.user['tenant_id']
        ).first()

        if not resident:
            skipped_aids_count += 1
            continue

        existing_aid = Aid.query.filter_by(resident_id=resident.id, aid_type=aid_type, date=date).first()
        if existing_aid:
            skipped_aids_count += 1
            continue

        db.session.add(Aid(resident_id=resident.id, aid_type=aid_type, date=date, tenant_id=request.user['tenant_id']))
        new_aids_count += 1

    db.session.commit()
    log_action(request.user, f"استيراد مساعدات جديدة: {new_aids_count}، تم تخطي {skipped_aids_count}")
    return jsonify({
        'message': f'تم استيراد {new_aids_count} مساعدة بنجاح، تم تخطي {skipped_aids_count} مساعدة بسبب التكرار أو عدم وجود المقيم.'
    }), 200

@app.route('/api/residents/search', methods=['GET', 'OPTIONS'])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@login_required
def search_resident_by_name_and_id():
    name = request.args.get('name')
    id_number = request.args.get('id')

    if not name or not id_number:
        return jsonify({'error': 'الاسم والهوية مطلوبان'}), 400

    resident = Resident.query.filter_by(
        husband_name=name,
        husband_id_number=id_number,
        tenant_id=request.user['tenant_id']
    ).first()

    if not resident:
        return jsonify({'error': 'المستفيد غير موجود'}), 404

    return jsonify({'id': resident.id, 'name': resident.husband_name})

@app.route('/api/aids/<int:aid_id>', methods=['PUT'])
@login_required
def update_aid(aid_id):
    aid = Aid.query.get_or_404(aid_id)
    if aid.tenant_id != request.user['tenant_id']:
        return jsonify({'error': 'غير مصرح لك بتعديل هذه المساعدة'}), 403

    for key, value in (request.get_json() or {}).items():
        setattr(aid, key, value)
    db.session.commit()

    log_action(request.user, "حدث بيانات المساعدة", aid.resident.husband_name if aid.resident else None)
    return jsonify({'message': 'تم تحديث المساعدة بنجاح'})

@app.route('/api/aids/<int:aid_id>', methods=['DELETE'])
@login_required
def delete_aid(aid_id):
    aid = Aid.query.get_or_404(aid_id)
    if aid.tenant_id != request.user['tenant_id']:
        return jsonify({'error': 'غير مصرح لك بحذف هذه المساعدة'}), 403

    resident_name = aid.resident.husband_name if aid.resident else None
    db.session.delete(aid)

    aids_left = Aid.query.filter_by(resident_id=aid.resident_id).count()
    if aids_left <= 1 and aid.resident:
        aid.resident.has_received_aid = False

    db.session.commit()

    log_action(request.user, "حذف مساعدة", resident_name)
    return jsonify({'message': 'تم حذف المساعدة بنجاح'})

# ====== جلب الإشعارات ======
@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    # استخدم نفس المنطقة الزمنية كما في الافتراضي عند الإدراج
    week_ago = datetime.now(pytz.timezone('Asia/Gaza')) - timedelta(days=7)

    # حذف الإشعارات الأقدم من 7 أيام لجهة المستخدم فقط
    stmt = delete(Notification).where(Notification.timestamp < week_ago).where(Notification.tenant_id == request.user['tenant_id'])
    db.session.execute(stmt)
    db.session.commit()

    notifications = Notification.query.filter_by(
        tenant_id=request.user['tenant_id']
    ).order_by(Notification.timestamp.desc()).limit(100).all()
    return jsonify([n.serialize() for n in notifications])

# ====== تحميل وتصدير المستفيدين ======
@app.route('/api/export_residents', methods=['GET'])
@login_required
def export_residents():
    residents = Resident.query.filter_by(tenant_id=request.user['tenant_id']).all()
    data = [r.serialize() for r in residents]
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Residents')
    output.seek(0)
    return send_file(output, download_name="residents.xlsx", as_attachment=True)

@app.route('/api/residents/import', methods=['POST'])
@login_required
def import_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'لم يتم إرسال ملف'}), 400

    file = request.files['file']

    try:
        df = pd.read_excel(file)

        field_map = {
            'اسم الزوج': 'husband_name',
            'رقم هوية الزوج': 'husband_id_number',
            'اسم الزوجة': 'wife_name',
            'رقم هوية الزوجة': 'wife_id_number',
            'رقم الهاتف': 'phone_number',
            'عدد الأفراد': 'num_family_members',
            'الإصابات': 'injuries',
            'الأمراض': 'diseases',
            'الضرر': 'damage_level',
            'المندوب': 'neighborhood',
            'ملاحظات': 'notes',
            'استلم مساعدة': 'has_received_aid'
        }

        df.rename(columns=field_map, inplace=True)
        allowed_fields = set(field_map.values())

        existing_ids = set(
            db.session.query(Resident.husband_id_number, Resident.wife_id_number)
            .filter(Resident.tenant_id == request.user['tenant_id'])
            .all()
        )
        existing_ids_flat = set()
        for h_id, w_id in existing_ids:
            if h_id: existing_ids_flat.add(str(h_id).strip())
            if w_id: existing_ids_flat.add(str(w_id).strip())

        count = 0
        skipped = 0

        for _, row in df.iterrows():
            record = {k: v for k, v in row.to_dict().items() if k in allowed_fields}

            if 'has_received_aid' in record:
                value = str(record['has_received_aid']).strip()
                record['has_received_aid'] = value in ['نعم', 'yes', 'Yes', '1', 'true', 'True']

            h_id = str(record.get('husband_id_number', '')).strip()
            w_id = str(record.get('wife_id_number', '')).strip()

            if h_id in existing_ids_flat or w_id in existing_ids_flat:
                skipped += 1
                continue

            record['tenant_id'] = request.user['tenant_id']
            resident = Resident(**record)
            db.session.add(resident)
            count += 1

        db.session.commit()

        log_action(request.user, f"استورد ملف مستفيدين ({count} سجل، تم تجاهل {skipped} مكرر)")

        return jsonify({'message': f'تم استيراد {count} مستفيد بنجاح، تم تجاهل {skipped} سجل مكرر'})

    except Exception as e:
        return jsonify({'error': f'حدث خطأ أثناء الاستيراد: {str(e)}'}), 500

# ====== الإحصائيات ======
@app.route('/api/residents/stats', methods=['GET'])
@login_required
def get_residents_stats():
    tenant_id = request.user['tenant_id']

    total_residents = db.session.query(func.count(Resident.id))\
        .filter(Resident.tenant_id == tenant_id).scalar()

    total_beneficiaries = db.session.query(func.count(Resident.id))\
        .filter(Resident.has_received_aid == True, Resident.tenant_id == tenant_id).scalar()

    total_non_beneficiaries = db.session.query(func.count(Resident.id))\
        .filter(Resident.has_received_aid == False, Resident.tenant_id == tenant_id).scalar()

    total_full_damage = db.session.query(func.count(Resident.id))\
        .filter(Resident.damage_level == 'كلي', Resident.tenant_id == tenant_id).scalar()

    total_severe_partial_damage = db.session.query(func.count(Resident.id))\
        .filter(Resident.damage_level == 'جزئي بليغ', Resident.tenant_id == tenant_id).scalar()

    total_partial_damage = db.session.query(func.count(Resident.id))\
        .filter(Resident.damage_level == 'طفيف', Resident.tenant_id == tenant_id).scalar()

    total_no_damage = (total_residents or 0) - (
        (total_full_damage or 0) + (total_severe_partial_damage or 0) + (total_partial_damage or 0)
    )

    stats = {
        "total_residents": total_residents or 0,
        "total_aids": total_beneficiaries or 0,
        "total_beneficiaries": total_beneficiaries or 0,
        "total_non_beneficiaries": total_non_beneficiaries or 0,
        "total_full_damage": total_full_damage or 0,
        "total_severe_partial_damage": total_severe_partial_damage or 0,
        "total_partial_damage": total_partial_damage or 0,
        "total_no_damage": total_no_damage or 0,
    }

    return jsonify(stats)

# ====== إدارة المستخدمين (مشرفين) ======
@app.route('/api/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'يجب إدخال اسم المستخدم وكلمة المرور'}), 400

    if User.query.filter_by(username=username, tenant_id=request.user['tenant_id']).first():
        return jsonify({'error': 'اسم المستخدم مستخدم بالفعل'}), 400

    new_user = User(username=username, role='supervisor', tenant_id=request.user['tenant_id'])
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()
    log_action(request.user, "إضافة مشرف جديد", username)
    return jsonify({
        'id': new_user.id,
        'username': new_user.username,
        'role': new_user.role
    }), 201

@app.route('/api/supervisors', methods=['GET'])
@login_required
@admin_required
def get_supervisors():
    supervisors = User.query.filter_by(role='supervisor', tenant_id=request.user['tenant_id']).all()
    return jsonify([
        {'id': s.id, 'username': s.username}
        for s in supervisors
    ])

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.filter_by(id=user_id, tenant_id=request.user['tenant_id']).first_or_404()

    if user.role != 'supervisor':
        return jsonify({'error': 'لا يمكن حذف المدير أو مستخدم غير مشرف'}), 400

    username = user.username
    db.session.delete(user)
    db.session.commit()
    log_action(request.user, "حذف مشرف", username)
    return jsonify({'message': 'تم حذف المشرف بنجاح'})

# ====== واردات وصادرات ======
@app.route('/api/imports', methods=['GET'])
@login_required
def list_imports():
    imports = Import.query.filter_by(tenant_id=request.user['tenant_id']).all()
    return jsonify([imp.serialize() for imp in imports])

# ================= واردات  ======================
@app.route('/api/imports', methods=['POST'])
@login_required
def add_import():
    data = request.get_json() or {}
    new_import = Import(
        source=data.get('source'),
        name=data.get('name'),
        date=data.get('date'),
        type=data.get('type'),
        amount=float(data.get('amount') or 0),
        tenant_id=request.user['tenant_id']
    )
    db.session.add(new_import)
    db.session.commit()
    log_action(request.user, f"إضافة وارد جديد ({new_import.name})", new_import.name)
    return jsonify(new_import.serialize()), 201

@app.route('/api/exports', methods=['GET'])
@login_required
def list_exports():
    exports = Export.query.filter_by(tenant_id=request.user['tenant_id']).all()
    return jsonify([exp.serialize() for exp in exports])


# ===============  صادرات ===================
@app.route('/api/exports', methods=['POST'])
@login_required
def add_export():
    data = request.get_json() or {}
    new_export = Export(
        description=data.get('description'),
        amount=float(data.get('amount') or 0),
        date=data.get('date'),
        tenant_id=request.user['tenant_id']
    )
    db.session.add(new_export)
    db.session.commit()
    log_action(request.user, f"إضافة صادر جديد ({new_export.description})", new_export.description)
    return jsonify(new_export.serialize()), 201



# ====== نقطة بداية ======
if __name__ == '__main__':
    app.run(debug=True)
