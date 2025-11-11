import json
import pandas as pd

REQUIRED_COLS = ["Type", "Category", "Amount"]

STANDARD_DEDUCTION_2024 = {
    "Single": 14600,
    "Married Filing Jointly": 29200,
    "Head of Household": 21900
}

def load_brackets(path: str):
    with open(path, "r") as f:
        return json.load(f)

def marginal_tax(income: float, brackets: list[list]) -> float:
    """
    Compute federal tax using progressive brackets [[low, high, rate], ...].
    'high' may be None for the top bracket.
    """
    if income <= 0:
        return 0.0
    tax = 0.0
    remaining = income
    for low, high, rate in brackets:
        upper = float("inf") if high is None else high
        if remaining <= 0:
            break
        span_low = max(0.0, low)
        span_high = upper
        if income > span_low:
            taxable_here = min(income, span_high) - span_low
            if taxable_here > 0:
                tax += taxable_here * rate
    return max(0.0, tax)

def load_expenses(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}. Required: {REQUIRED_COLS}")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df = df.dropna(subset=["Amount"])
    return df

def summarize_expenses(df: pd.DataFrame) -> dict:
    by_cat = df[df["Type"] == "Expense"].groupby("Category", as_index=False)["Amount"].sum()
    by_cat = by_cat.sort_values("Amount", ascending=False)
    total_income = df[df["Type"] == "Income"]["Amount"].sum()
    total_exp = df[df["Type"] == "Expense"]["Amount"].sum()
    return {
        "by_category": by_cat,
        "total_income": float(total_income),
        "total_expenses": float(total_exp)
    }
