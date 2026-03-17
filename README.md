<img width="1040" height="1162" alt="image" src="https://github.com/user-attachments/assets/ab1759b9-0245-404e-9008-6623f1295ec1" />

### NOTE: This is a current work-in-progess. Finalized version delivered in upcoming weeks.
# Sports Betting Decision Support Dashboard
A machine learning–driven sports betting analytics dashboard that integrates predictive modeling with sportsbook odds to identify value bets and optimize betting strategy through expected value analysis and bankroll management.

The system combines model-generated win probabilities with market odds to highlight profitable opportunities and simulate betting strategies using the Kelly Criterion. The results are presented through an interactive Flask dashboard designed for decision-support analysis.

---

# Project Overview

Sports betting markets contain inefficiencies where model predictions may disagree with sportsbook implied probabilities. This project builds a **decision-support system** that identifies these opportunities using machine learning and quantitative risk management techniques.

The system performs the following tasks:

* Predict game outcomes using an XGBoost machine learning model
* Retrieve sportsbook odds data
* Convert odds to implied probabilities
* Compare model predictions with market probabilities
* Calculate expected value (EV) of each bet
* Determine optimal bet size using the Kelly Criterion
* Simulate bankroll growth and risk exposure
* Display results in a real-time dashboard

The goal is not simply predicting winners, but identifying **positive expected value betting opportunities**.

---

# System Architecture

The project follows a modular machine learning pipeline.

```
Game Data + Sportsbook Odds
        ↓
Feature Engineering
        ↓
XGBoost Prediction Model
        ↓
Win Probability Estimates
        ↓
Expected Value Calculation
        ↓
Kelly Criterion Bet Sizing
        ↓
Bankroll Simulation
        ↓
Flask Decision Dashboard
```

---

# Dashboard Features

The dashboard provides a decision-support interface with the following analytics:

### Model Predictions

Displays predicted win probabilities for each team.

### Sportsbook Odds

Shows market odds and implied probabilities.

### Expected Value Analysis

Identifies value bets where model probabilities exceed market probabilities.

### Kelly Criterion Bet Sizing

Calculates optimal bet size based on bankroll and edge.

### Bankroll Simulation

Simulates bankroll growth under different betting strategies.

### Risk Metrics

Displays volatility and risk exposure.

---

# Project Structure

```
sports-betting-decision-dashboard
│
├ Data
│   Historical game data and processed datasets
│
├ Models
│   Trained machine learning models
│
├ src
│   Core machine learning pipeline
│   ├ DataProviders
│   ├ Predict
│   └ Utils
│
├ Flask
│   Dashboard application
│   ├ app.py
│   ├ templates
│   └ static
│
├ main.py
│   Model prediction pipeline
│
├ config.toml
│   Configuration settings
│
├ requirements.txt
│   Python dependencies
│
└ README.md
```

---

# Installation

Clone the repository:

```
git clone https://github.com/YOUR_USERNAME/sports-betting-decision-dashboard.git
cd sports-betting-decision-dashboard
```

Install required packages:

```
pip install -r requirements.txt
```

If installation fails due to TensorFlow compatibility with Python 3.12, install dependencies manually:

```
pip install flask pandas numpy scikit-learn xgboost matplotlib requests tqdm
```

---

# Running the Model Pipeline

You can run the prediction pipeline directly from the command line.

```
python main.py -xgb -odds=fanduel -kc
```

Arguments:

| Argument        | Description                      |
| --------------- | -------------------------------- |
| `-xgb`          | Use the XGBoost model            |
| `-odds=fanduel` | Retrieve FanDuel sportsbook odds |
| `-kc`           | Apply Kelly Criterion bet sizing |

This command generates predictions and calculates expected value for upcoming games.

---

# Launching the Dashboard

Navigate to the Flask application directory:

```
cd Flask
```

Start the dashboard server:

```
python app.py
```

The server will launch locally.

Open your browser and navigate to:

```
http://127.0.0.1:5000
```

---

# Dashboard Preview

*(Insert screenshot here)*

Example dashboard output includes:

* predicted win probabilities
* sportsbook odds comparison
* expected value analysis
* Kelly bet sizing recommendations
* bankroll simulation

---

# Technologies Used

Machine Learning

* XGBoost
* Scikit-learn

Data Processing

* Pandas
* NumPy

Backend

* Python

Dashboard

* Flask
* HTML / CSS

Visualization

* Matplotlib

---

# Key Concepts Implemented

### Expected Value (EV)

Expected value identifies profitable betting opportunities.

```
EV = (Pwin × Profit) − (Plose × Stake)
```

A bet is considered positive expected value if EV > 0.

---

### Kelly Criterion

The Kelly Criterion determines optimal bet sizing based on edge and odds.

```
f* = (bp − q) / b
```

Where:

* **b** = odds multiplier
* **p** = probability of winning
* **q** = probability of losing

This helps maximize long-term bankroll growth while controlling risk.

---

# Use Cases

This system can be used for:

* sports betting strategy research
* model evaluation against betting markets
* decision-support analytics
* educational demonstrations of expected value betting

---


# Future Improvements

Potential extensions include:

* real-time odds API integration
* additional machine learning models
* Monte Carlo bankroll simulations
* portfolio-style bet optimization
* automated daily predictions
* advanced risk metrics

---

# Author

Ben Tartaglia

Penn State University

Applied Data Science & Economics

<img width="2048" height="1795" alt="image" src="https://github.com/user-attachments/assets/7a20cbf9-0100-41ab-946e-51d05212113e" />

