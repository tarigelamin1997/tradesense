# TradeSense

> 🚨 This project follows strict contributor and architecture rules.  
> Breaking structure or deleting core files without approval is not allowed.  
> → See [`project-rules.md`](./project-rules.md)



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
pip install -r requirements.txt  # install pinned versions
```
Dependencies are pinned in `requirements.txt` to ensure reproducible installations.
Interactive tables are powered by `streamlit-aggrid` pinned at version 1.1.5.
Python 3.11 or 3.12 is recommended. Installing with Python 3.13 may fail because pre-built wheels for some packages (e.g. pandas) are not yet available.
## Testing

First create a virtual environment and install the required packages:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run `pip install -r requirements.txt` before executing `pytest` to ensure all
dependencies are available. Then run the test suite:

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

[MIT](LICENSE)

