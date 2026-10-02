import pathlib

app_path = pathlib.Path(r'd:\CropFlow\app.py')
text = app_path.read_text(encoding='utf-8')

new_translations = """    'Edit Profile': 'تعديل الملف الشخصي',
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
"""

text = text.replace("TRANSLATIONS = {\n", "TRANSLATIONS = {\n" + new_translations)
app_path.write_text(text, encoding='utf-8')
print('Translations added successfully')
