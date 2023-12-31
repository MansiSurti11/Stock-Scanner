from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import requests
import os


app = Flask(__name__, template_folder='template')

# Use an environment variable for the database URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///stocks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    company = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

# Replace 'YOUR_API_KEY' with your Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = 'G57FEEKQBAEWOAH7'
BASE_URL = 'https://www.alphavantage.co/query'

def get_stock_data(symbol):
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': '1min',
        'apikey': ALPHA_VANTAGE_API_KEY
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    # Extracting the latest stock quote
    latest_quote = next(iter(data.get('Time Series (1min)', {}).values()), None)

    return latest_quote

def filter_stocks(min_price=None, max_price=None, min_volume=None):
    query = Stock.query

    if min_price is not None:
        query = query.filter(Stock.price >= min_price)

    if max_price is not None:
        query = query.filter(Stock.price <= max_price)

    if min_volume is not None:
        query = query.filter(Stock.volume >= min_volume)

    return query.all()

@app.route('/')
def index():
    return render_template('index_db.html')

@app.route('/update_stocks', methods=['POST'])
def update_stocks():
    stocks = [
        {"symbol": "AAPL", "company": "Apple Inc."},
        {"symbol": "GOOGL", "company": "Alphabet Inc."},
        # Add more stocks as needed
    ]

    for stock in stocks:
        symbol = stock['symbol']
        company = stock['company']
        stock_data = get_stock_data(symbol)

        if stock_data:
            price = float(stock_data['1. open'])
            volume = int(stock_data['5. volume'])

            existing_stock = Stock.query.filter_by(symbol=symbol).first()

            if existing_stock:
                existing_stock.price = price
                existing_stock.volume = volume
            else:
                new_stock = Stock(symbol=symbol, company=company, price=price, volume=volume)
                db.session.add(new_stock)

    db.session.commit()

    return render_template('index_db.html', stocks=Stock.query.all())

@app.route('/filter_stocks', methods=['POST'])
def filter_stocks_route():
    min_price = request.form.get('min_price')
    max_price = request.form.get('max_price')
    min_volume = request.form.get('min_volume')

    stocks = filter_stocks(min_price=min_price, max_price=max_price, min_volume=min_volume)
    return render_template('index_custom_filters.html', stocks=stocks)

if __name__ == '__main__':
    # Use PORT environment variable if available (Heroku deployment)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
