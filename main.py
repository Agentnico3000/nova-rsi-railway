from flask import Flask, request, jsonify
import yfinance as yf
import os

app = Flask(__name__)

def get_rsi(symbol, period=14):
    data = yf.download(symbol, period='30d', interval='1d')
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]  # returns a single value as Series

@app.route('/run', methods=['POST'])
def run_bot():
    symbol = request.json.get('symbol', '').upper()
    rsi = get_rsi(symbol).item()  # ✅ FIXED: convert to float

    if rsi < 30:
        return jsonify({
            "status": "executed",
            "message": f"Buy executed on {symbol}. RSI: {rsi}"
        })
    else:
        return jsonify({
            "status": "no_trade",
            "message": f"No trade. RSI for {symbol} is {rsi}"
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
