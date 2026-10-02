from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_location_public BOOLEAN DEFAULT TRUE;'))
        db.session.execute(text('ALTER TABLE message ADD COLUMN IF NOT EXISTS attachment_path VARCHAR(300);'))
        db.session.execute(text('ALTER TABLE message ADD COLUMN IF NOT EXISTS attachment_type VARCHAR(20);'))
        db.session.execute(text('ALTER TABLE message ALTER COLUMN body DROP NOT NULL;'))
        db.session.commit()
        print('DB Schema updated')
    except Exception as e:
        print('Error:', e)
        db.session.rollback()
