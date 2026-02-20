# 🏦 Settlement Risk Engine data source (T+1 Compliance Edition)

![Status](https://img.shields.io/badge/Status-Live_Simulation-success)
![Regulation](https://img.shields.io/badge/Regulation-T%2B1_Ready-blue)

---

## ⚙️ The Synthetic Data Engine

Because real settlement data is highly sensitive (MNPI), we engineered a **Digital Twin** of the US Post-Trade Ecosystem. This is not random data; it is a calibrated simulation.

### How It Works
1.  **🌱 Calibration (The "Seeds"):** We ingest real-world 2025 regulatory data:
    * **SEC Fails-to-Deliver Data:** To identify inherently risky equities.
    * **FINRA TRACE Reports:** To model realistic bond market liquidity gaps.
    * **DTCC/SIFMA Benchmarks:** To set the systemic baseline efficiency (~96.7%).
2.  **🌪️ Generation (The "Storm"):** We simulate a 5-day trading week with dynamic market stress (VIX) and operational "rush hours" (3 PM cut-offs).
3.  **💎 Enrichment (The "Value"):** We augment standard ISO 20022 messages with internal risk signals (Credit Scores, Liquidity Metrics).

### Key Features
* **Dynamic "Live" Dates:** The engine automatically detects the current date, simulating a live trading week relative to *today*.
* **T+1 Compliance:** All trades respect the T+1 settlement cycle logic.
* **Hourly Batching:** Data is structured to simulate realistic hourly processing windows.

---

## 📊 Data Dictionary (16 Fields)

Our dataset follows a **Hybrid Architecture**, combining strict banking standards with advanced ML features.

### A. The ISO 20022 Core (The "Wire")
*Strict adherence to the `sese.024` (Status Advice) XML standard.*

| Field Name | ISO XML Tag | Description |
| :--- | :--- | :--- |
| **`UETR`** | `<UETR>` | Unique End-to-End Transaction Reference (UUID). |
| **`PreparationDateTime`** | `<CreDtTm>` | Timestamp of instruction (ISO 8601). |
| **`SettlementDate`** | `<SttlmDt>` | The contractual T+1 settlement date. |
| **`Asset_ISIN`** | `<FinInstrmId>` | International Securities Identification Number. |
| **`Direction`** | `<SctiesMvmntTp>` | `DELI` (Sell/Deliver) or `RECE` (Buy/Receive). |
| **`SettlementAmount`** | `<SttlmAmt>` | Cash value of the trade in USD. |
| **`Counterparty`** | `<Pty><Nm>` | Legal Entity Name (e.g., JPM_CHASE_NA). |
| **`Status`** | `<PrcgSts>` | Current State: `ACSC` (Success) or `PENF` (Fail). |
| **`ISO_ReasonCode`** | `<Rsn><Cd>` | Root Cause: `INSU` (Inventory), `CASH` (Credit), `LATE` (Time). |

### B. The Risk Enrichment (The "Brain")
*Internal proprietary signals added to power the AI models.*

| Field Name | Description | Value for ML |
| :--- | :--- | :--- |
| **`Counterparty_Credit_Score`** | Internal FICO-like score (300-850). | Primary predictor for `CASH` failures. |
| **`Asset_Liquidity_Score`** | Normalized metric (0.0 - 1.0). | Primary predictor for `INSU` failures (Bond vs Equity). |
| **`Asset_Class`** | Derived Category (Equity/Bond). | Segmentation for risk weighting. |
| **`Time_of_Day_Flag`** | `Market_Hours` vs `Near_Cutoff`. | Identifies operational bottleneck risks. |
| **`Market_Volatility_Factor`** | Systemic Stress Index (VIX derived). | Detects market-wide crash scenarios. |
| **`Counterparty_Hist_Fail_Rate`** | Historical performance metric. | Biases prediction based on past behavior. |

---

## 🖥️ Dashboard

The project includes an interactive **Live Dashboard** (`index.html`) to visualize the simulation.

### Features
* **Interactive Time Machine:** Use the "Advance 1 Hour" button to step through the trading day and watch risks evolve.
* **Auto-Play Mode:** Simulates a full day of trading in 30 seconds.
* **Real-Time Alerts:**
    * 🔴 **Red Badges:** High Failure Probability.
    * 🟣 **Purple Bars:** Illiquid Asset Warnings.
    * ⏰ **Late Flags:** Trades executed near the T+1 cut-off.
### Output
* **JSON API** (`data.json`)
* **ML Training Set** (`settlements.csv`)

---

## 🏆 Hackathon Value Proposition

Defensible Data: We don't guess. Our failure rates are calibrated to the DTCC/SIFMA September 2024 Report (96.69% Efficiency).

Model-Ready: The data is pre-cleaned, chronologically sorted, and feature-engineered for immediate XGBoost/LSTM training.

Business Logic: We demonstrate a deep understanding of Credit Risk, Liquidity Management, and T+1 Regulations.

---
Built for the DTCC AI Hackathon 2026