from flask import Flask, request, jsonify, render_template
import pandas as pd
import yfinance as yf
import sqlite3
import riskfolio as rp

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect('stocks.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def input_form():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker, name FROM tickers")
    stocks = cursor.fetchall()
    conn.close()
    return render_template('input.html', stocks=stocks)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker, name FROM tickers WHERE name LIKE ? OR ticker LIKE ?",
                   ('%' + query + '%', '%' + query + '%'))
    results = cursor.fetchall()
    conn.close()

    stock_list = [{"label": f"{row['name']} ({row['ticker']})", "value": row['ticker']} for row in results]
    return jsonify(stock_list)


@app.route('/graph', methods=['POST'])
def generate_graph():
    assets = request.form.getlist('stocks')
    start_date = '2010-01-01'
    end_date = pd.Timestamp.today().strftime('%Y-%m-%d')

    try:
        # Download historical data
        data = yf.download(assets, start=start_date, end=end_date)['Adj Close']
        if data.empty:
            return jsonify(error="No data downloaded. Check the stock symbols."), 400

        # Calculate daily returns and annual returns
        returns = data.pct_change().dropna()
        annual_returns = returns.resample('Y').apply(lambda x: (1 + x).prod() - 1)

        # Calculate covariance and correlation matrices
        cov = annual_returns.cov()
        corr = annual_returns.corr()

        # Detect highly correlated pairs
        correlation_threshold = 0.8
        high_corr_pairs = []
        for i in range(len(corr.columns)):
            for j in range(i):
                if abs(corr.iloc[i, j]) > correlation_threshold:
                    high_corr_pairs.append((corr.columns[i], corr.columns[j], corr.iloc[i, j]))

        # Generate alert message
        warning_message = ""
        if high_corr_pairs:
            warning_message = "🔔 **Attention : Les stocks suivants ont une forte corrélation :** " + ", ".join(
                [f"{pair[0]} et {pair[1]} (corrélation : {pair[2]:.2f})" for pair in high_corr_pairs]
            )

        # Initialize and optimize portfolio
        port = rp.Portfolio(returns=annual_returns)
        port.assets_stats(method_mu='hist', method_cov='hist')
        weights = port.optimization(model='Classic', rm='MV', rf=0, obj='Sharpe', l=0, hist=True)

        labels = weights.index.tolist()
        sizes = weights.values.tolist()

        return render_template('graph.html', labels=labels, sizes=sizes, warning_message=warning_message)
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == '__main__':
    app.run(debug=True)
