"""
05_predictive_model.py
------------------------------------------------------------------
Predictive modelling layer: trains a baseline Logistic Regression and
a Random Forest classifier to predict `default_flag` from the
engineered risk features, compares them, and saves:

  - outputs/charts/model_roc_curve.png
  - outputs/charts/model_feature_importance.png
  - outputs/model_metrics.csv

This demonstrates the "Predictive Modeling" half of the project on
top of the descriptive KPI/SQL layer -- a lightweight, explainable
model appropriate for a credit-risk use case (stakeholders need to
see *why* a customer is flagged, not just the score).

Run:
    python scripts/05_predictive_model.py
------------------------------------------------------------------
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve, accuracy_score, precision_score, recall_score, f1_score

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "merged_risk_data.csv")
CHART_DIR = os.path.join(BASE_DIR, "outputs", "charts")
METRICS_PATH = os.path.join(BASE_DIR, "outputs", "model_metrics.csv")

FEATURES = [
    "age", "credit_score", "annual_income", "monthly_debt_payment",
    "debt_to_income", "loan_amount", "existing_loans_count",
    "claim_count", "total_claim_amount", "has_high_value_claim",
]
CATEGORICAL = ["employment_type", "region", "marital_status", "education_level"]
TARGET = "default_flag"

SEED = 42


def build_features(df):
    X = df[FEATURES + CATEGORICAL].copy()
    X = pd.get_dummies(X, columns=CATEGORICAL, drop_first=True)
    y = df[TARGET]
    return X, y


def evaluate(name, model, X_test, y_test, y_prob):
    return {
        "model": name,
        "accuracy": round(accuracy_score(y_test, model.predict(X_test)), 4),
        "precision": round(precision_score(y_test, model.predict(X_test)), 4),
        "recall": round(recall_score(y_test, model.predict(X_test)), 4),
        "f1_score": round(f1_score(y_test, model.predict(X_test)), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
    }


if __name__ == "__main__":
    df = pd.read_csv(DATA_PATH)
    X, y = build_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=SEED, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # class_weight="balanced" matters here: only ~16% of customers default,
    # so an unweighted model can hit high accuracy by mostly predicting
    # "no default" while missing the cases underwriting actually cares about.
    # Balancing trades a little accuracy for much better recall on defaults.

    # --- Logistic Regression (baseline, interpretable) ---
    log_reg = LogisticRegression(max_iter=1000, random_state=SEED, class_weight="balanced")
    log_reg.fit(X_train_scaled, y_train)
    log_prob = log_reg.predict_proba(X_test_scaled)[:, 1]

    # --- Random Forest (higher accuracy, feature importance) ---
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=8, random_state=SEED, n_jobs=-1, class_weight="balanced"
    )
    rf.fit(X_train, y_train)
    rf_prob = rf.predict_proba(X_test)[:, 1]

    results = [
        evaluate("Logistic Regression", log_reg, X_test_scaled, y_test, log_prob),
        evaluate("Random Forest", rf, X_test, y_test, rf_prob),
    ]
    metrics_df = pd.DataFrame(results)
    metrics_df.to_csv(METRICS_PATH, index=False)
    print(metrics_df.to_string(index=False))

    # --- ROC curve comparison ---
    fig, ax = plt.subplots(figsize=(7, 6))
    for name, prob in [("Logistic Regression", log_prob), ("Random Forest", rf_prob)]:
        fpr, tpr, _ = roc_curve(y_test, prob)
        auc = roc_auc_score(y_test, prob)
        ax.plot(fpr, tpr, label=f"{name} (AUC = {auc:.3f})", linewidth=2)
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey", label="Random baseline")
    ax.set_title("ROC Curve — Default Prediction Models", fontweight="bold")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "model_roc_curve.png"))
    plt.close()

    # --- Feature importance (Random Forest) ---
    importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False).head(12)
    fig, ax = plt.subplots(figsize=(8, 6))
    importances.sort_values().plot(kind="barh", ax=ax, color="#264653")
    ax.set_title("Top 12 Feature Importances — Random Forest", fontweight="bold")
    ax.set_xlabel("Relative Importance")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "model_feature_importance.png"))
    plt.close()

    print(f"\nSaved model_roc_curve.png, model_feature_importance.png -> {CHART_DIR}")
    print(f"Saved model metrics -> {METRICS_PATH}")
