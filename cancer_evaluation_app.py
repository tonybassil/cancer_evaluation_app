import gspread
from oauth2client.service_account import ServiceAccountCredentials
def save_to_google_sheet(record):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    #creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    import json
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    client = gspread.authorize(creds)
    sheet = client.open("Evaluations").sheet1  # Your Google Sheet name
    sheet.append_row(list(record.values()))
    

import streamlit as st
from datetime import date
import pandas as pd
import os
from fpdf import FPDF
import base64

st.set_page_config(page_title="Cancer Drug Evaluation", layout="centered")

# --- FORM RESET ---
if "clear_trigger" not in st.session_state:
    st.session_state.clear_trigger = False

if st.session_state.clear_trigger:
    st.session_state.clear()
    st.session_state.submitted = False  # Reset lock
    st.session_state.clear_trigger = False
    st.rerun()

# --- Default values ---
defaults = {
    "submitted": False,
    "name": "",
    "insured_no": "",
    "evaluation_date": date.today(),
    "fda_approved": "-- Select --",
    "guideline_supported": "-- Select --",
    "stage": "-- Select --",
    "prior_treatment_failed": "-- Select --",
    "ecog": "-- Select --",
    "age": 0,
    "cost": 0.0,
    "survival_gain": 0.0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- Logo and title ---
st.image("BEST ASSISTANCE.JPG", use_container_width=False)
st.title("🧪 Cancer Drug Coverage Evaluation")

# --- Clear form button ---
if st.button("🧹 New / Clear Form"):
    st.session_state.clear_trigger = True
    st.rerun()

disabled = st.session_state.submitted

# --- Patient Information ---
st.header("Patient Information")
st.text_input("👤 Patient Name", value=st.session_state.name,
              key="name", disabled=disabled)
st.text_input("🆔 Insured Number", value=st.session_state.insured_no,
              key="insured_no", disabled=disabled)
st.date_input("📅 Evaluation Date", value=st.session_state.evaluation_date,
              key="evaluation_date", disabled=disabled)

# --- Clinical Criteria ---
st.header("Clinical Criteria")
st.selectbox("✅ FDA Approved?", ["-- Select --", "YES", "NO"], index=["-- Select --", "YES",
             "NO"].index(st.session_state.fda_approved), key="fda_approved", disabled=disabled)
st.selectbox("📚 Guideline Supported?", ["-- Select --", "YES", "NO"], index=["-- Select --", "YES", "NO"].index(
    st.session_state.guideline_supported), key="guideline_supported", disabled=disabled)
st.selectbox("🎯 Cancer Stage", ["-- Select --", "1", "2", "3", "4"], index=["-- Select --",
             "1", "2", "3", "4"].index(st.session_state.stage), key="stage", disabled=disabled)
st.selectbox("💊 Prior Treatment Failed?", ["-- Select --", "YES", "NO"], index=["-- Select --", "YES", "NO"].index(
    st.session_state.prior_treatment_failed), key="prior_treatment_failed", disabled=disabled)
st.selectbox("🚶 ECOG Performance", ["-- Select --", "ECOG 0", "ECOG 1", "ECOG 2", "ECOG 3"], index=[
             "-- Select --", "ECOG 0", "ECOG 1", "ECOG 2", "ECOG 3"].index(st.session_state.ecog), key="ecog", disabled=disabled)
st.number_input("🔢 Patient Age", min_value=0, max_value=120,
                step=1, key="age", disabled=disabled)
st.number_input("💰 Cost of Protocol (USD)", min_value=0.0,
                step=100.0, key="cost", disabled=disabled)
st.number_input("📈 Survival Gain (months)", min_value=0.0,
                step=0.1, key="survival_gain", disabled=disabled)

# --- Submit & Evaluate ---
if not disabled and st.button("🔍 Get Result"):
    required = [
        st.session_state.fda_approved,
        st.session_state.guideline_supported,
        st.session_state.stage,
        st.session_state.prior_treatment_failed,
        st.session_state.ecog
    ]
    if "-- Select --" in required:
        st.warning("⚠️ Please complete all selections before submitting.")
    else:
        score = 0
        debug = {}

        if st.session_state.fda_approved == "NO":
            result = "REJECTED"
        else:
            score += 20
            debug["FDA Approved"] = 20

            gs = 15 if st.session_state.guideline_supported == "YES" else 0
            score += gs
            debug["Guideline Supported"] = gs

            stg = 5 if int(st.session_state.stage) < 4 else 0
            score += stg
            debug["Stage"] = stg

            pt = 5 if st.session_state.prior_treatment_failed == "YES" else 0
            score += pt
            debug["Prior Treatment Failed"] = pt

            ag = 5 if st.session_state.age <= 75 else 0
            score += ag
            debug["Age"] = ag

            ecog_score = {"ECOG 0": 10, "ECOG 1": 10, "ECOG 2": 5,
                          "ECOG 3": 0}.get(st.session_state.ecog, 0)
            score += ecog_score
            debug["ECOG"] = ecog_score

            sg = 10 if st.session_state.survival_gain >= 6 else 0
            score += sg
            debug["Survival Gain"] = sg

            if st.session_state.cost <= 20000:
                cost_score = 30
            elif st.session_state.cost <= 30000:
                cost_score = 20
            elif st.session_state.cost <= 40000:
                cost_score = 10
            else:
                cost_score = 0
            score += cost_score
            debug["Cost"] = cost_score

            result = "APPROVED" if score >= 75 else "REJECTED"

        # --- Show Results ---
        st.subheader(f"Total Score: {score}")
        for k, v in debug.items():
            st.write(f"{k} Score: {v}")
        st.success(f"✅ Result: {result}" if result ==
                   "APPROVED" else f"❌ Result: {result}")

        # --- Record Dictionary ---
        record = {
            "Evaluation Date": st.session_state.evaluation_date,
            "Patient Name": st.session_state.name,
            "Insured Number": st.session_state.insured_no,
            "FDA Approved": st.session_state.fda_approved,
            "Guideline Supported": st.session_state.guideline_supported,
            "Stage": st.session_state.stage,
            "Prior Treatment Failed": st.session_state.prior_treatment_failed,
            "Age": st.session_state.age,
            "ECOG": st.session_state.ecog,
            "Cost of Protocol": st.session_state.cost,
            "Survival Gain": st.session_state.survival_gain,
            "Score": score,
            "Result": result
        }

        # --- Save to CSV ---
        file = "evaluations.csv"
        if os.path.exists(file):
            df = pd.read_csv(file)
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        else:
            df = pd.DataFrame([record])
       #tony df.to_csv(file, index=False)
        save_to_google_sheet(record)
        st.info("✅ Evaluation saved successfully to evaluations.csv")

        # --- PDF Export ---
        class PDF(FPDF):
            def header(self):
                self.image("BEST ASSISTANCE.JPG", 10, 8, 50)
                self.set_font("Arial", "B", 14)
                self.cell(200, 10, "Cancer Evaluation Report",
                          ln=True, align="C")
                self.ln(10)

        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", "", 12)
        for k, v in record.items():
            pdf.cell(0, 10, f"{k}: {v}", ln=True)

        pdf_bytes = pdf.output(dest="S").encode("latin-1")
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="Evaluation_{st.session_state.insured_no}.pdf">📄 Click here to download the PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

        st.session_state.submitted = True
