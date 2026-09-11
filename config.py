# config.py
# Configuración general para el Bot de Trading con PPO en Bybit Testnet

BYBIT_API_KEY = "tu_api_key_de_bybit"
BYBIT_API_SECRET = "tu_api_secret_de_bybit"

# Configuración del entorno de pruebas
USE_SANDBOX = True

# Top 15 monedas dinámicas en Spot
SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'PEPE/USDT', 
    'DOGE/USDT', 'AVAX/USDT', 'LINK/USDT', 'ADA/USDT', 'SUI/USDT', 
    'SHIB/USDT', 'NEAR/USDT', 'RENDER/USDT', 'FET/USDT', 'INJ/USDT'
]

# Aliases de compatibilidad para pipelines existentes
MEMECOINS = SYMBOLS
TRADE_LOG_FILE = 'trades_log.csv'

# Parámetros del modelo y trading
TIMEFRAME = '1m'
MODEL_PATH = 'ppo_crypto_bot.zip'
HISTORICAL_DAYS = 30

# --- DISCORD ---
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1547720496479469578/IGJaA36bBJjHIhdNwZYl8-OV8PNa9ivZsPf0zvKbo3383oHdSSNIMeiqnpn0FOCAC9Lx"