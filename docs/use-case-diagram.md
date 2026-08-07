# Use Case Diagram

```mermaid
flowchart LR
    User(["🧑 User"])

    subgraph System["SiloScope"]
        UC1(["Run Stock Forecast"])
        UC2(["Run Crypto Forecast"])
        UC3(["Compare Two Tickers"])
        UC4(["Track Live Intraday Forecast"])
        UC5(["View Model Formulas & Explanations"])
        UC6(["View Track Record"])
        UC7(["View Analyst Consensus"])
    end

    User --- UC1
    User --- UC2
    User --- UC3
    User --- UC4
    User --- UC5
    User --- UC6

    UC3 -.->|includes| UC7
    UC1 -.->|includes| UC6
    UC2 -.->|includes| UC6
```

- **Run Stock / Crypto Forecast** -- pick a ticker, run all 10 models + the ensemble, see which
  has actually been most accurate for it. Each includes a per-ticker glimpse of Track Record.
- **Compare Two Tickers** -- run two forecasts side by side; includes Analyst Consensus (Yahoo
  Finance analyst targets) when available for that ticker.
- **Track Live Intraday Forecast** -- predicts today's close from the return so far.
- **View Model Formulas & Explanations** -- the home page's formula showcase for all 10 models.
- **View Track Record** -- rolling accuracy per model and the ensemble-vs-naive-baseline
  significance test, across the app's full prediction history.
