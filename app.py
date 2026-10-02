from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, ProductImage, Reservation, Message, MessagePermission, Worker
from datetime import date, datetime, timedelta
import os
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from flask_babel import Babel, _
from sqlalchemy import inspect, text, or_, and_
from hmac import compare_digest
import secrets
import time
import random
import uuid
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_super_secret_key')
# DATABASE_URL enables PostgreSQL while keeping SQLite as a local fallback.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cropflow.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('COOKIE_SECURE', '0') == '1'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=14)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

# Babel configuration
app.config['BABEL_DEFAULT_LOCALE'] = 'ar'

def get_locale():
    return session.get('lang', 'ar')

babel = Babel(app, locale_selector=get_locale)

TRANSLATIONS = {
    'Edit Profile': 'تعديل الملف الشخصي',
    'Products': 'المحاصيل',
    'Delete this crop?': 'حذف هذا المحصول؟',
    'Product deleted successfully.': 'تم حذف المحصول بنجاح.',
    'Crop added successfully.': 'تمت إضافة المحصول بنجاح.',
    'Invalid input. Check quantities and dates.': 'مدخلات خاطئة. تحقق من الكميات والتواريخ.',
    'List your supply and let buyers know what is available.': 'اعرض منتجاتك ودع المشترين يعرفون ما هو متاح.',
    'Add Product': 'إضافة محصول',
    'Search...': 'بحث...',
    'Edit': 'تعديل',
    'Delete': 'حذف',
    'Image attached': 'صورة مرفقة',
    'Voice message': 'رسالة صوتية',
    'Attach image': 'إرفاق صورة',
    'Record voice': 'تسجيل صوتي',
    'Login with Terralogic': 'تسجيل الدخول بواسطة Terralogic',
    'YOUR ACCOUNT': 'حسابك', 'Settings': 'الإعدادات',
    'Manage your profile, appearance and privacy.': 'إدارة ملفك الشخصي والمظهر والخصوصية.',
    'Account details': 'تفاصيل الحساب',
    'Edit your name, photo, location and profile.': 'تعديل اسمك وصورتك وموقعك وملفك الشخصي.',
    'Shopping cart': 'سلة المشتريات',
    'View your cart and checkout.': 'عرض سلة المشتريات والدفع.',
    'Choose light, dark or follow your device.': 'اختر فاتح، داكن أو اتبع إعدادات جهازك.',
    'System': 'النظام', 'Light': 'فاتح', 'Dark': 'داكن', 'Save': 'حفظ',
    'Change platform language.': 'تغيير لغة المنصة.',
    'Who can message me?': 'من يمكنه مراسلتي؟',
    'Everyone': 'الجميع', 'Selected accounts': 'حسابات محددة',
    'Save settings': 'حفظ الإعدادات', 'Log out': 'تسجيل الخروج',
    'Search by name or username': 'ابحث بالاسم أو اسم المستخدم',
    'Search accounts': 'البحث عن الحسابات', 'Search': 'بحث',
    'No accounts found': 'لم يتم العثور على حسابات',
    'View Profile': 'عرض الملف الشخصي',
    'No conversations yet. Find an account in Community to start one.': 'لا توجد محادثات بعد. ابحث عن حساب في المجتمع لبدء واحدة.',
    'Start the conversation.': 'ابدأ المحادثة.',
    'Write a message...': 'اكتب رسالة...',
    'Send message': 'إرسال رسالة',
    'Select a conversation': 'اختر محادثة',
    'Open Community to find an account and start messaging.': 'افتح المجتمع للبحث عن حساب وبدء المراسلة.',
    'Browse accounts': 'تصفح الحسابات',
    'Public Profile': 'الملف الشخصي العام',
    'No description provided.': 'لم يتم توفير وصف.',
    'Message': 'مراسلة', 'Contact': 'تواصل',
    'Marketplace': 'السوق', 'Dashboard': 'لوحة التحكم', 'Sign in': 'تسجيل الدخول',
    'Get started': 'ابدأ الآن', 'Workspace': 'مساحة العمل', 'Profile settings': 'إعدادات الملف الشخصي',
    'Preferences': 'التفضيلات', 'Appearance': 'المظهر', 'Language': 'اللغة', 'Support': 'الدعم',
    'Help center': 'مركز المساعدة', 'Privacy policy': 'سياسة الخصوصية', 'Sign out securely': 'تسجيل الخروج بأمان',
    'Built for better supply chains.': 'مصمم لسلاسل توريد أفضل.', 'THE B2B PRODUCE NETWORK': 'شبكة المنتجات الزراعية للأعمال',
    'From the farm\nstraight to business.': 'من المزرعة\nمباشرة إلى قطاع الأعمال.', 'Skip intro': 'تخطي المقدمة',
    'CropFlow makes fresh, reliable sourcing simple for restaurants, retailers and food teams.': 'يجعل CropFlow التوريد الطازج والموثوق سهلاً للمطاعم وتجار التجزئة وفرق الأغذية.',
    'Explore the marketplace': 'استكشف السوق', 'Join as a supplier': 'انضم كمورد', 'fresher sourcing': 'توريد أكثر نضارة',
    'Trusted sourcing for growing teams': 'توريد موثوق للفرق المتنامية', 'Verified suppliers': 'موردون موثقون',
    'Clear availability': 'توفر واضح', 'Built for trade': 'مصمم للتجارة', 'LIVE MARKETPLACE': 'السوق المباشر',
    'Source what is in season.': 'احصل على منتجات الموسم.', 'active listings': 'منتج متاح',
    'Search crops or farms...': 'ابحث عن محصول أو مزرعة...', 'Search crops or farms': 'ابحث عن محصول أو مزرعة',
    'Updated daily': 'يتم التحديث يومياً', 'Available': 'متوفر', 'Available volume': 'الكمية المتاحة',
    'Ships by': 'متاح حتى', 'SAR / kg': 'دينار / كجم', 'Reserve': 'احجز', 'Sign in to reserve': 'سجل الدخول للحجز',
    'Your next harvest starts here.': 'يبدأ حصادك القادم من هنا.',
    'No active listings yet. Check back soon or become the first supplier.': 'لا توجد منتجات متاحة حالياً. عد قريباً أو كن أول مورد.',
    'HOW IT WORKS': 'كيف تعمل المنصة', 'Trade with less friction.': 'تجارة أسهل وأكثر وضوحاً.',
    'List your supply': 'أضف منتجاتك', 'Share what is available, when it ships and at what volume.': 'شارك ما هو متاح وموعد الشحن والكمية.',
    'Find the right fit': 'اعثر على ما يناسبك', 'Buyers discover transparent listings from verified farms.': 'يكتشف المشترون منتجات واضحة من مزارع موثوقة.',
    'Grow together': 'ننمو معاً', 'Reserve with confidence and build lasting trade relationships.': 'احجز بثقة وابنِ علاقات تجارية مستدامة.',
    'Welcome back.': 'مرحباً بعودتك.', 'Sign in to manage your supply and orders.': 'سجل الدخول لإدارة منتجاتك وطلباتك.',
    'Username': 'اسم المستخدم', 'Password': 'كلمة المرور', 'Remember me': 'تذكرني', 'Forgot password?': 'نسيت كلمة المرور؟',
    'New to CropFlow?': 'جديد على CropFlow؟', 'Create an account': 'إنشاء حساب', 'JOIN THE NETWORK': 'انضم إلى الشبكة', 'Sign in as': 'تسجيل الدخول بصفتك', 'Farmer account': 'حساب مزارع', 'Buyer account': 'حساب مشتري', 'Continue with Google': 'المتابعة باستخدام Google', 'Google login is not configured yet.': 'تسجيل الدخول عبر Google غير مهيأ بعد.', 'Your account type does not match this login option.': 'نوع حسابك لا يطابق خيار تسجيل الدخول هذا.', 'Google login failed. Please try again.': 'فشل تسجيل الدخول عبر Google. حاول مرة أخرى.', 'Manage listings and supply': 'إدارة المنتجات والتوريد', 'Discover and reserve crops': 'اكتشاف المحاصيل وحجزها', 'or': 'أو', 'Please choose a valid account type.': 'اختر نوع حساب صحيحاً.',
    'Build better trade.': 'ابنِ تجارة أفضل.', 'Create one account for your farm, company or buying team.': 'أنشئ حساباً لمزرعتك أو شركتك أو فريق المشتريات.',
    'Full name': 'الاسم الكامل', 'Phone number': 'رقم الهاتف', 'Work email': 'البريد الإلكتروني للعمل',
    'I am joining as': 'نوع الحساب', 'Farmer / supplier': 'مزارع / مورد', 'Company / restaurant / buyer': 'شركة / مطعم / مشتري',
    'Use 8+ characters, one uppercase letter and one number.': 'استخدم 8 أحرف على الأقل، وحرفاً كبيراً ورقماً.',
    'Already have an account?': 'لديك حساب بالفعل؟', 'ACCOUNT RECOVERY': 'استعادة الحساب', 'Reset your password.': 'أعد ضبط كلمة المرور.',
    'We will help you get back into your workspace.': 'سنساعدك على العودة إلى مساحة عملك.', 'Send reset link': 'إرسال رابط الاستعادة',
    'Back to sign in': 'العودة لتسجيل الدخول', 'SUPPLIER WORKSPACE': 'مساحة المورد', 'Good to see you, %(name)s.': 'سعيدون برؤيتك، %(name)s.',
    'Keep your supply visible and your buyers moving.': 'حافظ على ظهور منتجاتك وسهولة وصول المشترين إليها.', 'New listing': 'منتج جديد',
    'Add a crop listing': 'إضافة منتج زراعي', 'Crop name': 'اسم المحصول', 'e.g. Roma tomatoes': 'مثال: طماطم روما',
    'Available quantity (kg)': 'الكمية المتاحة (كجم)', 'Price per kg (SAR)': 'السعر لكل كجم (دينار)', 'Available until': 'متاح حتى', 'Minimum order (kg)': 'الحد الأدنى للطلب (كجم)', 'Minimum order': 'الحد الأدنى للطلب',
    'Publish listing': 'نشر المنتج', 'Your active listings': 'منتجاتك النشطة', 'Until': 'حتى',
    'No listings yet. Your first one can go live in seconds.': 'لا توجد منتجات بعد. يمكنك نشر أول منتج خلال ثوانٍ.',
    'YOUR WORKSPACE': 'مساحة العمل الخاصة بك', 'Keep your account details current and your workspace secure.': 'حافظ على تحديث بياناتك وأمان مساحة عملك.',
    'Email': 'البريد الإلكتروني', 'Not provided': 'غير متوفر', 'Farm / location': 'المزرعة / الموقع', 'New password': 'كلمة مرور جديدة',
    'Leave blank to keep current password': 'اتركه فارغاً للإبقاء على كلمة المرور الحالية', 'Save changes': 'حفظ التغييرات',
    'Your session expired. Please try again.': 'انتهت جلستك. حاول مرة أخرى.',
    'Too many login attempts. Please try again in a few minutes.': 'محاولات دخول كثيرة. حاول مرة أخرى بعد دقائق.',
    'Password must be at least 8 characters and include a number and an uppercase letter.': 'يجب أن تتكون كلمة المرور من 8 أحرف على الأقل وتتضمن رقماً وحرفاً كبيراً.',
    'If an account matches this email, password reset instructions will be sent shortly.': 'إذا كان البريد مرتبطاً بحساب، فستصل تعليمات الاستعادة قريباً.', 'Verification code': 'رمز التحقق', 'Enter the code shown below': 'أدخل الرمز الظاهر أدناه', 'Invalid verification code.': 'رمز التحقق غير صحيح.', 'Refresh code': 'تحديث الرمز', 'Your command center': 'مركز التحكم الخاص بك', 'Notification preferences': 'تفضيلات الإشعارات', 'Minimum order cannot exceed available quantity.': 'لا يمكن أن يتجاوز الحد الأدنى للطلب الكمية المتاحة.', 'Compare supply, pricing and order minimums in one clear workspace.': 'قارن الكميات والأسعار والحد الأدنى للطلب في مساحة واضحة واحدة.', 'Are you sure you want to sign out?': 'هل أنت متأكد من تسجيل الخروج؟', 'Edit profile': 'تعديل البيانات', 'New password must be at least 8 characters and include a number and an uppercase letter.': 'يجب أن تتكون كلمة المرور الجديدة من 8 أحرف على الأقل وتتضمن رقماً وحرفاً كبيراً.', 'View farm': 'عرض المزرعة', 'Farm products': 'منتجات المزرعة', 'Upload product images': 'رفع صور المنتج', 'Choose images': 'اختر الصور', 'Public farm profile': 'صفحة المزرعة العامة', 'No product image': 'لا توجد صورة للمنتج', 'Farm name': 'اسم المزرعة', 'Farm description': 'نبذة عن المزرعة', 'Product focus': 'نوع المنتجات', 'Contact owner': 'تواصل مع المالك', 'Call owner': 'اتصال بالمالك', 'Edit crop': 'تعديل المحصول', 'Save crop changes': 'حفظ تعديلات المحصول', 'Add more images': 'إضافة صور أخرى', 'Farm profile': 'ملف المزرعة', 'Farm profile picture': 'صورة ملف المزرعة', 'Describe your farm and how you grow.': 'اكتب نبذة عن مزرعتك وطريقة الزراعة.', 'Vegetables, fruits, herbs': 'خضروات، فواكه، أعشاب', 'Crop updated successfully.': 'تم تعديل المحصول بنجاح.', 'Error updating crop. Check data.': 'حدث خطأ أثناء تعديل المحصول. تحقق من البيانات.', 'Add new product': 'إضافة منتج جديد', 'Cancel': 'إلغاء'
}


