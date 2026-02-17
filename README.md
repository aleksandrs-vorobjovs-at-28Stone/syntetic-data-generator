# 🏦 SettlementCore AI: High-Fidelity Risk Engine (ISO 20022)

A professional-grade synthetic data generator simulating the US Securities Settlement lifecycle. This engine provides a "Ground Truth" data source for predictive failure modeling, liquidity forecasting, and multi-asset class anomaly detection.

## 🚀 Live Demo & API
- **Monitoring Dashboard:** `https://<your-username>.github.io/<repo-name>/index.html`
- **Real-Time JSON Feed:** `https://<your-username>.github.io/<repo-name>/data.json`
- **Analytical Training Set (CSV):** `https://<your-username>.github.io/<repo-name>/settlements.csv`

---

## 🧠 Data Calibration (Version 2.0 "Enriched")
The engine is grounded in a deep-sector calibration layer using actual 2025 regulatory data. The "Seed Engine" maintains a universe of **25,000+ unique assets**:

* **Equities (17,500+):** Derived from SEC Fails-to-Deliver (FTD) data to model operational "noise."
* **Corporate Bonds & Fixed Income (7,400+):** Programmatically expanded from FINRA TRACE reports to model inventory scarcity and liquidity tiers.
* **DTCC Systemic Benchmarks:** Calibrated via PDF extraction to maintain a ~74% baseline systemic efficiency.



---

## 🧪 Advanced Risk Modeling Logic
The engine generates 10,000 instructions per hour using a **70/30 Asset Mix**, ensuring high visibility for complex Fixed Income fails.

| Feature | Data Field | ML Utility |
| :--- | :--- | :--- |
| **Instruction Side** | `Direction` | `DELI` (Sell) vs `RECE` (Buy). Essential for inventory-specific risk. |
| **Asset Category** | `Asset_Class` | Distinct logic for `Equity`, `Corporate Bond`, and `Fixed Income`. |
| **Trade Size Risk** | `SettlementAmount` | Asset-aware amounts (Bonds/FI average higher ticket sizes). |
| **Temporal Stress** | `PreparationDateTime` | Models "Cut-off Risk" with failure spikes near 16:00 UTC. |
| **Systemic Volatility** | `Market_Volatility_Factor`| Real-time correlation with live **VIX Index** + stochastic jitter. |

---

## 📋 ISO 20022 Data Structure
The API outputs follow the **sese.024 (Settlement Status Advice)** standard, enriched with instructional metadata:

| Field Name | Description | Importance for Risk Modeling |
| :--- | :--- | :--- |
| **Asset_Class** | Equity / Corp Bond / Fixed Income | **Liquidity/Complexity:** Each class follows unique risk parameters. |
| **Direction** | DELI / RECE | **Inventory Risk:** Distinguishes between internal stock lack vs. counterparty failure. |
| **Status** | ACSC / PENF | **Ground Truth:** Primary labels for supervised ML classification. |
| **Reason Code** | INSU / LATE / CASH / CLOS | **Causal Inference:** `INSU` (Securities Lack), `CASH` (Funding Gap). |



---

## 🛠 Automation & Tech Stack
* **Python 3.10:** Optimized for stochastic risk modeling and large JSON metadata processing.
* **Pandas & NumPy:** For asset-class-specific log-normal trade distributions.
* **GitHub Actions:** Automated hourly generation, calibration, and dashboard deployment.
* **yfinance:** Live API bridge for dynamic market stress (VIX) calculation.
* **Tailwind CSS:** Professional-grade "Command Center" UI with real-time sync.

---

### 📈 Business Value Simulation
This dataset allows for the simulation of:
1.  **Capital at Risk (CaR):** Quantifying the total dollar value of predicted failures across asset classes.
2.  **Liquidity Optimization:** Identifying "Funding Gaps" where `RECE` instructions fail due to `CASH` issues.
3.  **Regulatory Reporting:** Automating CSDR (Settlement Discipline Regime) penalty estimations for Bond fails.

---
*Disclaimer: This is a synthetic data project developed for simulation and risk-modeling purposes. All identifiers and trade records are programmatically generated.*