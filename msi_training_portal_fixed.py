import os
import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import hashlib
import random
from PIL import Image, ImageDraw

# =========================
# PAGE CONFIG
# =========================
icon_path = os.path.join("assets", "favicon.png")
page_icon = Image.open(icon_path)

st.set_page_config(
    page_title="MSI Nigeria – Training Portal",
    page_icon=page_icon,
    layout="wide"
)


# =========================
# MSI BRAND COLORS
# =========================
MSI_BLUE = "#0099D8"
MSI_DARK_BLUE = "#005B8F"
MSI_BG = "#F4FAFD"

# =========================
# LOGO
# =========================
def show_logo(width=140):
    logo_path = os.path.join("assets", "msi_logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=width)
    else:
        img = Image.new("RGB", (200, 200), MSI_BLUE)
        draw = ImageDraw.Draw(img)
        draw.text((60, 80), "MSI", fill="white")
        draw.text((40, 115), "NIGERIA", fill="white")
        st.image(img, width=width)

# =========================
# STYLES
# =========================
st.markdown(f"""
<style>

/* ========== GLOBAL BACKGROUND ========== */
body {{
    background-color: {MSI_BG};
}}

/* ========== PAGE WIDTH CONTROL ========== */
.block-container {{
    max-width: 1200px;
    padding-top: 1.5rem;
}}

/* ========== SECTION HEADERS ========== */
h3, h4 {{
    margin-bottom: 0.6rem;
    color: {MSI_DARK_BLUE};
}}

/* ========== CARD STYLE (BOOTSTRAP-LIKE) ========== */
.section {{
    background: white;
    padding: 18px 22px;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    margin-bottom: 18px;
    border-left: 4px solid {MSI_BLUE};
}}

/* ========== LABELS ========== */
label {{
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #444 !important;
    margin-bottom: 2px !important;
}}

/* ========== INPUT FIELDS (SHORTER + CLEANER) ========== */
input, textarea, select {{
    min-height: 38px !important;
    font-size: 0.9rem !important;
    border-radius: 8px !important;
    padding: 6px 10px !important;
}}

/* ========== SELECTBOX WIDTH CONTROL ========== */
div[data-baseweb="select"] {{
    max-width: 100%;
}}

div[data-baseweb="select"] > div {{
    min-height: 38px !important;
    border-radius: 8px !important;
}}

/* ========== FILE UPLOADER COMPACT ========== */
section[data-testid="stFileUploader"] {{
    padding: 10px;
    border: 1px dashed #ccc;
    border-radius: 10px;
    background: #fafafa;
}}

section[data-testid="stFileUploader"] button {{
    font-size: 0.8rem;
    padding: 6px 12px;
}}

/* ========== BUTTONS (BOOTSTRAP PRIMARY STYLE) ========== */
.stButton > button {{
    background-color: {MSI_BLUE};
    color: white;
    border-radius: 10px;
    height: 42px;
    font-size: 0.95rem;
    font-weight: 600;
    width: 100%;
    border: none;
}}

.stButton > button:hover {{
    background-color: {MSI_DARK_BLUE};
    transform: translateY(-1px);
}}

/* ========== FORM SPACING ========== */
form {{
    padding-top: 0.5rem;
}}

div[data-testid="column"] {{
    padding-right: 10px;
}}

/* ========== SUCCESS CARD ========== */
.success-card {{
    background-color: white;
    padding: 22px;
    border-radius: 14px;
    border: 2px solid {MSI_BLUE};
    text-align: center;
}}

</style>
""", unsafe_allow_html=True)


# =========================
# LOAD EXCEL DATA (CASCADE + COST CENTRES)
# =========================
@st.cache_data
def load_excel_data():
    # Load from app folder (place cascade.xlsx in same folder as your app.py)
    path = os.path.join(os.path.dirname(__file__), "cascade.xlsx")
    
    # If not found, try current directory
    if not os.path.exists(path):
        path = "cascade.xlsx"
    
    # Load the data
    df = pd.read_excel(path, sheet_name="CostCentres")
    
    # Clean the data
    df = df.dropna(subset=["Region", "State", "LGA"])
    
    # Get unique cost centres (sorted)
    cost_centres = sorted(df["CostCentre"].dropna().unique().tolist())
    
    # Get unique facility types and provider cadres
    facility_types = sorted(df["Facility Type"].dropna().unique().tolist())
    provider_cadres = sorted(df["Provider Cadre"].dropna().unique().tolist())
    
    return df, cost_centres, facility_types, provider_cadres

location_df, cost_centres, facility_types, provider_cadres = load_excel_data()

# =========================
# SUPABASE
# =========================
def init_supabase():
    from supabase import create_client
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

try:
    supabase = init_supabase()
except Exception:
    supabase = None
    st.warning("⚠️ Running in demo mode (no database)")

# =========================
# HELPERS
# =========================
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def generate_enrollment_id(first_name, surname, sb):
    initials = f"{first_name[0].upper()}{surname[-1].upper()}"
    ym = datetime.now().strftime("%Y%m")
    base = f"MSI-{initials}-{ym}"
    if sb:
        res = sb.table("enrollments").select("enrollment_id").like(
            "enrollment_id", f"{base}-%"
        ).execute()
        count = len(res.data) + 1
    else:
        count = random.randint(1, 999)
    return f"{base}-{count:03d}"

def is_admin(email):
    if not supabase:
        return email == "admin@msi.org"
    res = supabase.table("users").select("is_admin").eq("email", email).execute()
    return bool(res.data and res.data[0]["is_admin"])

# =========================
# SESSION
# =========================
st.session_state.setdefault("user", None)

# =========================
# AUTH
# =========================
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        show_logo()
        st.markdown("<h3 style='text-align:center;'>MSI Nigeria Login</h3>", unsafe_allow_html=True)

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if not supabase:
                st.session_state.user = {"email": email, "is_admin": email == "admin@msi.org"}
                st.rerun()
            else:
                res = supabase.table("users").select("*").eq("email", email).execute()
                if res.data and res.data[0]["password"] == hash_password(password):
                    st.session_state.user = res.data[0]
                    st.rerun()
                else:
                    st.error("Invalid login")
    st.stop()

# =========================
# MAIN APP
# =========================
admin = is_admin(st.session_state.user["email"])

col_logo, col_title = st.columns([1, 6])
with col_logo:
    show_logo(90)
with col_title:
    st.markdown("<h2>MSI Nigeria – Training Portal</h2>", unsafe_allow_html=True)

pages = ["📝 Enroll for Training", "📊 View Enrollments"]
if admin:
    pages.append("⬇️ Admin Downloads")

page = st.sidebar.radio("Navigation", pages)

if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ENROLL PAGE (WITH WORKING CASCADE)
# =========================
if page == "📝 Enroll for Training":
    st.subheader("Training Enrollment")

    # 🔹 CASCADE OUTSIDE FORM - This allows real-time updates
    st.markdown("### Select Location")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Region dropdown
        available_regions = sorted(location_df["Region"].dropna().unique())
        region = st.selectbox(
            "Region *",
            available_regions,
            key="region_select"
        )
    
    with col2:
        # State dropdown (filtered by region)
        region_filtered = location_df[location_df["Region"] == region]
        available_states = sorted(region_filtered["State"].dropna().unique())
        state = st.selectbox(
            "State *",
            available_states,
            key="state_select"
        )
    
    with col3:
        # LGA dropdown (filtered by state and region)
        state_filtered = region_filtered[region_filtered["State"] == state]
        available_lgas = sorted(state_filtered["LGA"].dropna().unique())
        lga = st.selectbox(
            "LGA *",
            available_lgas,
            key="lga_select"
        )

    # Rest of the form
    st.markdown("### Training Details")
    
    with st.form("enroll"):
        # Basic Information
        col1, col2 = st.columns(2)
        first = col1.text_input("First Name *")
        last = col2.text_input("Surname *")
        phone = st.text_input("Phone Number *")

        # Channel
        channel = st.selectbox("Channel *", ["PSS", "LA"])

        # Cost Centre (searchable selectbox)
        st.markdown("### Facility Information")
        cost_centre = st.selectbox(
            "Cost Centre *",
            cost_centres,
            help="Start typing to search for cost centre"
        )

        # Facility Type
        facility_type = st.selectbox("Facility Type *", facility_types)

        # Provider Cadre
        provider_cadre = st.selectbox("Provider Cadre *", provider_cadres)

        # Provider Gender
        provider_gender = st.selectbox("Provider Gender *", ["Female", "Male"])

        # Training Information
        st.markdown("### Training Details")
        training = st.selectbox(
            "Training Type *",
            ["IUD Training", "Implant Training", "LARC Beginners Training", "Data Management Training"]
        )
        
        date = st.date_input("Training Date *")

        # File uploads
        st.markdown("### Required Documents")
        supporting_docs = st.file_uploader(
            "Supporting Documents (min 2) *", 
            accept_multiple_files=True,
            type=["pdf", "jpg", "png"]
        )

        submit = st.form_submit_button("Submit Enrollment", use_container_width=True)

    if submit:
        # Validation
        if not all([first, last, phone, channel, region, state, lga, 
                   cost_centre, facility_type, provider_cadre, provider_gender, 
                   training]) or len(supporting_docs) < 2:
            st.error("⚠️ Please complete all required fields and upload at least 2 supporting documents")
        else:
            # Generate enrollment ID
            eid = generate_enrollment_id(first, last, supabase)

            # Prepare record
            record = {
                "id": str(uuid.uuid4()),
                "enrollment_id": eid,
                "first_name": first,
                "surname": last,
                "phone_number": phone,
                "channel": channel,
                "region": region,
                "state": state,
                "lga": lga,
                "cost_centre": cost_centre,
                "facility_type": facility_type,
                "provider_cadre": provider_cadre,
                "provider_gender": provider_gender,
                "training_type": training,
                "training_date": str(date),
                "email": st.session_state.user["email"],
                "status": "Submitted",
                "created_at": datetime.now().isoformat()
            }

            if supabase:
                try:
                    # Upload supporting documents only
                    eid_folder = record["id"]
                    
                    docs = []
                    for i, d in enumerate(supporting_docs, 1):
                        p = f"{eid_folder}/doc_{i}_{d.name}"
                        supabase.storage.from_("enrollments").upload(
                        p,
                        d.read(),
                        {"content-type": d.type}
                 )

                        docs.append(p)

                    # Add file paths to record
                    record["supporting_documents"] = docs

                    # Insert into database
                    supabase.table("enrollments").insert(record).execute()

                    st.success("✅ Enrollment submitted successfully!")
                    st.balloons()
                    
                    # Display enrollment ID
                    st.markdown(f"""
                    <div style='background-color: {MSI_BG}; padding: 20px; border-radius: 10px; 
                                border: 2px solid {MSI_BLUE}; text-align: center; margin-top: 20px;'>
                        <h3 style='color: {MSI_DARK_BLUE};'>🎉 Your Enrollment ID</h3>
                        <h1 style='color: {MSI_BLUE}; font-family: monospace; font-size: 2.5em; 
                                   letter-spacing: 2px;'>{eid}</h1>
                        <p style='color: #666; font-size: 14px;'>
                            📋 Please save this ID for your records
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error submitting enrollment: {str(e)}")
            else:
                st.success("✅ Enrollment submitted (Demo mode)")
                st.markdown(f"### Enrollment ID: `{eid}`")

# =========================
# VIEW PAGE
# =========================
elif page == "📊 View Enrollments":
    st.subheader("Your Enrollments")
    
    if not supabase:
        st.info("Demo mode - No enrollments to display")
    else:
        data = supabase.table("enrollments").select("*").eq(
            "email", st.session_state.user["email"]
        ).execute().data

        if data:
            df = pd.DataFrame(data)
            
            # Select columns to display
            display_cols = [
                'enrollment_id', 'first_name', 'surname', 'phone_number',
                'channel', 'region', 'state', 'lga', 'training_type', 
                'training_date', 'status'
            ]
            
            # Filter to only existing columns
            display_cols = [col for col in display_cols if col in df.columns]
            df_display = df[display_cols]
            
            # Rename for better display
            column_names = {
                'enrollment_id': 'Enrollment ID',
                'first_name': 'First Name',
                'surname': 'Surname',
                'phone_number': 'Phone',
                'channel': 'Channel',
                'region': 'Region',
                'state': 'State',
                'lga': 'LGA',
                'training_type': 'Training',
                'training_date': 'Date',
                'status': 'Status'
            }
            df_display = df_display.rename(columns=column_names)
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            st.caption(f"Total Enrollments: {len(df)}")
        else:
            st.info("No enrollments found")

# =========================
# ADMIN PAGE
# =========================
elif page == "⬇️ Admin Downloads" and admin:
    st.subheader("Admin Downloads")

    if not supabase:
        st.info("Demo mode – no data available")
    else:
        data = supabase.table("enrollments").select("*").execute().data

        if not data:
            st.info("No enrollments found")
        else:
            df = pd.DataFrame(data)
            
            # Search functionality
            search = st.text_input("🔍 Search by Enrollment ID, Name, or Region", "")
            
            if search:
                mask = (
                    df['enrollment_id'].str.contains(search, case=False, na=False) |
                    df['first_name'].str.contains(search, case=False, na=False) |
                    df['surname'].str.contains(search, case=False, na=False) |
                    df['region'].str.contains(search, case=False, na=False)
                )
                filtered_df = df[mask]
            else:
                filtered_df = df
            
            # Download button
            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Enrollments (CSV)",
                data=csv,
                file_name=f"msi_enrollments_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

            # Display data
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(filtered_df)} of {len(df)} enrollments")