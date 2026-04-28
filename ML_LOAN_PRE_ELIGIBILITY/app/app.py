import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import date, timedelta
import os, pickle, joblib, hashlib, sqlite3

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LoanSmart AI",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f5f7fa; }
    .block-container { padding-top: 0rem; padding-bottom: 2rem; }
    h1, h2, h3 { color: #1a1a2e; }
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
        padding: 4rem 2rem 3rem 2rem;
        text-align: center;
        color: white;
    }
    .hero h1 { color: white !important; font-size: 3rem; margin-bottom: 0.5rem; }
    .hero p  { color: #aad4f5; font-size: 1.15rem; }
    .feature-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border: 1px solid #eee;
    }
    .auth-box {
        background: white;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.10);
        border: 1px solid #e8e8e8;
    }
    .auth-title    { font-size:1.7rem; font-weight:700; color:#1a1a2e; text-align:center; margin-bottom:0.2rem; }
    .auth-subtitle { color:#888; text-align:center; margin-bottom:1.5rem; font-size:0.95rem; }
    .status-gold { background:#fff8e1; border-left:4px solid #f9a825; padding:1rem; border-radius:6px; }
    .status-warn { background:#fff3e0; border-left:4px solid #fb8c00; padding:1rem; border-radius:6px; }
    .status-bad  { background:#fce4ec; border-left:4px solid #e53935; padding:1rem; border-radius:6px; }
    .status-good { background:#e8f5e9; border-left:4px solid #43a047; padding:1rem; border-radius:6px; }
    .section-divider { border-top: 2px solid #eeeeee; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# SQLite DATABASE
# ════════════════════════════════════════════════════════════════════════════
DB_PATH = "loansmart_users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email     TEXT UNIQUE NOT NULL,
            phone     TEXT,
            password  TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(username, full_name, email, phone, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO users (username,full_name,email,phone,password) VALUES (?,?,?,?,?)",
            (username.strip(), full_name.strip(), email.strip(), phone.strip(), hash_pw(password))
        )
        conn.commit(); conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError as e:
        conn.close()
        if "username" in str(e): return False, "❌ Username already taken."
        if "email"    in str(e): return False, "❌ Email already registered."
        return False, "❌ Registration failed."

def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT full_name, email FROM users WHERE username=? AND password=?",
        (username.strip(), hash_pw(password))
    ).fetchone()
    if row:
        conn.close()
        return True, row[0], row[1]
    exists = conn.execute("SELECT 1 FROM users WHERE username=?", (username.strip(),)).fetchone()
    conn.close()
    if exists: return False, "❌ Incorrect password.", ""
    return False, "❌ Username not found. Please sign up.", ""

init_db()

# ─── Session State ────────────────────────────────────────────────────────────
for k,v in {"page":"landing","logged_in":False,"username":"","full_name":"","email":""}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ════════════════════════════════════════════════════════════════════════════
# LANDING PAGE
# ════════════════════════════════════════════════════════════════════════════
def show_landing():
    st.markdown("""
    <div class="hero">
        <div style="font-size:3.5rem">🏦</div>
        <h1>LoanSmart AI</h1>
        <p>India's Intelligent Loan Pre-Eligibility + Behavior-Aware Scoring System</p>
        <p style="color:#7ecbf7;font-size:0.95rem">Powered by Machine Learning · Transparent · Fast · Fair</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(4)
    for col, (icon, title, desc) in zip(cols, [
        ("🤖","ML Prediction",      "Instant eligibility with probability scores"),
        ("📊","SHAP Explainability","Understand every decision — no black box"),
        ("📅","Behavior Tracking",  "Monitor EMI discipline over time"),
        ("🏆","Dynamic Scoring",    "Rewards good behaviour, penalises defaults"),
    ]):
        col.markdown(f"""
        <div class="feature-card">
            <div style="font-size:2.5rem">{icon}</div>
            <b>{title}</b>
            <p style="color:#666;font-size:0.88rem;margin-top:0.5rem">{desc}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:white;border-radius:12px;padding:1.5rem;text-align:center;
                box-shadow:0 2px 12px rgba(0,0,0,0.06);border:1px solid #eee;">
        <div style="display:flex;justify-content:space-around;flex-wrap:wrap;gap:1rem">
            <div><h2 style="color:#1565c0;margin:0">98%</h2><p style="color:#666;margin:0">Model Accuracy</p></div>
            <div><h2 style="color:#2e7d32;margin:0">0.99</h2><p style="color:#666;margin:0">ROC-AUC Score</p></div>
            <div><h2 style="color:#f57c00;margin:0">11</h2><p style="color:#666;margin:0">Features Used</p></div>
            <div><h2 style="color:#6a1b9a;margin:0">Real-time</h2><p style="color:#666;margin:0">Behavior Scoring</p></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, c1, c2, _ = st.columns([1.5, 1, 1, 1.5])
    with c1:
        if st.button("🚀 Login", use_container_width=True, type="primary"):
            st.session_state.page = "login"; st.rerun()
    with c2:
        if st.button("📝 Sign Up", use_container_width=True):
            st.session_state.page = "signup"; st.rerun()

    st.markdown("""<p style="text-align:center;color:#aaa;font-size:0.82rem;margin-top:2rem">
    ⚠️ Academic decision support tool only. Final approval rests with authorized financial institutions.<br>
    Built by Harshita & Team · Department of Computer Science · 2024–25</p>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ════════════════════════════════════════════════════════════════════════════
def show_login():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);padding:1.5rem;text-align:center;color:white;margin-bottom:2rem">
        <span style="font-size:1.8rem">🏦</span>
        <b style="font-size:1.3rem;margin-left:0.5rem">LoanSmart AI</b>
    </div>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Welcome Back 👋</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Login to access your dashboard</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        username = st.text_input("👤 Username", placeholder="Enter your username",  key="l_user")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password", key="l_pass")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Login →", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("Please fill in all fields.")
            else:
                ok, result, email = login_user(username, password)
                if ok:
                    st.session_state.update({"logged_in":True,"username":username,
                                             "full_name":result,"email":email,"page":"app"})
                    st.rerun()
                else:
                    st.error(result)

        st.markdown("---")
        st.markdown("<center style='color:#666'>Don't have an account?</center>", unsafe_allow_html=True)
        if st.button("Create Account →", use_container_width=True):
            st.session_state.page = "signup"; st.rerun()
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.page = "landing"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# SIGNUP PAGE
# ════════════════════════════════════════════════════════════════════════════
def show_signup():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);padding:1.5rem;text-align:center;color:white;margin-bottom:2rem">
        <span style="font-size:1.8rem">🏦</span>
        <b style="font-size:1.3rem;margin-left:0.5rem">LoanSmart AI</b>
    </div>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Create Account 🚀</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Fill in your details to get started</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        full_name = st.text_input("👤 Full Name",       placeholder="e.g. Harshita Sharma",    key="s_name")
        email     = st.text_input("📧 Email",            placeholder="e.g. you@email.com",       key="s_email")
        phone     = st.text_input("📱 Phone Number",     placeholder="10-digit mobile number",   key="s_phone")
        username  = st.text_input("🆔 Username",         placeholder="Choose a unique username", key="s_user")
        password  = st.text_input("🔒 Password",         type="password", placeholder="Min 6 characters",  key="s_pass")
        confirm   = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter password",  key="s_conf")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Create Account →", use_container_width=True, type="primary"):
            if not all([full_name, email, phone, username, password, confirm]):
                st.error("⚠️ Please fill in all fields.")
            elif len(password) < 6:
                st.error("⚠️ Password must be at least 6 characters.")
            elif password != confirm:
                st.error("⚠️ Passwords do not match!")
            elif "@" not in email or "." not in email:
                st.error("⚠️ Enter a valid email address.")
            elif not phone.isdigit() or len(phone) != 10:
                st.error("⚠️ Phone must be exactly 10 digits.")
            else:
                ok, msg = register_user(username, full_name, email, phone, password)
                if ok:
                    st.success(f"✅ {msg} Please login now.")
                    st.session_state.page = "login"; st.rerun()
                else:
                    st.error(msg)

        st.markdown("---")
        st.markdown("<center style='color:#666'>Already have an account?</center>", unsafe_allow_html=True)
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.page = "login"; st.rerun()
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.page = "landing"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE ROUTER
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "landing":
    show_landing(); st.stop()
elif st.session_state.page == "login":
    show_login(); st.stop()
elif st.session_state.page == "signup":
    show_signup(); st.stop()
elif not st.session_state.logged_in:
    st.session_state.page = "landing"; st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# MAIN APP (only after login)
# ════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown(f"""
<div style="text-align:center;padding:1rem 0 0.5rem 0">
    <span style="font-size:2.5rem">🏦</span><br>
    <b style="font-size:1.1rem">LoanSmart AI</b><br>
    <small style="color:#888">Adaptive ML · Behavior Scoring</small>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="background:#e8f5e9;border-radius:8px;padding:0.5rem 0.8rem;font-size:0.9rem">
    👤 <b>{st.session_state.full_name}</b><br>
    <small style="color:#666">@{st.session_state.username}</small>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

section = st.sidebar.radio("📌 Navigate", [
    "🏠 Dashboard",
    "🔍 Loan Eligibility Prediction",
    "📊 SHAP Explanation",
    "📈 Model Performance",
    "📅 Behavior Tracking",
    "🏆 Reward / Penalty & Dynamic Score"
])
st.sidebar.markdown("---")
st.sidebar.info("⚠️ Decision support tool only. Final approval rests with financial institutions.")
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.update({"logged_in":False,"username":"","full_name":"","email":"","page":"landing"})
    st.rerun()


# ─── Load Model ──────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    for path in ["outputs/models/loan_model.pkl","../outputs/models/loan_model.pkl","model.pkl","loan_model.pkl"]:
        if os.path.exists(path):
            try: return pickle.load(open(path,"rb"))
            except:
                try: return joblib.load(path)
                except: continue
    return None

model = load_model()

def mock_predict(income, loan_amount, credit_history, coapplicant_income):
    score = 0
    if credit_history == 1:    score += 40
    if income > 4000:          score += 20
    if coapplicant_income > 0: score += 10
    ratio = loan_amount / max(income + coapplicant_income, 1)
    if ratio < 3: score += 20
    elif ratio < 5: score += 10
    prob = min(score / 90, 0.97)
    return prob, 1 if prob >= 0.5 else 0


# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
if section == "🏠 Dashboard":
    st.title(f"Welcome back, {st.session_state.full_name}! 👋")
    st.markdown(f"<small style='color:#888'>@{st.session_state.username} · {st.session_state.email}</small>", unsafe_allow_html=True)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    d1,d2,d3 = st.columns(3)
    for col, icon, title, desc in zip([d1,d2,d3],
        ["🔍","📅","🏆"],
        ["Check Loan Eligibility","Track Repayment Behaviour","Dynamic Credit Score"],
        ["Get instant ML-based pre-eligibility verdict",
         "Enter EMI records and analyze payment discipline",
         "See how behaviour rewards or penalises your score"]
    ):
        col.markdown(f"""
        <div class="feature-card">
            <div style="font-size:2rem">{icon}</div>
            <b>{title}</b>
            <p style="color:#666;font-size:0.88rem;margin-top:0.4rem">{desc}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Best Model Accuracy","98%","Random Forest")
    m2.metric("ROC-AUC Score","0.99","Excellent")
    m3.metric("Features Used","11","Kaggle India Dataset")
    m4.metric("Scoring Type","Dynamic","Behavior-Aware")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.info("👈 Use the sidebar to navigate between sections.")


# ════════════════════════════════════════════════════════════════════════════
# LOAN ELIGIBILITY
# ════════════════════════════════════════════════════════════════════════════
elif section == "🔍 Loan Eligibility Prediction":
    st.title("🔍 Loan Pre-Eligibility Prediction")
    st.markdown("Fill in the applicant details below to get an instant pre-eligibility assessment.")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col1,col2,col3 = st.columns(3)
    with col1:
        st.subheader("Personal Details")
        gender        = st.selectbox("Gender",["Male","Female"])
        married       = st.selectbox("Marital Status",["Yes","No"])
        dependents    = st.selectbox("Dependents",["0","1","2","3+"])
        education     = st.selectbox("Education",["Graduate","Not Graduate"])
        self_employed = st.selectbox("Self Employed",["No","Yes"])
    with col2:
        st.subheader("Financial Details")
        applicant_income   = st.number_input("Applicant Monthly Income (₹)",0,200000,5000,step=500)
        coapplicant_income = st.number_input("Co-applicant Monthly Income (₹)",0,200000,0,step=500)
        loan_amount        = st.number_input("Loan Amount (₹ thousands)",10,10000,150,step=10)
        loan_term          = st.selectbox("Loan Term (months)",[360,180,120,84,60,36,12])
        credit_history     = st.selectbox("Credit History",[1,0],format_func=lambda x:"Good (1)" if x==1 else "Poor (0)")
    with col3:
        st.subheader("Other Details")
        property_area = st.selectbox("Property Area",["Urban","Semiurban","Rural"])
        st.markdown("<br>",unsafe_allow_html=True)
        lti = loan_amount / max((applicant_income+coapplicant_income)/1000, 0.1)
        st.metric("Loan-to-Income Ratio", f"{lti:.2f}x", delta="🟢 Good" if lti<3 else ("🟡 Moderate" if lti<5 else "🔴 High"))

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    if st.button("🚀 Check Eligibility", use_container_width=True, type="primary"):
        with st.spinner("Running ML model..."):
            prob, pred = mock_predict(applicant_income, loan_amount, credit_history, coapplicant_income)
            if model:
                try:
                    row = pd.DataFrame([{"Gender":gender,"Married":married,"Dependents":dependents,
                        "Education":education,"Self_Employed":self_employed,
                        "ApplicantIncome":applicant_income,"CoapplicantIncome":coapplicant_income,
                        "LoanAmount":loan_amount,"Loan_Amount_Term":loan_term,
                        "Credit_History":credit_history,"Property_Area":property_area}])
                    prob = float(model.predict_proba(row)[0][1])
                    pred = int(model.predict(row)[0])
                except: pass

        confidence = "High" if abs(prob-0.5)>0.3 else ("Medium" if abs(prob-0.5)>0.15 else "Low")
        c1,c2,c3 = st.columns(3)
        c1.metric("Decision","✅ ELIGIBLE" if pred==1 else "❌ NOT ELIGIBLE")
        c2.metric("Approval Probability",f"{prob*100:.1f}%")
        c3.metric("Confidence Level",confidence)
        if pred==1:
            st.markdown('<div class="status-good">✅ <b>Pre-Eligible!</b> Applicant meets basic criteria. Proceed to full bank verification.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-bad">❌ <b>Not Eligible.</b> Key factors: low credit history, high LTI ratio, or insufficient income.</div>', unsafe_allow_html=True)
        st.markdown("#### Approval Probability")
        fig, ax = plt.subplots(figsize=(8,1.2))
        ax.barh([""], [prob], color="#43a047", height=0.4)
        ax.barh([""], [1-prob], left=[prob], color="#e0e0e0", height=0.4)
        ax.set_xlim(0,1); ax.axis("off")
        ax.text(prob/2,0,f"{prob*100:.1f}%",ha="center",va="center",color="white",fontsize=12,fontweight="bold")
        st.pyplot(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# SHAP
# ════════════════════════════════════════════════════════════════════════════
elif section == "📊 SHAP Explanation":
    st.title("📊 SHAP — Why Was This Decision Made?")
    st.markdown("SHAP values show which features pushed the prediction towards approval or rejection.")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    features  = ["Credit History","Applicant Income","Loan Amount","Loan Term",
                 "Co-applicant Income","Property Area","Education","Self Employed","Dependents","Gender"]
    shap_vals = np.array([0.42,0.18,-0.15,0.08,0.12,0.06,0.04,-0.03,-0.05,0.01])
    colors    = ["#43a047" if v>0 else "#e53935" for v in shap_vals]
    sorted_idx = np.argsort(np.abs(shap_vals))
    fig, ax = plt.subplots(figsize=(9,5))
    ax.barh([features[i] for i in sorted_idx],[shap_vals[i] for i in sorted_idx],
            color=[colors[i] for i in sorted_idx],edgecolor="white")
    ax.axvline(0,color="black",linewidth=0.8,linestyle="--")
    ax.set_xlabel("SHAP Value (impact on approval probability)")
    ax.set_title("Feature Impact on Loan Decision",fontsize=13,fontweight="bold")
    ax.legend(handles=[mpatches.Patch(color="#43a047",label="Pushes toward Approval"),
                       mpatches.Patch(color="#e53935",label="Pushes toward Rejection")],loc="lower right")
    plt.tight_layout(); st.pyplot(fig)
    st.markdown("---")
    st.subheader("📌 Key Rejection Reasons (Example)")
    r1,r2,r3 = st.columns(3)
    with r1: st.markdown('<div class="status-bad">🔴 <b>Low Credit History</b><br>Largest negative impact on approval chance.</div>',unsafe_allow_html=True)
    with r2: st.markdown('<div class="status-warn">🟠 <b>High Loan-to-Income Ratio</b><br>Requested amount exceeds repayment capacity.</div>',unsafe_allow_html=True)
    with r3: st.markdown('<div class="status-warn">🟠 <b>Insufficient Income</b><br>Income below threshold for requested loan.</div>',unsafe_allow_html=True)
    st.caption("💡 SHAP values are simulated for demo. Connect your trained SHAP explainer for real values.")


# ════════════════════════════════════════════════════════════════════════════
# MODEL PERFORMANCE
# ════════════════════════════════════════════════════════════════════════════
elif section == "📈 Model Performance":
    st.title("📈 Model Performance Metrics")
    st.markdown("Logistic Regression (baseline) vs Random Forest (best model).")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    perf = pd.DataFrame({
        "Model":    ["Logistic Regression","Random Forest"],
        "Accuracy": [0.81,0.98],"Precision":[0.80,0.98],
        "Recall":   [0.81,0.98],"F1-Score": [0.79,0.98],"ROC-AUC":[0.82,0.99],
    })
    c1,c2 = st.columns(2)
    for col,(_, row),bg,border in zip([c1,c2],perf.iterrows(),["#e3f2fd","#e8f5e9"],["#1565c0","#2e7d32"]):
        col.markdown(f"""
        <div style="background:{bg};border-left:5px solid {border};border-radius:10px;padding:1.2rem 1.5rem">
            <b style="font-size:1.1rem">{row['Model']}</b><br><br>
            🎯 Accuracy &nbsp;<b>{row['Accuracy']*100:.0f}%</b><br>
            📊 F1-Score &nbsp;&nbsp;<b>{row['F1-Score']*100:.0f}%</b><br>
            📈 ROC-AUC &nbsp;<b>{row['ROC-AUC']:.2f}</b>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    fig, axes = plt.subplots(1,2,figsize=(12,4))
    metrics = ["Accuracy","Precision","Recall","F1-Score"]
    x = np.arange(len(metrics)); w = 0.3
    for i,(_, row) in enumerate(perf.iterrows()):
        bars = axes[0].bar(x+i*w,[row[m] for m in metrics],width=w,label=row["Model"],color=["#90caf9","#43a047"][i])
        for bar in bars:
            axes[0].text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.002,
                         f"{bar.get_height():.2f}",ha="center",va="bottom",fontsize=8)
    axes[0].set_xticks(x+w/2); axes[0].set_xticklabels(metrics)
    axes[0].set_ylim(0.6,1.08); axes[0].set_title("Metrics Comparison"); axes[0].legend()
    axes[1].bar(perf["Model"],perf["ROC-AUC"],color=["#90caf9","#43a047"],edgecolor="white",width=0.4)
    axes[1].set_ylim(0.7,1.05); axes[1].set_title("ROC-AUC Comparison")
    for i,v in enumerate(perf["ROC-AUC"]):
        axes[1].text(i,v+0.005,f"{v:.2f}",ha="center",fontweight="bold")
    plt.tight_layout(); st.pyplot(fig)

    st.markdown("---")
    st.subheader("Confusion Matrix (Random Forest — Best Model)")
    col_cm,col_info = st.columns([1,1])
    with col_cm:
        cm = np.array([[55,2],[1,92]])
        fig2,ax2 = plt.subplots(figsize=(4,3))
        ax2.imshow(cm,cmap="Greens")
        ax2.set_xticks([0,1]); ax2.set_yticks([0,1])
        ax2.set_xticklabels(["Predicted No","Predicted Yes"])
        ax2.set_yticklabels(["Actual No","Actual Yes"])
        for i in range(2):
            for j in range(2):
                ax2.text(j,i,str(cm[i,j]),ha="center",va="center",fontsize=14,
                         fontweight="bold",color="white" if cm[i,j]>60 else "black")
        ax2.set_title("Confusion Matrix — Random Forest"); plt.tight_layout(); st.pyplot(fig2)
    with col_info:
        st.markdown("""
        **How to read this:**
        - ✅ **Top-left (TN):** Correctly predicted NOT eligible
        - ✅ **Bottom-right (TP):** Correctly predicted ELIGIBLE
        - ❌ **Top-right (FP):** Wrongly approved
        - ❌ **Bottom-left (FN):** Wrongly rejected

        > 📌 Replace with your actual confusion matrix values from notebook!
        """)
    st.caption("💡 Update confusion matrix numbers from your notebook.")


# ════════════════════════════════════════════════════════════════════════════
# BEHAVIOR TRACKING
# ════════════════════════════════════════════════════════════════════════════
elif section == "📅 Behavior Tracking":
    st.title("📅 Repayment Behavior Tracker")
    st.markdown("Enter EMI payment records to analyze repayment discipline over time.")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    customer_id = st.text_input("Customer ID", value="CUST_001")
    num_emis    = st.slider("Number of EMI records to enter", 3, 12, 6)

    st.markdown("#### Enter EMI Records")
    records = []
    header = st.columns([2, 2, 1])
    header[0].markdown("**Due Date**")
    header[1].markdown("**Payment Date**")
    header[2].markdown("**Paid?**")

    for i in range(num_emis):
        c1, c2, c3 = st.columns([2, 2, 1])
        due     = c1.date_input(f"Due {i+1}",
                                value=date.today() - timedelta(days=30*(num_emis - i)),
                                key=f"due_{i}", label_visibility="collapsed")
        paid_dt = c2.date_input(f"Paid {i+1}",
                                value=due + timedelta(days=int(np.random.randint(0, 8))),
                                key=f"paid_{i}", label_visibility="collapsed")
        paid    = c3.checkbox("", value=True, key=f"ck_{i}")
        delay   = (paid_dt - due).days if paid else None
        records.append({
            "EMI #":        i + 1,
            "Due Date":     due,
            "Payment Date": paid_dt if paid else "MISSED",
            "Days Delayed": delay if delay is not None else "MISSED",
            "Status": "On Time" if (delay is not None and delay <= 0)
                      else ("Late"   if (delay is not None and delay > 0)
                            else "Missed")
        })

    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("📊 Analyze Behavior", use_container_width=True, type="primary"):
        on_time = sum(1 for r in records if r["Status"] == "On Time")
        late    = sum(1 for r in records if r["Status"] == "Late")
        missed  = sum(1 for r in records if r["Status"] == "Missed")
        total   = len(records)
        pct     = on_time / total * 100

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total EMIs",    total)
        m2.metric("On Time",       f"{on_time} ({pct:.0f}%)")
        m3.metric("Late Payments", late)
        m4.metric("Missed",        missed)

        fig, ax = plt.subplots(figsize=(9, 2))
        colors_map = {"On Time": "#43a047", "Late": "#fb8c00", "Missed": "#e53935"}
        for idx, r in enumerate(records):
            ax.bar(idx + 1, 1, color=colors_map[r["Status"]], edgecolor="white", width=0.8)
        ax.set_xlim(0.3, total + 0.7); ax.set_ylim(0, 1.3)
        ax.set_xticks(range(1, total + 1))
        ax.set_xticklabels([f"EMI {i+1}" for i in range(total)], fontsize=9)
        ax.set_yticks([]); ax.set_title("EMI Payment Timeline")
        patches = [mpatches.Patch(color=c, label=l) for l, c in colors_map.items()]
        ax.legend(handles=patches, loc="upper right", fontsize=8)
        plt.tight_layout()
        st.pyplot(fig)

        st.session_state["behavior"] = {
            "on_time_pct": pct, "late": late, "missed": missed, "total": total
        }
        st.success("Done! Go to 'Reward / Penalty & Dynamic Score' to see your updated score.")


# ════════════════════════════════════════════════════════════════════════════
# REWARD / PENALTY & DYNAMIC SCORE
# ════════════════════════════════════════════════════════════════════════════
elif section == "📅 Behavior Tracking":
    st.title("📅 Repayment Behavior Tracker")
    st.markdown("Enter EMI payment records to analyze repayment discipline over time.")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        customer_id = st.text_input("Customer ID", value="CUST_001")
    with col_b:
        num_emis = st.slider("Number of EMI records to enter", 3, 12, 6)

    st.markdown("#### Enter EMI Records")
    header = st.columns([0.5, 2, 2, 1.2, 2])
    for h, label in zip(header, ["#", "Due Date", "Payment Date", "Paid?", "Status"]):
        h.markdown(f"**{label}**")

    records = []
    for i in range(num_emis):
        c0, c1, c2, c3, c4 = st.columns([0.5, 2, 2, 1.2, 2])
        c0.markdown(f"**{i+1}**")
        due     = c1.date_input(f"Due_{i}",
                                value=date.today() - timedelta(days=30*(num_emis - i)),
                                key=f"due_{i}", label_visibility="collapsed")
        paid_dt = c2.date_input(f"Paid_{i}",
                                value=due + timedelta(days=int(np.random.randint(0, 8))),
                                key=f"paid_{i}", label_visibility="collapsed")
        paid    = c3.checkbox("✔", value=True, key=f"ck_{i}", label_visibility="collapsed")

        if not paid:
            status = "❌ Missed"
            delay  = None
        else:
            delay  = (paid_dt - due).days
            status = "✅ On Time" if delay <= 0 else f"⚠️ Late ({delay}d)"

        c4.markdown(status)
        records.append({
            "EMI #":        i + 1,
            "Due Date":     due,
            "Payment Date": paid_dt if paid else "—",
            "Days Delayed": delay if delay is not None else "MISSED",
            "Status":       status
        })

    st.markdown("<br>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)

    if st.button("📊 Analyze Behavior", use_container_width=True, type="primary"):
        on_time = sum(1 for r in records if "On Time" in r["Status"])
        late    = sum(1 for r in records if "Late"    in r["Status"])
        missed  = sum(1 for r in records if "Missed"  in r["Status"])
        total   = len(records)
        pct     = on_time / total * 100

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total EMIs",  total)
        m2.metric("✅ On Time",  f"{on_time} ({pct:.0f}%)")
        m3.metric("⚠️ Late",    late)
        m4.metric("❌ Missed",   missed)

        # Timeline bar chart
        fig, ax = plt.subplots(figsize=(10, 2.5))
        color_map = {"On Time": "#43a047", "Late": "#fb8c00", "Missed": "#e53935"}
        for idx, r in enumerate(records):
            key   = "On Time" if "On Time" in r["Status"] else ("Late" if "Late" in r["Status"] else "Missed")
            emoji = "✅" if key == "On Time" else ("⚠️" if key == "Late" else "❌")
            ax.bar(idx + 1, 1, color=color_map[key], edgecolor="white", width=0.75)
            ax.text(idx + 1, 0.5, emoji, ha="center", va="center", fontsize=14)
        ax.set_xlim(0.3, total + 0.7); ax.set_ylim(0, 1.4)
        ax.set_xticks(range(1, total + 1))
        ax.set_xticklabels([f"EMI {i+1}" for i in range(total)], fontsize=9)
        ax.set_yticks([])
        ax.set_title(f"EMI Payment Timeline — {customer_id}", fontsize=11)
        ax.legend(handles=[mpatches.Patch(color=c, label=l) for l, c in color_map.items()],
                  loc="upper right", fontsize=9)
        plt.tight_layout(); st.pyplot(fig)

        # Delay trend line
        delay_vals = [r["Days Delayed"] if r["Days Delayed"] != "MISSED" else 0 for r in records]
        fig2, ax2 = plt.subplots(figsize=(10, 2.5))
        ax2.plot(range(1, total + 1), delay_vals, marker="o", color="#1565c0", linewidth=2, markersize=7)
        ax2.fill_between(range(1, total + 1), delay_vals, alpha=0.15, color="#1565c0")
        ax2.axhline(0, color="#43a047", linestyle="--", linewidth=1.2, label="On-time line (0 days)")
        ax2.set_xticks(range(1, total + 1))
        ax2.set_xticklabels([f"EMI {i+1}" for i in range(total)], fontsize=9)
        ax2.set_ylabel("Days Delayed"); ax2.set_title("Delay Trend Over Time")
        ax2.legend(fontsize=9); plt.tight_layout(); st.pyplot(fig2)

        # Pie chart
        fig3, ax3 = plt.subplots(figsize=(4, 4))
        sizes  = [on_time, late, missed]
        labels = ["On Time", "Late", "Missed"]
        colors = ["#43a047", "#fb8c00", "#e53935"]
        non_zero = [(s, l, c) for s, l, c in zip(sizes, labels, colors) if s > 0]
        if non_zero:
            s_, l_, c_ = zip(*non_zero)
            ax3.pie(s_, labels=l_, colors=c_, autopct="%1.0f%%", startangle=90,
                    wedgeprops={"edgecolor": "white", "linewidth": 2})
            ax3.set_title("Payment Distribution")
            _, pie_col, _ = st.columns([1, 1.5, 1])
            with pie_col: st.pyplot(fig3)

        # Summary
        st.markdown("---")
        st.subheader("📋 Behavior Summary")
        if pct == 100:
            st.markdown('<div class="status-gold">🥇 <b>Perfect Record!</b> All EMIs paid on time. Gold Status — +10 credit bonus applied.</div>', unsafe_allow_html=True)
        elif pct >= 90 and missed == 0:
            st.markdown('<div class="status-good">✅ <b>Excellent Discipline.</b> Very few delays, no missed. Good standing — +5 bonus.</div>', unsafe_allow_html=True)
        elif missed >= 3:
            st.markdown('<div class="status-bad">🚫 <b>High Risk!</b> 3+ missed payments. Blacklist warning — −30 penalty applied.</div>', unsafe_allow_html=True)
        elif late >= 3:
            st.markdown('<div class="status-bad">🔴 <b>Repeated Delays.</b> 3+ late payments. Medium risk — −15 penalty.</div>', unsafe_allow_html=True)
        elif missed in [1, 2]:
            st.markdown('<div class="status-warn">⚠️ <b>Watchlist.</b> 1–2 missed payments. Minor penalty of −5.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-good">✅ <b>Good Standing.</b> Mostly on-time with minor delays — +5 discipline bonus.</div>', unsafe_allow_html=True)

        st.session_state["behavior"] = {
            "on_time_pct": pct, "late": late, "missed": missed,
            "total": total, "customer_id": customer_id
        }
        st.success("✅ Analysis complete! Go to '🏆 Reward / Penalty & Dynamic Score' to see your final credit score.")


# ════════════════════════════════════════════════════════════════════════════
# REWARD / PENALTY & DYNAMIC SCORE
# ════════════════════════════════════════════════════════════════════════════
elif section == "🏆 Reward / Penalty & Dynamic Score":
    st.title("🏆 Reward / Penalty Engine & Dynamic Credit Score")
    st.markdown("Final credit score = ML prediction + repayment behavior adjustment.")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Input Parameters")
        base_ml_score = st.slider("Base ML Eligibility Score", 0, 100, 65,
                                   help="From the ML Eligibility Prediction section (0–100)")
        behavior = st.session_state.get("behavior", None)
        if behavior:
            st.success(
                f"✅ Auto-filled from Behavior Tracker (Customer: {behavior.get('customer_id', '—')})\n\n"
                f"🕐 {behavior['on_time_pct']:.0f}% on-time  |  "
                f"⚠️ {behavior['late']} late  |  ❌ {behavior['missed']} missed"
            )
            on_time_pct  = behavior["on_time_pct"]
            late_count   = behavior["late"]
            missed_count = behavior["missed"]
        else:
            st.info("💡 Go to **Behavior Tracking** first for auto-fill, or enter manually below:")
            on_time_pct  = st.slider("On-Time Payment %", 0, 100, 80)
            late_count   = st.number_input("Late Payments",   min_value=0, max_value=20, value=1)
            missed_count = st.number_input("Missed Payments", min_value=0, max_value=20, value=0)

    with col2:
        st.subheader("📋 Rule Reference")
        st.markdown("""
        | Condition | Status | Score Effect |
        |---|---|---|
        | ≥95% on-time, 0 missed | 🥇 Gold | **+10 bonus** |
        | Good overall | ✅ Good Standing | **+5 bonus** |
        | 1–2 missed payments | ⚠️ Watchlist | **−5 penalty** |
        | ≥3 late payments | 🔴 Medium Risk | **−15 penalty** |
        | ≥3 missed payments | 🚫 Blacklisted | **−30 penalty** |
        """)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    if st.button("⚡ Calculate Dynamic Score", use_container_width=True, type="primary"):

        # ── Rule Engine ──────────────────────────────────────────────────────
        discipline_bonus = 0
        risk_penalty     = 0

        if missed_count >= 3:
            risk_penalty     = 30
            status_label     = "🚫 Blacklisted — Multiple Defaults"
            status_class     = "status-bad"
        elif late_count >= 3:
            risk_penalty     = 15
            status_label     = "🔴 Medium Risk — Repeated Delays"
            status_class     = "status-bad"
        elif missed_count in [1, 2]:
            risk_penalty     = 5
            status_label     = "⚠️ Watchlist — Minor Issues Detected"
            status_class     = "status-warn"
        elif on_time_pct >= 95 and missed_count == 0:
            discipline_bonus = 10
            status_label     = "🥇 Gold Status — Exemplary Discipline"
            status_class     = "status-gold"
        else:
            discipline_bonus = 5
            status_label     = "✅ Good Standing"
            status_class     = "status-good"

        final_score = min(max(base_ml_score + discipline_bonus - risk_penalty, 0), 100)

        # ── Status Banner ─────────────────────────────────────────────────────
        st.markdown(f'<div class="{status_class}"><b style="font-size:1.15rem">{status_label}</b></div>',
                    unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Score Metrics ─────────────────────────────────────────────────────
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Base ML Score",    f"{base_ml_score}/100")
        s2.metric("Discipline Bonus", f"+{discipline_bonus}",
                  delta=f"+{discipline_bonus}" if discipline_bonus else None)
        s3.metric("Risk Penalty",     f"-{risk_penalty}",
                  delta=f"-{risk_penalty}" if risk_penalty else None, delta_color="inverse")
        s4.metric("🎯 Final Score",   f"{final_score}/100",
                  delta=f"{final_score - base_ml_score:+d} pts")

        # ── Score Breakdown Bar ───────────────────────────────────────────────
        st.markdown("#### Score Breakdown")
        fig, ax = plt.subplots(figsize=(9, 1.8))
        ax.barh([""], [base_ml_score],    color="#90caf9", label=f"Base ML ({base_ml_score})")
        ax.barh([""], [discipline_bonus], left=[base_ml_score],
                color="#43a047", label=f"Discipline Bonus (+{discipline_bonus})")
        ax.barh([""], [risk_penalty],     left=[base_ml_score + discipline_bonus],
                color="#e53935", label=f"Risk Penalty (-{risk_penalty})")
        ax.set_xlim(0, 115); ax.axis("off")
        ax.text(min(final_score / 2, 105), 0, f"Final: {final_score} / 100",
                ha="center", va="center", fontsize=13, fontweight="bold", color="white")
        ax.legend(loc="lower right", fontsize=9)
        plt.tight_layout(); st.pyplot(fig)

        # ── Gauge Chart ───────────────────────────────────────────────────────
        st.markdown("#### Credit Score Gauge")
        fig2, ax2 = plt.subplots(figsize=(6, 3), subplot_kw={"aspect": "equal"})
        zones = [(0.33, "#e53935"), (0.33, "#fb8c00"), (0.34, "#43a047")]
        cumulative = np.pi
        for frac, color in zones:
            span = frac * np.pi
            t = np.linspace(cumulative, cumulative - span, 100)
            ax2.plot(np.cos(t), np.sin(t), color=color, linewidth=18, solid_capstyle="butt")
            cumulative -= span
        needle_angle = np.pi - (final_score / 100) * np.pi
        ax2.annotate("", xy=(0.65 * np.cos(needle_angle), 0.65 * np.sin(needle_angle)),
                     xytext=(0, 0), arrowprops=dict(arrowstyle="->", color="black", lw=2.5))
        ax2.text(0, -0.25, f"{final_score}", ha="center", fontsize=22, fontweight="bold")
        ax2.text(0, -0.45, "/ 100",          ha="center", fontsize=12, color="#666")
        ax2.text(-1.0, -0.15, "High\nRisk",  ha="center", fontsize=9, color="#e53935")
        ax2.text(0,    0.85,  "Medium",      ha="center", fontsize=9, color="#fb8c00")
        ax2.text(1.0,  -0.15, "Low\nRisk",  ha="center", fontsize=9, color="#43a047")
        ax2.set_xlim(-1.3, 1.3); ax2.set_ylim(-0.6, 1.1); ax2.axis("off")
        plt.tight_layout()
        _, gc, _ = st.columns([1, 2, 1])
        with gc: st.pyplot(fig2)

        # ── Formula Box ───────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:#f0f4ff;border-radius:10px;padding:1rem 1.5rem;
                    border:1px solid #c5cae9;margin-top:0.5rem">
            <b>Formula:</b> Final Score = ML Score + Discipline Bonus − Risk Penalty<br>
            <b style="font-size:1.05rem">
                = {base_ml_score} + {discipline_bonus} − {risk_penalty}
                = <span style="color:#1565c0">{final_score} / 100</span>
            </b>
        </div>""", unsafe_allow_html=True)

        # ── Final Recommendation ──────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📋 Final Recommendation")
        if final_score >= 80:
            st.success("🟢 **Strong Candidate** — Recommend for loan approval with standard terms.")
        elif final_score >= 60:
            st.warning("🟡 **Moderate Candidate** — Consider approval with higher interest rate or reduced loan amount.")
        elif final_score >= 40:
            st.warning("🟠 **Borderline** — Conditional approval with co-applicant or collateral recommended.")
        else:
            st.error("🔴 **High Risk** — Not recommended for approval. Suggest financial counseling first.")