{\rtf1\ansi\ansicpg1252\cocoartf2821
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 from flask import Flask, request, jsonify\
import yfinance as yf\
import pandas as pd\
from alpaca_trade_api.rest import REST\
import os\
\
app = Flask(__name__)\
\
def calculate_rsi(data, period=14):\
    delta = data.diff()\
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()\
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()\
    rs = gain / loss\
    return 100 - (100 / (1 + rs))\
\
@app.route('/run', methods=['POST'])\
def run_strategy():\
    data = request.get_json()\
    symbol = data.get('symbol', 'SPY')\
\
    key = os.getenv('ALPACA_KEY')\
    secret = os.getenv('ALPACA_SECRET')\
    paper = os.getenv('MODE', 'paper') == 'paper'\
\
    base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"\
    api = REST(key, secret, base_url)\
\
    candles = yf.download(symbol, period="7d", interval="15m")\
    rsi = calculate_rsi(candles['Close']).iloc[-1]\
\
    if rsi < 30:\
        api.submit_order(\
            symbol=symbol,\
            qty=1,\
            side='buy',\
            type='market',\
            time_in_force='gtc'\
        )\
        return jsonify(\{"status": "executed", "message": f"Buy executed on \{symbol\}. RSI: \{round(rsi, 2)\}"\})\
\
    return jsonify(\{"status": "no_trade", "message": f"No trade. RSI for \{symbol\} is \{round(rsi, 2)\}"\})\
\
app.run(host='0.0.0.0', port=8080)\
}