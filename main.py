from flask import Flask, request, jsonify
import yfinance as yf
import os

app = Flask(__name__)

def get_rsi(symbol, period=14):
    data = yf.download(symbol, period='30d', interval='1d')
    if data.empty:
        raise ValueError("No data returned from yfinance.")
        
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))

    if rsi_series.empty:
        raise ValueError("RSI calculation failed.")

    return rsi_series.iloc[-1]

@app.route('/run', methods=['POST'])
def run_bot():
    symbol = request.json.get('symbol', '').upper()

    try:
        rsi_value = get_rsi(symbol)

        if rsi_value < 30:
            return jsonify({
                "status": "executed",
                "message": f"Buy executed on {symbol}. RSI: {round(rsi_value, 2)}"
            })
        else:
            return jsonify({
                "status": "no_trade",
                "message": f"No trade. RSI for {symbol} is {round(rsi_value, 2)}"
            })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
