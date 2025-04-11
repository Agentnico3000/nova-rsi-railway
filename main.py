from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import os

app = Flask(__name__)

@app.route('/scan', methods=['POST'])
def scan():
    try:
        symbol = request.json.get('symbol', 'SPY').upper()
        data = yf.download(symbol, period='5d', interval='15m', progress=False)
        if data.empty:
            return jsonify({'error': 'No data'}), 400

        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        rsi = 100 - (100 / (1 + (gain.ewm(alpha=1/14).mean() / loss.ewm(alpha=1/14).mean())))

        current_rsi = round(rsi.iloc[-1], 2)
        price = round(data['Close'].iloc[-1], 2)
        signal = 'HOLD'
        if current_rsi < 30:
            signal = 'BUY'
        elif current_rsi > 70:
            signal = 'SELL'

        return jsonify({
            'symbol': symbol,
            'price': price,
            'rsi': current_rsi,
            'signal': signal,
            'timestamp': datetime.now(pytz.timezone('America/New_York')).isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'online'})

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
