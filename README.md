# 🏦 AI-Driven Securities Settlement Engine (ISO 20022)

A high-fidelity synthetic data generator designed to simulate the US Securities Settlement lifecycle. This engine provides a "Ground Truth" data source for predictive failure modeling, liquidity forecasting, and anomaly detection.

## 🚀 Live Demo & API
- **Monitoring Dashboard:** `https://<your-username>.github.io/<repo-name>/index.html`
- **Real-Time JSON Feed:** `https://<your-username>.github.io/<repo-name>/data.json`
- **Analytical Training Set (CSV):** `https://<your-username>.github.io/<repo-name>/settlements.csv`

---

## 🧠 Data Calibration ("The Seed Engine")
This generator is grounded in actual regulatory data from 2025-2026, ensuring the statistical distributions are realistic:
* **SEC Fails-to-Deliver (FTD):** Calibrates ticker-specific historical failure probabilities.
* **DTCC Systemic Reports:** Establishes the 98.5% market efficiency baseline.
* **FINRA TRACE Volume:** Drives liquidity-based risk multipliers for Corporate Bonds.

---

## 🧪 Machine Learning Features
The engine generates 10,000 trades per hour with embedded "predictive signals" designed for ML model training:

| Feature | Data Field | ML Utility |
| :--- | :--- | :--- |
| **Counterparty Credit** | `InstructingParty_LEI` | Dynamic risk weight based on Legal Entity Identifier (LEI). |
| **Asset Liquidity** | `Asset_ISIN` | High-fidelity ticker stress scores from regulatory seeds. |
| **Trade Magnitude** | `SettlementAmount` | Log-normal distribution of trade sizes ($100k - $50M+). |
| **Temporal Stress** | `PreparationDateTime` | Exponential failure spike near the 16:00 UTC market cut-off. |
| **Market Volatility** | `Market_Volatility_Factor` | Real-time correlation with the live VIX Index. |

---

## 📋 ISO 20022 Compliance
The API outputs follow the **sese.024 (Settlement Status Advice)** messaging standard:
- **ACSC (AcceptedSettlementCompleted):** Successful trade finalization.
- **PENF (PendingFail):** Failure to settle on $T+n$.
- **Reason Codes:** Includes `INSU` (Insufficient Securities), `LATE` (Cut-off Missed), and `CASH` (Funding Gap).

---

## 🛠 Automation & Tech Stack
- **Python 3.10:** Logic engine using `NumPy` for stochastic risk modeling.
- **GitHub Actions:** Hourly automated generation and deployment.
- **yfinance API:** Real-time extraction of market volatility (VIX).
- **Tailwind CSS:** Professional "Command Center" monitoring dashboard.

---

### 📈 Business Value Simulation
This dataset allows for the calculation of:
1. **Capital at Risk:** Real-time monitoring of failed trade volume.
2. **Cost of Fails:** Calculation of overnight funding costs (e.g., 5% APR on failed par value).
3. **AI Efficacy:** Demonstrates a 60-70% reduction in fails through predictive flagging.

---
*Disclaimer: This is a synthetic data project developed for simulation and risk-modeling purposes. All trades and identifiers are generated for demonstration.*