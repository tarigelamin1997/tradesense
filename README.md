# TradeSense

**Smarter Decisions. Safer Trades.**

TradeSense is a modular trading analytics and risk management app built with Streamlit. Upload your trading history, analyze performance, and manage risk with actionable insights.

## Features

- Upload CSV/Excel trade history from any broker. Both file paths and file-like uploads are supported.
- Map custom column names to required fields.
- Universal trade model works across asset classes.
- Core analytics: win rate, expectancy, drawdown, Sharpe ratio, and more.
- Interactive dashboards with Plotly charts.
- Risk assessment and position sizing recommendations.
- Sample futures data included for quick start.
- Placeholders for Stripe/PayPal integration.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
## Testing

First create a virtual environment and install the required packages:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run the test suite:

```bash
pytest
```


## Running the App

```bash
streamlit run app.py
```

Upload your trade history or simply run the app without a file to see the built‑in
sample data from `sample_data/futures_sample.csv`.

## Extending

- Add new importers in `data_import/` for forex, options, stocks, etc.
- Integrate payment systems via `payment.py`.
- Customize branding in `app.py` and assets.

## License

MIT

