import pandas as pd
from utils import marginal_tax, STANDARD_DEDUCTION_2024

DEDUCTION_HINTS = {
    "Home Office": "Home office costs may be deductible if used regularly and exclusively for business.",
    "Vehicle": "Consider standard mileage vs. actual expenses; track business miles.",
    "Charity": "Charitable donations may be itemized; keep receipts from qualified orgs.",
    "Education": "Some education expenses may qualify for Lifetime Learning Credit (limits apply).",
    "Health": "HSA contributions can be tax-advantaged if eligible.",
    "Retirement": "IRA/401(k) contributions may reduce taxable income (limits apply).",
    "Supplies": "Ordinary & necessary business supplies are generally deductible.",
    "Utilities": "Portions used for business could be deductible depending on context."
}

def recommend_deductions(df: pd.DataFrame) -> list[str]:
    cats = set(df[df["Type"] == "Expense"]["Category"].unique())
    recs = []
    for k, v in DEDUCTION_HINTS.items():
        if k in cats:
            recs.append(f"• {k}: {v}")
    if "Retirement" not in cats:
        recs.append("• Retirement: Consider starting/boosting IRA/401(k) contributions.")
    if "Health" not in cats:
        recs.append("• Health: Consider HSA contributions if eligible.")
    if not recs:
        recs.append("• Track itemizable categories (Charity, Medical, Taxes) to compare vs. standard deduction.")
    return recs

def estimate_tax(
    filing_status: str,
    total_income: float,
    total_expenses: float,
    brackets: list[list],
    force_itemize: bool = False,
    itemized_total: float | None = None
):
    """
    Compute taxable income under standard vs itemized (basic demo logic).
    """
    standard = STANDARD_DEDUCTION_2024.get(filing_status, 0.0)
    # Itemized = either provided or a basic proxy (allow only some categories)
    allowed_itemized = float(itemized_total) if itemized_total is not None else 0.0

    # Choose path
    if force_itemize:
        deduction_used = allowed_itemized
        deduction_type = "Itemized"
    else:
        if allowed_itemized > standard:
            deduction_used = allowed_itemized
            deduction_type = "Itemized"
        else:
            deduction_used = standard
            deduction_type = "Standard"

    agi = max(0.0, total_income)  # simplified for demo
    taxable_income = max(0.0, agi - deduction_used - total_expenses)

    est_federal = marginal_tax(taxable_income, brackets)

    return {
        "AGI (simplified)": round(agi, 2),
        "Deduction Used": round(deduction_used, 2),
        "Deduction Type": deduction_type,
        "Taxable Income": round(taxable_income, 2),
        "Estimated Federal Tax": round(est_federal, 2)
    }