TRANSLATIONS.update({
    'Dinar': 'دينار', 'Shopping cart': 'سلة التسوق', 'Close cart': 'إغلاق السلة',
    'Your cart is empty.': 'سلة التسوق فارغة.', 'Estimated total': 'الإجمالي التقديري',
    'View cart and checkout': 'عرض السلة وإتمام الطلب', 'Remove': 'حذف',
    'Add to cart': 'إضافة إلى السلة', 'Cart': 'السلة', 'Proceed to checkout': 'إتمام طلب التوريد',
    'Save for later': 'حفظ لوقت لاحق', 'Saved for later': 'محفوظ لوقت لاحق',
    'Checkout complete.': 'تم إتمام طلب التوريد.', 'No items to checkout.': 'لا توجد عناصر لإتمام الطلب.',
    'Checkout failed. Please refresh and try again.': 'فشل إتمام الطلب. حدّث الصفحة وحاول مرة أخرى.',
    'Order quantity is below the minimum order quantity.': 'الكمية أقل من الحد الأدنى للطلب.',
})


def _(message, **values):
    if message == 'SAR / kg':
        translated = 'دينار / كجم' if get_locale() == 'ar' else 'Dinar / kg'
        return translated
    if message == 'Price per kg (SAR)':
        translated = 'السعر لكل كجم (دينار)' if get_locale() == 'ar' else 'Price per kg (Dinar)'
        return translated
    translated = TRANSLATIONS.get(message, message) if get_locale() == 'ar' else message
    return translated % values if values else translated


