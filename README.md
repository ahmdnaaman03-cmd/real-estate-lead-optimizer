# Real Estate Lead Optimizer

A professional Streamlit web application designed for real estate professionals to clean, standardize, and optimize their lead data.

## Features
- **Dynamic Pay-Per-Row Paywall**: Integrated with Paymob for secure, dynamic pricing (0.05 EGP per row, min 50 EGP).
- **Phone Standardizer**: Automatically cleans and formats Egyptian mobile numbers.
- **VIP Lead Detector**: Identifies "Ultra" and "Premium" leads based on phone number patterns.
- **Smart De-duplication**: Removes duplicate leads based on phone numbers.
- **Location Standardizer**: Unifies chaotic area names into standard categories.
- **Secure Export**: Exports cleaned data to Excel-friendly CSV (utf-8-sig).

## Setup
1. Install dependencies: `pip install streamlit pandas requests openpyxl`
2. Run the app: `streamlit run app.py`
3. Configure Paymob API details in the sidebar.

Developed by Ahmed Saeed
