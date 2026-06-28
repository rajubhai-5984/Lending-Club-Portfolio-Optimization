# AI-Based Lending Club Portfolio Optimization

An end-to-end Machine Learning project that predicts loan profitability and constructs an optimized investment portfolio using historical Lending Club loan data. The project combines predictive modeling with portfolio optimization techniques to maximize risk-adjusted returns.

## Features

- Predicts loan returns and investment risk using machine learning.
- Performs data preprocessing and feature engineering on financial datasets.
- Extracts textual information from loan descriptions using TF-IDF.
- Uses K-Means clustering to estimate loan covariance for portfolio diversification.
- Optimizes portfolio allocation using Sharpe Ratio optimization.
- Compares optimized portfolios against baseline investment strategies.

## Tech Stack

- Python
- Pandas
- NumPy
- Scikit-learn
- SQLite
- TF-IDF Vectorization
- K-Means Clustering

## Project Structure

```
.
├── data/
├── models/
├── notebooks/
├── scripts/
├── results/
├── requirements.txt
└── README.md
```

*(Folder names may vary depending on your repository structure.)*

## Methodology

1. Collect and preprocess historical Lending Club loan data.
2. Perform feature engineering on numerical and textual attributes.
3. Train machine learning models to estimate expected loan returns.
4. Apply K-Means clustering to estimate covariance among loans.
5. Optimize investment allocation using the Sharpe Ratio.
6. Evaluate portfolio performance against baseline strategies.

## Results

- Improved risk-adjusted portfolio performance through optimization.
- Generated diversified investment portfolios using clustering techniques.
- Automated the end-to-end workflow from preprocessing to portfolio evaluation.

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/Lending-Club-Portfolio-Optimization.git
```

Navigate to the project directory:

```bash
cd Lending-Club-Portfolio-Optimization
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the training and portfolio optimization pipeline:

```bash
python main.py
```

*(Replace `main.py` with your project's entry file if different.)*

## Future Improvements

- Incorporate advanced ensemble models such as XGBoost or LightGBM.
- Develop a web dashboard for portfolio visualization.
- Integrate real-time loan data for continuous portfolio optimization.
- Experiment with deep learning approaches for return prediction.

## Author

**Rajan Kumar**

GitHub: https://github.com/rajubhai-5984