app.jinja_env.globals['_'] = _

login_attempts = {}


def csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


def is_rate_limited(key, limit=8, window=300):
    now = time.time()
    attempts = [stamp for stamp in login_attempts.get(key, []) if now - stamp < window]
    login_attempts[key] = attempts
    return len(attempts) >= limit


def record_attempt(key):
    login_attempts.setdefault(key, []).append(time.time())


@app.before_request
def protect_requests():
    if request.method == 'POST':
        submitted_token = request.form.get('_csrf_token') or request.headers.get('X-CSRFToken')
        if not submitted_token or not compare_digest(submitted_token, session.get('_csrf_token', '')):
            if request.is_json:
                return jsonify({'error': 'Invalid CSRF token'}), 400
            flash(_('Your session expired. Please try again.'), 'danger')
            return redirect(request.referrer or url_for('index'))


@app.context_processor
def inject_security_helpers():
    return {'csrf_token': csrf_token}

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def initialize_database():
    """Create new tables and add nullable columns to legacy SQLite databases."""
    inspector = inspect(db.engine)
    if db.engine.dialect.name != 'sqlite':
        db.create_all()
        user_columns = {column['name'] for column in inspect(db.engine).get_columns('user')}
        for column_name, column_type in {
            'theme': "VARCHAR(20) NOT NULL DEFAULT 'system'",
            'message_policy': "VARCHAR(20) NOT NULL DEFAULT 'everyone'",
        }.items():
            if column_name not in user_columns:
                db.session.execute(text(f'ALTER TABLE "user" ADD COLUMN {column_name} {column_type}'))
        db.session.commit()
        return

    user_columns = {column['name'] for column in inspector.get_columns('user')} if inspector.has_table('user') else set()
    legacy_columns = {
        'email': 'VARCHAR(150)',
        'full_name': 'VARCHAR(150)',
        'phone': 'VARCHAR(20)',
        'location': 'VARCHAR(200)',
        'google_id': 'VARCHAR(200)'
            , 'farm_description': 'TEXT'
            , 'farm_product_type': 'VARCHAR(120)'
            , 'avatar_path': 'VARCHAR(300)'
            , 'theme': "VARCHAR(20) NOT NULL DEFAULT 'system'"
            , 'message_policy': "VARCHAR(20) NOT NULL DEFAULT 'everyone'"
    }
    for column_name, column_type in legacy_columns.items():
        if column_name not in user_columns:
            db.session.execute(text(f'ALTER TABLE user ADD COLUMN {column_name} {column_type}'))
    db.session.commit()
    product_columns = {column['name'] for column in inspector.get_columns('product')} if inspector.has_table('product') else set()
    if 'min_order_quantity' not in product_columns and inspector.has_table('product'):
        db.session.execute(text('ALTER TABLE product ADD COLUMN min_order_quantity FLOAT NOT NULL DEFAULT 1'))
        db.session.commit()
    db.create_all()


