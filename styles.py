"""Apparence de l'application : couleurs, cartes, mobile, icônes des motifs."""
import streamlit as st

# ─── Icônes motifs (SVG, rendu identique sur tous les appareils) ────────────
MOTIF_SVG = {
    "lisse": '<svg viewBox="0 0 40 40" width="34" height="34"><rect x="5" y="5" width="30" height="30" rx="4" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    "briques": '<svg viewBox="0 0 40 40" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="6" width="16" height="8"/><rect x="19" y="6" width="18" height="8"/><rect x="-5" y="16" width="16" height="8"/><rect x="11" y="16" width="16" height="8"/><rect x="27" y="16" width="16" height="8"/><rect x="3" y="26" width="16" height="8"/><rect x="19" y="26" width="18" height="8"/></svg>',
    "chevrons": '<svg viewBox="0 0 40 40" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M2 12 L12 4 L22 12"/><path d="M18 12 L28 4 L38 12"/><path d="M2 26 L12 18 L22 26"/><path d="M18 26 L28 18 L38 26"/></svg>',
    "hexagones_motif": '<svg viewBox="0 0 40 40" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.8"><polygon points="12,4 22,4 27,12 22,20 12,20 7,12"/><polygon points="24,20 34,20 39,28 34,36 24,36 19,28"/><polygon points="0,20 10,20 15,28 10,36 0,36 -5,28"/></svg>',
    "quadrillage": '<svg viewBox="0 0 40 40" width="34" height="34" stroke="currentColor" stroke-width="1.8"><line x1="0" y1="13" x2="40" y2="13"/><line x1="0" y1="27" x2="40" y2="27"/><line x1="13" y1="0" x2="13" y2="40"/><line x1="27" y1="0" x2="27" y2="40"/></svg>',
    "losanges": '<svg viewBox="0 0 40 40" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.8"><polygon points="10,2 20,12 10,22 0,12"/><polygon points="30,2 40,12 30,22 20,12"/><polygon points="10,22 20,32 10,42 0,32"/><polygon points="30,22 40,32 30,42 20,32"/></svg>',
    "cercles": '<svg viewBox="0 0 40 40" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="7"/><circle cx="29" cy="12" r="7"/><circle cx="12" cy="29" r="7"/><circle cx="29" cy="29" r="7"/></svg>',
    "opus": '<svg viewBox="0 0 40 40" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.6"><polygon points="2,4 16,2 15,15 3,17"/><polygon points="18,3 37,6 35,16 17,16"/><polygon points="2,19 14,18 13,30 1,32"/><polygon points="16,19 25,18 36,20 34,33 17,32"/></svg>',
    "galets": '<svg viewBox="0 0 40 40" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.8"><ellipse cx="10" cy="12" rx="8" ry="5"/><ellipse cx="28" cy="10" rx="7" ry="5"/><ellipse cx="10" cy="27" rx="7" ry="5"/><ellipse cx="29" cy="28" rx="8" ry="5"/></svg>',
    "spirale": '<svg viewBox="0 0 40 40" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 20 m0,-14 a14,14 0 1,1 -9.9,23.9 a9,9 0 1,1 6.4,-15.4 a4,4 0 1,1 -2.8,6.8"/></svg>',
    "perso": '<svg viewBox="0 0 40 40" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 30 L26 10 L32 16 L12 36 L5 37 Z"/><path d="M23 13 L29 19"/></svg>',
}
def motif_icon_html(k, color="#1B5E20", size=34):
    svg = MOTIF_SVG.get(k, MOTIF_SVG["lisse"])
    svg = svg.replace('width="34" height="34"', f'width="{size}" height="{size}"')
    return f'<span style="color:{color};display:inline-flex;">{svg}</span>'

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;900&display=swap');
* { font-family: 'Poppins', sans-serif; }
/* Mode sombre - forcer couleurs texte */
.stMarkdown p { color: inherit !important; }
h1, h2, h3, h4, h5, h6 { color: #1B5E20 !important; }
.stApp { color: #1a1a1a !important; }
[data-theme="dark"] .card, [data-theme="dark"] .contact-card,
[data-theme="dark"] .historique-card, [data-theme="dark"] .temoignage-card,
[data-theme="dark"] .apercu-pave, [data-theme="dark"] .paiement-box { 
    color: #1a1a1a !important; background-color: #f1f8e9 !important; 
}
.contact-card p, .contact-card h4 { color: #1B5E20 !important; }
.card p, .card h4 { color: #1a1a1a !important; }
.historique-card { color: #1a1a1a !important; }
.temoignage-card p { color: #333 !important; }
.eco-badge { color: #1B5E20 !important; }
.nav-title { color: #1B5E20 !important; }
.nav-desc { color: #555 !important; }
.stat-label { color: #C8E6C9 !important; }
.main-title { font-size: 42px; font-weight: 900; color: #1B5E20; text-align: center; margin-bottom: 4px; letter-spacing: 2px; }
.slogan { font-size: 16px; color: #4CAF50; text-align: center; font-style: italic; margin-bottom: 8px; }
.section-title { font-size: 24px; font-weight: 700; color: #2E7D32; margin-top: 25px; margin-bottom: 15px; border-bottom: 3px solid #4CAF50; padding-bottom: 8px; }
.card { background: linear-gradient(135deg, #F1F8E9, #E8F5E9); padding: 20px; border-radius: 14px; border-left: 5px solid #4CAF50; margin-bottom: 15px; box-shadow: 0 2px 12px rgba(76,175,80,0.1); }
.eco-badge { background: linear-gradient(135deg, #E8F5E9, #C8E6C9); color: #1B5E20; padding: 18px; border-radius: 12px; border: 2px dashed #4CAF50; text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px; }
.nav-card { background: white; padding: 28px 20px; border-radius: 16px; text-align: center; cursor: pointer; border: 2px solid #E8F5E9; transition: all 0.3s; box-shadow: 0 4px 16px rgba(0,0,0,0.08); margin-bottom: 10px; }
.nav-card:hover { border-color: #4CAF50; box-shadow: 0 8px 24px rgba(76,175,80,0.2); transform: translateY(-2px); }
.nav-icon { font-size: 48px; margin-bottom: 10px; }
.nav-title { font-size: 16px; font-weight: 700; color: #1B5E20; margin-bottom: 6px; }
.nav-desc { font-size: 12px; color: #777; }
.stat-card { background: linear-gradient(135deg, #1B5E20, #2E7D32); color: white; padding: 20px; border-radius: 14px; text-align: center; }
.stat-number { font-size: 32px; font-weight: 900; color: #A5D6A7; }
.stat-label { font-size: 12px; color: #C8E6C9; margin-top: 4px; }
.progress-bar { display: flex; justify-content: space-between; margin-bottom: 20px; padding: 12px; background: #F1F8E9; border-radius: 10px; }
.prog-step { text-align: center; flex: 1; font-size: 11px; font-weight: 600; }
.prog-step.active { color: #1B5E20; }
.prog-step.done { color: #4CAF50; }
.prog-step.inactive { color: #BDBDBD; }
.logo-box { background: linear-gradient(135deg, #1B5E20, #2E7D32); padding: 18px 36px; border-radius: 16px; display: inline-flex; align-items: center; gap: 14px; box-shadow: 0 8px 32px rgba(27,94,32,0.35); }
.logo-brand { font-size: 28px; font-weight: 900; color: #fff; letter-spacing: 2px; }
.logo-brand span { color: #A5D6A7; }
.logo-tag { font-size: 10px; color: #C8E6C9; letter-spacing: 3px; text-transform: uppercase; }
.contact-card { background: linear-gradient(135deg, #F1F8E9, #E8F5E9); padding: 24px; border-radius: 14px; border-left: 5px solid #4CAF50; margin-bottom: 15px; }
.historique-card { background: #F9FBE7; border-left: 4px solid #8BC34A; padding: 12px 16px; border-radius: 10px; margin-bottom: 10px; }
.temoignage-card { background: white; padding: 20px; border-radius: 14px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); border-top: 4px solid #4CAF50; margin-bottom: 15px; }
.apercu-pave { background: #F5F5F5; padding: 20px; border-radius: 14px; text-align: center; border: 2px dashed #4CAF50; margin: 15px 0; }
.color-notice { background: #FFF8E1; padding: 12px; border-radius: 10px; border-left: 4px solid #FFC107; margin: 10px 0; font-size: 14px; }
.paiement-box { background: linear-gradient(135deg, #E8F5E9, #F1F8E9); padding: 20px; border-radius: 14px; border: 2px solid #4CAF50; margin: 15px 0; }
.stButton>button { background: linear-gradient(135deg, #2E7D32, #1B5E20); color: white; border-radius: 10px; width: 100%; font-weight: 700; height: 48px; border: none; box-shadow: 0 4px 12px rgba(27,94,32,0.3); }
.stButton>button:hover { background: linear-gradient(135deg, #1B5E20, #0a3d0a); transform: translateY(-1px); }

/* ─── Mobile : plus lisible et plus facile à toucher ─── */
.block-container, [data-testid="stMainBlockContainer"] { padding-top: 1.5rem !important; }
@media (max-width: 640px) {
  .block-container, [data-testid="stMainBlockContainer"] { padding-left: 0.9rem !important; padding-right: 0.9rem !important; padding-top: 1rem !important; }
  .main-title { font-size: 28px; }
  .section-title { font-size: 20px; margin-top: 18px; }
  .logo-box { padding: 12px 22px; }
  .logo-brand { font-size: 22px; }
  .nav-card { padding: 16px 12px; }
  .nav-icon { font-size: 36px; }
  .stat-number { font-size: 24px; }
  .stButton>button, .stDownloadButton>button { min-height: 52px; font-size: 16px; }
  .progress-bar { padding: 8px 4px; }
  .prog-step { font-size: 10px; }
  .card, .contact-card, .paiement-box { padding: 14px; }
}
</style>
"""


def appliquer():
    st.markdown(CSS, unsafe_allow_html=True)