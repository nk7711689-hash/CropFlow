import pathlib

css_path = pathlib.Path(r'd:\CropFlow\static\css\style.css')
lines = css_path.read_text(encoding='utf-8').splitlines(keepends=True)

# Keep lines 1-119, replace everything from line 120 onwards
keep = lines[:119]

new_css = """
/* ── Product Detail ── */
.product-detail-gallery img { width: 100%; max-height: 400px; object-fit: contain; border-radius: var(--radius); background: var(--warm); }

/* ── Profile Page ── */
.profile-top { text-align: center; padding: 25px 0 20px; position: relative; }
.profile-top .profile-settings-btn { position: absolute; top: 0; left: 0; color: var(--ink-soft); font-size: 1.15rem; text-decoration: none; }
.profile-top .profile-settings-btn:hover { color: var(--green-dark); }

.profile-avatar-wrap { width: 110px; height: 110px; border-radius: 50%; overflow: hidden; margin: 0 auto 14px; background: var(--green-pale); color: var(--green-dark); display: flex; align-items: center; justify-content: center; font-size: 2.5rem; border: 3px solid var(--line); }
.profile-avatar-wrap img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }

.profile-name { font-size: 1.45rem; margin: 0 0 4px; font-weight: 700; }
.profile-username { color: var(--ink-soft); font-size: .88rem; margin: 0; }

.profile-details { text-align: center; padding: 16px 0 24px; border-bottom: 1px solid var(--line); margin-bottom: 28px; }
.profile-location { color: var(--ink-soft); font-size: .88rem; margin: 0 0 12px; }
.profile-location i { color: var(--green-dark); margin-inline-end: 4px; }
.profile-bio { font-size: .92rem; color: var(--ink); margin: 0 auto 14px; max-width: 500px; line-height: 1.6; }

.profile-tags { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 18px; }
.profile-tags span { background: var(--green-pale); color: var(--green-dark); border-radius: 20px; padding: 5px 14px; font-size: .78rem; font-weight: 600; }

.profile-actions { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
.profile-actions .button i { margin-inline-end: 6px; }

.profile-products-section { margin-top: 10px; }
.profile-section-title { font-size: 1.1rem; margin-bottom: 18px; padding-bottom: 10px; border-bottom: 1px solid var(--line); }

/* ── Mini edit/delete buttons on product cards ── */
.mini-card-actions { position: absolute; top: 8px; right: 8px; display: flex; gap: 5px; z-index: 10; }
[dir="rtl"] .mini-card-actions { right: auto; left: 8px; }
.mini-card-actions a,
.mini-card-actions button { background: rgba(255,255,255,.92); backdrop-filter: blur(6px); border: 1px solid var(--line); color: var(--ink-soft); border-radius: 8px; padding: 5px 8px; font-size: .75rem; cursor: pointer; transition: all .15s; line-height: 1; }
.mini-card-actions a:hover { color: var(--green-dark); background: #fff; }
.mini-card-actions button:hover { color: #c0392b; background: #fff; }

/* ── FAB (floating add button) ── */
.fab-add { position: fixed; bottom: 100px; left: 24px; background: var(--green-dark); color: #fff; width: 56px; height: 56px; border-radius: 16px; display: flex; align-items: center; justify-content: center; box-shadow: 0 6px 18px rgba(47, 98, 88, .35); z-index: 100; text-decoration: none; font-size: 1.4rem; transition: transform .2s, box-shadow .2s; }
[dir="rtl"] .fab-add { left: auto; right: 24px; }
.fab-add:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(47, 98, 88, .45); }

/* ── Edit Profile avatar preview ── */
.profile-avatar-preview { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; display: block; margin-top: 10px; border: 2px solid var(--line); }

/* ── Header extras ── */
.header-login { color: var(--ink); font-weight: 600; font-size: .88rem; margin-inline-end: 12px; text-decoration: none; }
.header-login:hover { color: var(--green-dark); }
.icon-button { background: none; border: none; color: var(--ink-soft); font-size: 1.1rem; cursor: pointer; padding: 6px; text-decoration: none; }
.icon-button:hover { color: var(--green-dark); }
.menu-button { background: none; border: 1px solid var(--line); border-radius: 10px; color: var(--ink); cursor: pointer; padding: 6px 10px; font-size: 1rem; }
.menu-button:hover { background: var(--green-pale); }

/* ── Chat compose extras ── */
.chat-compose-extras { display: flex; gap: 10px; padding: 10px 0 0; color: var(--ink-soft); }
.chat-compose-extras button { background: none; border: none; color: inherit; cursor: pointer; font-size: 1.1rem; }

@media (max-width: 520px) {
    .profile-avatar-wrap { width: 90px; height: 90px; }
    .profile-name { font-size: 1.2rem; }
    .fab-add { width: 50px; height: 50px; bottom: 90px; left: 16px; border-radius: 14px; font-size: 1.2rem; }
    [dir="rtl"] .fab-add { left: auto; right: 16px; }
}
"""

css_path.write_text(''.join(keep) + new_css, encoding='utf-8')
print('CSS updated successfully')
