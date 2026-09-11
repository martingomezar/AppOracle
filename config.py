# config.py
# Configuración general para el Bot de Trading con PPO en Bybit Testnet

BYBIT_API_KEY = "Ta4k6Wbd6GUkfTFe3Z"
BYBIT_API_SECRET = "PNbvhjR1elyyEv9iveWqv2Zp9GQ3HEcHduLm"

# Configuración del entorno de pruebas
USE_SANDBOX = True

# Top 15 monedas dinámicas en Spot
SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'PEPE/USDT', 
    'DOGE/USDT', 'AVAX/USDT', 'LINK/USDT', 'ADA/USDT', 'SUI/USDT', 
    'SHIB/USDT', 'NEAR/USDT', 'RENDER/USDT', 'FET/USDT', 'INJ/USDT'
]

# Aliases de compatibilidad y parámetros de operación y riesgo
MEMECOINS = SYMBOLS
TRADE_LOG_FILE = 'trades_log.csv'
TRADE_AMOUNT_USDT = 10.0
STOP_LOSS_PCT = 0.025
TAKE_PROFIT_PCT = 0.05
TRAILING_ACTIVATION = 0.015
TRAILING_STOP_PCT = 0.0075
TRAILING_DISTANCE = 0.0075  # Distancia de trailing stop requerida por el pipeline

# Parámetros del modelo y trading
TIMEFRAME = '1m'
MODEL_PATH = 'ppo_crypto_bot.zip'
HISTORICAL_DAYS = 30

# --- DISCORD ---
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1547720496479469578/IGJaA36bBJjHIhdNwZYl8-OV8PNa9ivZsPf0zvKbo3383oHdSSNIMeiqnpn0FOCAC9Lx"