import json
import io
import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from utils import load_brackets, load_expenses, summarize_expenses, STANDARD_DEDUCTION_2024
from tax_optimizer import estimate_tax, recommend_deductions

st.set_page_config(page_title="TaxLens — AI Tax Optimization", page_icon="💰", layout="wide")
st.title("💰 TaxLens — AI Tax Optimization Assistant")
st.caption("Educational demo — simplified U.S. federal logic. This is not tax advice.")

with st.sidebar:
    st.header("⚙️ Settings")
    filing_status = st.selectbox("Filing Status", ["Single", "Married Filing Jointly", "Head of Household"])
    force_itemize = st.checkbox("Force Itemized Deductions", value=False)
    st.markdown(f"**Standard Deduction (2024):** ${STANDARD_DEDUCTION_2024.get(filing_status,0):,.0f}")
    st.markdown("Upload CSV with columns: **Type, Category, Amount**. Type ∈ {Income, Expense}.")

uploaded = st.file_uploader("📂 Upload Income/Expense CSV", type=["csv"])
use_sample = st.checkbox("Use sample_data.csv")

if not uploaded and not use_sample:
    st.info("Upload a CSV or check 'Use sample_data.csv' to begin.")
    st.stop()

if use_sample:
    data_file = "sample_data.csv"
else:
    data_file = uploaded

try:
    df = load_expenses(data_file)
except Exception as e:
    st.error(f"Could not read data: {e}")
    st.stop()

# Summaries
summary = summarize_expenses(df)
total_income = summary["total_income"]
total_expenses = summary["total_expenses"]

colA, colB, colC = st.columns(3)
colA.metric("Total Income", f"${total_income:,.2f}")
colB.metric("Total Expenses", f"${total_expenses:,.2f}")
colC.metric("Net (Income - Expenses)", f"${(total_income - total_expenses):,.2f}")

# Itemized proxy input (optional)
with st.expander("Optional: Enter Itemized Deductions Total (demo)"):
    itemized_total = st.number_input("Itemized Deductions Total ($)", min_value=0.0, step=100.0)

# Load brackets & estimate tax
brackets = load_brackets("tax_brackets_2024.json")[filing_status]
result = estimate_tax(
    filing_status=filing_status,
    total_income=total_income,
    total_expenses=total_expenses,
    brackets=brackets,
    force_itemize=force_itemize,
    itemized_total=itemized_total if itemized_total else None
)

st.subheader("💵 Tax Summary (Simplified)")
st.json(result)

# Recommendations
st.subheader("💡 Suggestions")
for tip in recommend_deductions(df):
    st.success(tip)

# Chart: expenses by category
st.subheader("📊 Expenses by Category")
by_cat = summary["by_category"]
if not by_cat.empty:
    fig = plt.figure()
    plt.bar(by_cat["Category"], by_cat["Amount"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Amount ($)")
    plt.title("Expenses by Category")
    st.pyplot(fig)
else:
    st.write("No expense rows in the dataset.")

# Export CSV summary
export_df = by_cat.copy()
export_df.columns = ["Category", "Total_Amount"]
export_df["Filing_Status"] = filing_status
export_df["Standard_Deduction_2024"] = STANDARD_DEDUCTION_2024.get(filing_status, 0)
export_df["Taxable_Income"] = result["Taxable Income"]
export_df["Estimated_Federal_Tax"] = result["Estimated Federal Tax"]

st.subheader("📥 Download")
st.download_button(
    "Download Category Summary (CSV)",
    data=export_df.to_csv(index=False).encode("utf-8"),
    file_name="TaxLens_CategorySummary.csv",
    mime="text/csv"
)

# Create simple PDF report
def build_pdf(summary_json: dict, file_like):
    c = canvas.Canvas(file_like, pagesize=letter)
    width, height = letter
    y = height - 60
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, y, "TaxLens — Summary Report (Educational)")
    y -= 25
    c.setFont("Helvetica", 11)
    c.drawString(60, y, f"Date: {datetime.date.today().isoformat()}")
    y -= 20
    for k, v in summary_json.items():
        line = f"{k}: {v}"
        c.drawString(60, y, line)
        y -= 16
        if y < 100:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 11)
    c.showPage()
    c.save()

pdf_buffer = io.BytesIO()
build_pdf(result, pdf_buffer)
st.download_button(
    "Download PDF Summary",
    data=pdf_buffer.getvalue(),
    file_name="TaxLens_Summary.pdf",
    mime="application/pdf"
)

st.caption("Note: This educational tool simplifies federal tax rules and may not reflect your actual liability.")