def set_verification_code():
    first = random.randint(2, 9)
    second = random.randint(1, 9)
    session['verification_code'] = str(first + second)
    session['verification_prompt'] = f'{first} + {second}'


def save_product_images(product, files):
    upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'products')
    os.makedirs(upload_folder, exist_ok=True)
    saved = 0
    for image_file in files:
        if not image_file or not image_file.filename:
            continue
        original_name = secure_filename(image_file.filename)
        extension = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            continue
        stored_name = f'{uuid.uuid4().hex}.{extension}'
        image_file.save(os.path.join(upload_folder, stored_name))
        db.session.add(ProductImage(path=f'uploads/products/{stored_name}', original_name=original_name, product=product))
        saved += 1
    return saved


def save_farm_avatar(image_file):
    if not image_file or not image_file.filename:
        return None
    original_name = secure_filename(image_file.filename)
    extension = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return None
    upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'farms')
    os.makedirs(upload_folder, exist_ok=True)
    stored_name = f'{uuid.uuid4().hex}.{extension}'
    image_file.save(os.path.join(upload_folder, stored_name))
    return f'uploads/farms/{stored_name}'

# OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# --- Routes ---

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['ar', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    products = Product.query.filter(
        Product.quantity > 0,
        Product.expiry_date >= date.today()
    ).order_by(Product.name.asc(), Product.date_added.desc()).all()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        client_key = request.remote_addr or 'unknown'
        if is_rate_limited(client_key):
            flash(_('Too many login attempts. Please try again in a few minutes.'), 'danger')
            return render_template('login.html'), 429

        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        remember = request.form.get('remember') == 'on'
        record_attempt(client_key)
        
        user = User.query.filter_by(username=username).first()
        if role not in {'farmer', 'buyer'}:
            flash(_('Please choose a valid account type.'), 'danger')
        elif user and user.role != role:
            flash(_('Your account type does not match this login option.'), 'danger')
        elif user and user.password and check_password_hash(user.password, password):
            login_attempts.pop(client_key, None)
            session.permanent = remember
            login_user(user, remember=remember, duration=app.config['PERMANENT_SESSION_LIFETIME'])
            if user.role == 'farmer':
                return redirect(url_for('dashboard'))
            return redirect(url_for('index'))
        else:
            flash(_('Invalid credentials. Please try again.'), 'danger')
            
    return render_template('login.html')

@app.route('/login/google/<role>')
def login_google(role):
    if role not in {'farmer', 'buyer'}:
        flash(_('Please choose a valid account type.'), 'danger')
        return redirect(url_for('login'))
    if not os.environ.get('GOOGLE_CLIENT_ID') or not os.environ.get('GOOGLE_CLIENT_SECRET'):
        flash(_('Google login is not configured yet.'), 'danger')
        return redirect(url_for('login'))
    session['google_role'] = role
    redirect_uri = url_for('auth_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google')
def auth_google():
    try:
        token = google.authorize_access_token()
    except Exception:
        flash(_('Google login failed. Please try again.'), 'danger')
        return redirect(url_for('login'))

    user_info = token.get('userinfo')
    if not user_info:
        flash(_('Google login failed. Please try again.'), 'danger')
        return redirect(url_for('login'))
        
    email = user_info.get('email')
    google_id = user_info.get('sub')
    name = user_info.get('name')
    requested_role = session.pop('google_role', 'buyer')

    if not email or not google_id:
        flash(_('Google login failed. Please try again.'), 'danger')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        # Check if email exists
        user = User.query.filter_by(email=email).first()
        if user:
            if user.role != requested_role:
                flash(_('Your account type does not match this login option.'), 'danger')
                return redirect(url_for('login'))
            user.google_id = google_id
            db.session.commit()
        else:
            # Create new user
            username = email.split('@')[0]
            # Ensure unique username
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User(username=username, email=email, full_name=name, google_id=google_id, role=requested_role)
            db.session.add(user)
            db.session.commit()
            
    if user.role != requested_role:
        flash(_('Your account type does not match this login option.'), 'danger')
        return redirect(url_for('login'))
    login_user(user)
    return redirect(url_for('dashboard') if user.role == 'farmer' else url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'GET':
        set_verification_code()

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        verification_code = request.form.get('verification_code', '').strip()

        if not verification_code or not compare_digest(verification_code, session.get('verification_code', '')):
            flash(_('Invalid verification code.'), 'danger')
            set_verification_code()
            return render_template('register.html')

        if len(password or '') < 8 or not any(char.isupper() for char in password) or not any(char.isdigit() for char in password):
            flash(_('Password must be at least 8 characters and include a number and an uppercase letter.'), 'danger')
            return render_template('register.html')

        if role not in {'farmer', 'buyer'}:
            flash(_('Please choose a valid account type.'), 'danger')
            return render_template('register.html')
        
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if user_exists:
            flash(_('Username already exists.'), 'danger')
        elif email_exists:
            flash(_('Email already registered.'), 'danger')
        else:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(
                username=username,
                email=email,
                password=hashed_password,
                role=role,
                full_name=request.form.get('full_name'),
                phone=request.form.get('phone')
            )
            db.session.add(new_user)
            db.session.commit()
            session.pop('verification_code', None)
            session.pop('verification_prompt', None)
            
            flash(_('Account created successfully! You can now login.'), 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        flash(_('If an account matches this email, password reset instructions will be sent shortly.'), 'success')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('user_profile.html', user=current_user)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    from models import User
    user = User.query.get_or_404(user_id)
    return render_template('user_profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.phone = request.form.get('phone')
        current_user.location = request.form.get('location')
        if current_user.role == 'farmer':
            current_user.farm_description = request.form.get('farm_description')
            current_user.farm_product_type = request.form.get('farm_product_type')
        avatar_path = save_farm_avatar(request.files.get('avatar'))
        if avatar_path:
            current_user.avatar_path = avatar_path
        
        new_password = request.form.get('new_password')
        if new_password:
            if len(new_password) < 8 or not any(char.isupper() for char in new_password) or not any(char.isdigit() for char in new_password):
                flash(_('New password must be at least 8 characters and include a number and an uppercase letter.'), 'danger')
                return render_template('edit_profile.html')
            current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            
        db.session.commit()
        flash(_('Profile updated successfully.'), 'success')
        return redirect(url_for('profile'))
        
    return render_template('edit_profile.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        theme = request.form.get('theme')
        if theme in {'system', 'light', 'dark'}:
            current_user.theme = theme
        if 'message_policy' in request.form:
            policy = request.form.get('message_policy', 'everyone')
            current_user.message_policy = policy if policy in {'everyone', 'selected'} else 'everyone'
            MessagePermission.query.filter_by(owner_id=current_user.id).delete()
            if current_user.message_policy == 'selected':
                ids = {int(value) for value in request.form.getlist('allowed_contact_ids') if value.isdigit()}
                for contact in User.query.filter(User.id.in_(ids), User.id != current_user.id).all():
                    db.session.add(MessagePermission(owner_id=current_user.id, contact_id=contact.id))
        db.session.commit()
        flash(_('Settings saved.'), 'success')
        return redirect(url_for('settings'))
    users = User.query.filter(User.id != current_user.id).order_by(User.username.asc()).all()
    allowed_ids = {permission.contact_id for permission in current_user.message_permissions}
    return render_template('settings.html', users=users, allowed_ids=allowed_ids)


@app.route('/community')
@login_required
def community():
    query = request.args.get('q', '').strip()
    users = User.query.filter(User.id != current_user.id)
    if query:
        users = users.filter(or_(User.username.ilike(f'%{query}%'), User.full_name.ilike(f'%{query}%')))
    users = users.order_by(User.full_name.asc(), User.username.asc()).limit(100).all()
    return render_template('community.html', users=users, query=query)


@app.route('/messages')
@login_required
def messages():
    unread_count = Message.query.filter_by(recipient_id=current_user.id, read_at=None).count()
    contacts = User.query.join(Message, or_(Message.sender_id == User.id, Message.recipient_id == User.id)).filter(
        or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id), User.id != current_user.id
    ).distinct().order_by(User.username.asc()).all()
    for contact in contacts:
        contact.has_unread = Message.query.filter_by(sender_id=contact.id, recipient_id=current_user.id, read_at=None).count() > 0
    partner = User.query.get(request.args.get('with', type=int)) if request.args.get('with', type=int) else None
    if partner and partner.id == current_user.id:
        partner = None
    thread = []
    if partner:
        thread = Message.query.filter(or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == partner.id),
            and_(Message.sender_id == partner.id, Message.recipient_id == current_user.id)
        )).order_by(Message.created_at.asc()).all()
        Message.query.filter_by(sender_id=partner.id, recipient_id=current_user.id, read_at=None).update({Message.read_at: datetime.utcnow()})
        db.session.commit()
    return render_template('messages.html', contacts=contacts, partner=partner, thread=thread, unread_count=unread_count)


@app.route('/messages/send/<int:recipient_id>', methods=['POST'])
@login_required
def send_message(recipient_id):
    recipient = User.query.get_or_404(recipient_id)
    body = request.form.get('body', '').strip()
    if not body or len(body) > 4000:
        flash(_('Write a message of up to 4000 characters.'), 'danger')
    elif recipient.message_policy == 'selected' and not MessagePermission.query.filter_by(owner_id=recipient.id, contact_id=current_user.id).first():
        flash(_('This account is not accepting messages from you.'), 'danger')
    else:
        db.session.add(Message(sender_id=current_user.id, recipient_id=recipient.id, body=body))
        db.session.commit()
    return redirect(url_for('messages', **{'with': recipient.id}))


@app.route('/api/messages/<int:partner_id>')
@login_required
def poll_messages(partner_id):
    partner = User.query.get_or_404(partner_id)
    after_id = request.args.get('after', 0, type=int)
    new_messages = Message.query.filter(or_(
        and_(Message.sender_id == current_user.id, Message.recipient_id == partner.id),
        and_(Message.sender_id == partner.id, Message.recipient_id == current_user.id)
    ), Message.id > after_id).order_by(Message.id.asc()).all()
    Message.query.filter_by(sender_id=partner.id, recipient_id=current_user.id, read_at=None).update({Message.read_at: datetime.utcnow()})
    db.session.commit()
    return jsonify({'messages': [{'id': item.id, 'sender_id': item.sender_id, 'body': item.body, 'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')} for item in new_messages]})


@app.route('/workers', methods=['GET', 'POST'])
@login_required
def workers():
    if current_user.role != 'farmer':
        flash(_('Unauthorized access.'), 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name:
            db.session.add(Worker(name=name[:150], job_title=request.form.get('job_title', '').strip()[:120], phone=request.form.get('phone', '').strip()[:30], farmer_id=current_user.id))
            db.session.commit()
            flash(_('Worker added successfully.'), 'success')
        return redirect(url_for('workers'))
    return render_template('workers.html', workers=Worker.query.filter_by(farmer_id=current_user.id).order_by(Worker.name.asc()).all())


@app.route('/workers/<int:worker_id>/delete', methods=['POST'])
@login_required
def delete_worker(worker_id):
    if current_user.role != 'farmer':
        return jsonify({'success': False}), 403
    worker = Worker.query.filter_by(id=worker_id, farmer_id=current_user.id).first_or_404()
    db.session.delete(worker)
    db.session.commit()
    return redirect(url_for('workers'))



@app.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.filter_by(id=product_id, farmer_id=current_user.id).first_or_404()
    for image in product.images:
        db.session.delete(image)
    db.session.delete(product)
    db.session.commit()
    flash(_('Product deleted successfully.'), 'success')
    return redirect(url_for('user_profile', user_id=current_user.id))


@app.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'farmer':
        flash(_('Unauthorized access.'), 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        min_order_quantity = request.form.get('min_order_quantity')
        expiry_date_str = request.form.get('expiry_date')
        image_files = request.files.getlist('images')
        try:
            if not name or float(quantity) <= 0 or float(price) < 0 or float(min_order_quantity) <= 0 or float(min_order_quantity) > float(quantity):
                raise ValueError
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            new_product = Product(name=name, quantity=float(quantity), min_order_quantity=float(min_order_quantity), price=float(price), expiry_date=expiry_date, farmer_id=current_user.id)
            db.session.add(new_product)
            db.session.commit()
            if image_files and image_files[0].filename != '':
                save_product_images(new_product, image_files)
                db.session.commit()
            flash(_('Crop added successfully.'), 'success')
            return redirect(url_for('user_profile', user_id=current_user.id))
        except ValueError:
            flash(_('Invalid input. Check quantities and dates.'), 'danger')
    return render_template('add_product.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.role != 'farmer':
        flash(_('Unauthorized access.'), 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        min_order_quantity = request.form.get('min_order_quantity')
        expiry_date_str = request.form.get('expiry_date')
        image_files = request.files.getlist('images')
        
        try:
            if not name or float(quantity) <= 0 or float(price) < 0 or float(min_order_quantity) <= 0 or float(min_order_quantity) > float(quantity):
                raise ValueError
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            new_product = Product(
                name=name,
                quantity=float(quantity),
                min_order_quantity=float(min_order_quantity),
                price=float(price),
                expiry_date=expiry_date,
                farmer_id=current_user.id
            )
            db.session.add(new_product)
            saved_images = save_product_images(new_product, image_files)
            db.session.commit()
            flash(_('Product added successfully!') + (f' ({saved_images} images)' if saved_images else ''), 'success')
        except Exception as e:
            try:
                exceeds_stock = float(min_order_quantity) > float(quantity)
            except (TypeError, ValueError):
                exceeds_stock = False
            if exceeds_stock:
                flash(_('Minimum order cannot exceed available quantity.'), 'danger')
            else:
                flash(_('Error adding product. Check data.'), 'danger')
            
        return redirect(url_for('dashboard'))
        
    farmer_products = Product.query.filter_by(farmer_id=current_user.id).all()
    return render_template('dashboard.html', products=farmer_products)


@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.filter_by(id=product_id, farmer_id=current_user.id).first_or_404()
    if request.method == 'POST':
        try:
            quantity = float(request.form.get('quantity'))
            price = float(request.form.get('price'))
            minimum = float(request.form.get('min_order_quantity'))
            if not request.form.get('name') or quantity <= 0 or price < 0 or minimum <= 0 or minimum > quantity:
                raise ValueError
            product.name = request.form.get('name').strip()
            product.quantity = quantity
            product.price = price
            product.min_order_quantity = minimum
            product.expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date()
            save_product_images(product, request.files.getlist('images'))
            db.session.commit()
            flash(_('Crop updated successfully.'), 'success')
            return redirect(url_for('dashboard'))
        except (TypeError, ValueError):
            db.session.rollback()
            flash(_('Error updating crop. Check data.'), 'danger')
    return render_template('edit_product.html', product=product)


@app.route('/farm/<int:farmer_id>')
def farm_profile(farmer_id):
    farmer = User.query.filter_by(id=farmer_id, role='farmer').first_or_404()
    products = Product.query.filter(
        Product.farmer_id == farmer.id,
        Product.quantity > 0,
        Product.expiry_date >= date.today()
    ).order_by(Product.date_added.desc()).all()
    return render_template('farm.html', farmer=farmer, products=products)


@app.route('/cart')
@login_required
def cart_page():
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    return render_template('cart.html')


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)


@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout_cart():
    if current_user.role != 'buyer':
        return jsonify({'success': False, 'message': 'Only buyers can checkout.'}), 403
    payload = request.get_json(silent=True) or {}
    requested_items = payload.get('items') or []
    if not requested_items:
        return jsonify({'success': False, 'message': _('No items to checkout.')}), 400
    try:
        reservations = []
        total = 0
        for requested in requested_items:
            product = db.session.get(Product, int(requested.get('id')))
            quantity = float(requested.get('quantity'))
            minimum = float(product.min_order_quantity) if product else 0
            if not product or product.expiry_date < date.today() or quantity < minimum or quantity > product.quantity:
                raise ValueError(_('Order quantity is below the minimum order quantity.'))
            product.quantity -= quantity
            total += quantity * product.price
            reservations.append(Reservation(product_id=product.id, buyer_id=current_user.id, quantity=quantity))
        db.session.add_all(reservations)
        db.session.commit()
        return jsonify({'success': True, 'total': round(total, 2), 'message': _('Checkout complete.')})
    except (TypeError, ValueError, OverflowError) as error:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(error)}), 400


@app.route('/reserve/<int:product_id>', methods=['POST'])
@login_required
def reserve_product(product_id):
    if current_user.role != 'buyer':
        flash(_('Only buyers can reserve products.'), 'danger')
        return redirect(url_for('index'))

    product = Product.query.get_or_404(product_id)
    if product.expiry_date < datetime.utcnow().date() or product.quantity <= 0:
        flash(_('This product is no longer available.'), 'danger')
        return redirect(url_for('index'))

    quantity = request.form.get('quantity', '1')
    try:
        quantity = float(quantity)
        if quantity <= 0 or quantity > product.quantity:
            raise ValueError
    except (TypeError, ValueError):
        flash(_('Please enter a valid quantity within the available stock.'), 'danger')
        return redirect(url_for('index'))

    product.quantity -= quantity
    reservation = Reservation(product_id=product.id, buyer_id=current_user.id, quantity=quantity)
    db.session.add(reservation)
    db.session.commit()
    flash(_('Product reserved successfully.'), 'success')
    return redirect(url_for('index'))

# --- API Endpoints ---

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.filter(
        Product.quantity > 0,
        Product.expiry_date >= date.today()
    ).order_by(Product.date_added.desc()).all()
    return jsonify([product.to_dict() for product in products])


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or request.form
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()

    if not user or not user.password or not password or not check_password_hash(user.password, password):
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    })

if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    app.run(debug=True)
