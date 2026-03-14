# 🏭 PredictMaint Pro — Industrial Predictive Maintenance System

A complete ML-powered predictive maintenance web system built with Flask and scikit-learn.

## 🌐 Live Demo
[Click here to open the app](https://pmapp.onrender.com)

## 👤 Login Credentials
| Username   | Password      | Role       |
|------------|---------------|------------|
| admin      | Admin@123     | Admin      |
| engineer1  | Engineer@123  | Engineer   |
| operator1  | Operator@123  | Operator   |
| manager1   | Manager@123   | Manager    |

## ✅ Features
- Machine failure prediction using Random Forest
- Anomaly detection using Isolation Forest
- Remaining Useful Life (RUL) prediction
- Real-time live simulation dashboard
- Smart maintenance planner with cost estimation
- PDF report download
- Role-based login system
- Analytics dashboard
- Explainable AI feature importance chart
- Web Audio alarm for critical machines

## 🤖 ML Models Used
| Model | Purpose |
|---|---|
| RandomForestClassifier | Failure prediction |
| IsolationForest | Anomaly detection |
| RandomForestRegressor | RUL prediction |
| StandardScaler | Feature normalization |

## 🏭 Machines Monitored
| ID | Machine | Zone |
|---|---|---|
| MCH-101 | CNC Milling Machine | Zone A |
| MCH-102 | Hydraulic Press | Zone B |
| MCH-103 | Conveyor Belt System | Zone A |
| MCH-104 | Industrial Compressor | Zone C |
| MCH-105 | Rotary Kiln | Zone C |
| MCH-106 | Turbine Generator | Zone B |

## 🚀 Run Locally
```bash
pip install -r requirements.txt
python app.py
```
Open → http://127.0.0.1:5000

## 🛠 Tech Stack
- Backend: Flask, SQLite, scikit-learn, pandas
- Frontend: HTML, CSS, Bootstrap, Chart.js
- Auth: Flask-Login, Werkzeug
- PDF: ReportLab
