from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///trades.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class TradeSignal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    signal = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Float, nullable=False)
    rsi = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    executed = db.Column(db.Boolean, default=False)

def get_signal(symbol):
    data = yf.download(symbol, period='5d', interval='15m', progress=False)
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    rsi = 100 - (100 / (1 + (gain.ewm(alpha=1/14).mean() / loss.ewm(alpha=1/14).mean())))
    current_rsi = round(rsi.iloc[-1], 2)
    current_price = round(data['Close'].iloc[-1], 2)
    signal = 'HOLD'
    if current_rsi < 32 and current_price > data['Close'].rolling(20).mean().iloc[-1]:
        signal = 'BUY'
    elif current_rsi > 70:
        signal = 'SELL'
    db.session.add(TradeSignal(symbol=symbol, signal=signal, price=current_price, rsi=current_rsi))
    db.session.commit()
    return {
        'symbol': symbol,
        'signal': signal,
        'price': current_price,
        'rsi': current_rsi,
        'timestamp': datetime.now(pytz.timezone('America/New_York')).isoformat()
    }

def auto_scanner():
    with app.app_context():
        while True:
            symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']
            with ThreadPoolExecutor() as executor:
                results = list(executor.map(get_signal, symbols))
            active_signals = [r for r in results if r['signal'] != 'HOLD']
            for signal in active_signals:
                print(f"SIGNAL: {signal}")
            time.sleep(900)

@app.route('/scan', methods=['POST'])
def scan():
    symbol = request.json.get('symbol', 'SPY').upper()
    signal = get_signal(symbol)
    return jsonify(signal)

@app.route('/recent-signals', methods=['GET'])
def get_signals():
    signals = TradeSignal.query.filter(
        TradeSignal.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).order_by(TradeSignal.timestamp.desc()).limit(50).all()
    return jsonify([{
        'id': s.id,
        'symbol': s.symbol,
        'signal': s.signal,
        'price': s.price,
        'rsi': s.rsi,
        'time': s.timestamp.isoformat()
    } for s in signals])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    if os.getenv('AUTO_SCAN', 'true').lower() == 'true':
        threading.Thread(target=auto_scanner, daemon=True).start()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)