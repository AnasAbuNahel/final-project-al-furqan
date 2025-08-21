from app import app, db, User, Tenant
from werkzeug.security import generate_password_hash

def create_tenant_with_user():
    # بيانات الجهة ثابتة
    tenant_name = "systeam"
    tenant_slug = "am"

    # تحقق إذا الجهة موجودة مسبقًا
    existing_tenant = Tenant.query.filter_by(slug=tenant_slug).first()
    if existing_tenant:
        print(f"⚠️ الجهة '{tenant_name}' موجودة مسبقًا (ID={existing_tenant.id})")
        new_tenant = existing_tenant
    else:
        # إنشاء الجهة
        new_tenant = Tenant(name=tenant_name, slug=tenant_slug)
        db.session.add(new_tenant)
        db.session.commit()
        print(f"✅ تم إنشاء الجهة '{tenant_name}' (ID={new_tenant.id})")

    # بيانات المستخدم ثابتة
    username = "AnasAbuNahel"
    password = "Anas407923630.0"
    role = "user"

    # تحقق إذا المستخدم موجود مسبقًا
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"⚠️ المستخدم '{username}' موجود مسبقًا (ID={existing_user.id})")
    else:
        # إنشاء الحساب
        hashed_pw = generate_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_pw,
            role=role,
            tenant_id=new_tenant.id
        )
        db.session.add(new_user)
        db.session.commit()
        print(f"✅ تم إنشاء الحساب '{username}' بدور '{role}' للجهة '{tenant_name}'\n")
        print("➡️ الآن يمكنك تسجيل الدخول من الواجهة باستخدام هذا الحساب.")

if __name__ == "__main__":
    with app.app_context():
        create_tenant_with_user()
