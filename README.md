## Monthly Billing Statement Dashboard

A professional dashboard for monthly billing statements with filters, KPIs, detailed tables, and charts.

### Run locally
1. (Optional) Create and activate a virtual environment
   - Python 3.10+
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app
   ```bash
   streamlit run app.py
   ```

Open the displayed URL in your browser.

### CSV schema (if you upload your own data)
Required columns (case-sensitive):
- `statement_date` (YYYY-MM-DD)
- `bank_name`
- `bank_specific_name`
- `product_line`
- `unit_price` (numeric)
- `volume` (numeric)
- `currency` (e.g., USD, EUR)
- `unit_of_measure` (e.g., transactions, items)

Optional columns:
- `fee_type` (e.g., Fixed, Variable)
- `region`

### Notes
- If you don't upload a CSV, the app generates realistic sample data for the selected month.
- All tables are downloadable as CSV.
