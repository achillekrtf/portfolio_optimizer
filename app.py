from flask import Flask, request, jsonify, render_template
import pandas as pd
import yfinance as yf
import sqlite3
import riskfolio as rp
import numpy as np


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
        data = yf.download(assets, start=start_date, end=end_date)['Adj Close']
        if data.empty:
            return jsonify(error="No data downloaded. Check the stock symbols."), 400

        rf_data = yf.download("^IRX", period="1d")
        current_rf = rf_data["Adj Close"].iloc[0] / 100  # Convert to decimal (e.g., 0.02 for 2%)

        returns = data.pct_change().dropna()
        annual_returns = returns.resample('YE').apply(lambda x: (1 + x).prod() - 1)

        port = rp.Portfolio(returns=returns)
        port.assets_stats(method_mu='hist', method_cov='hist')

        model_type = request.form.get('dataInput')  # e.g., 'Sharpe' or 'MaxRet'
        risk_tolerance = float(request.form.get('riskTolerance', 0))


        method_mu = 'hist'  # Method to estimate expected returns based on historical data.
        method_cov = 'hist'  # Method to estimate covariance matrix based on historical data.

        port.assets_stats(method_mu=method_mu, method_cov=method_cov)
        weights = port.optimization(model='Classic', rm='MV', rf=0, obj=model_type, hist=True)

        labels = weights.index.tolist()
        sizes = weights.values.flatten().tolist()  # Convert to a 1D list

        portfolio_return = (returns * sizes).sum(axis=1).mean()  # Average daily return
        annualized_return = round((portfolio_return * 252),2)  # Annualized return

        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        portfolio_std_value = round(portfolio_std.item(),2)

        sharpe_ratio = (annualized_return - current_rf) / portfolio_std  # Risk-free rate adjusted Sharpe
        sharpe_ratio = round(sharpe_ratio[0][0],2)


        stock_labels = weights.index.tolist()
        sizes = weights.values.flatten().tolist()
        date_strings = data.index.strftime('%Y-%m-%d').tolist()
        price = data.dropna().T.values.tolist()

        correlation_matrix = annual_returns.corr()
        correlations = correlation_matrix.values.tolist()


        return render_template('graph.html', labels=stock_labels, sizes=sizes, correlations=correlations,
                               stock_labels=stock_labels, prices=price, date_strings=date_strings,
                               sharpe_ratio=sharpe_ratio, annualized_return=annualized_return,
                               portfolio_std=portfolio_std_value)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/submit', methods=['POST'])
def submit():
    data_value = request.form.get('dataInput')
    return render_template('graph.html')

if __name__ == '__main__':
    app.run(debug=True)
