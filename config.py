# config.py

# --- CREDENCIALES DE BINANCE (SANDBOX / TESTNET) ---
BINANCE_API_KEY = 'k7lMQnkID6gZwhfFtzFg8MhBdrwMXv9xUXxbL13Nsehsf24MK27s1x9FmggoKleL'
BINANCE_API_SECRET = '2RfQR611idClDGuPqNwSh4Opf63UG5HVaA6D3hbXe2yHlIef90uU877rvLmuo1lW'
USE_SANDBOX = True  # True para Testnet / False para Producción real

# --- LISTA DE MEMECOINS A OPERAR ---
MEMECOINS = [
    'PEPE/USDT', 'DOGE/USDT', 'SHIB/USDT', 'FLOKI/USDT', 'BONK/USDT',
    'WIF/USDT', 'BOME/USDT', 'MEME/USDT', 'MYRO/USDT', 'POPCAT/USDT',
    'NEIRO/USDT', 'GOAT/USDT', 'PNUT/USDT', 'ACT/USDT', 'CHILLGUY/USDT',
    'CATI/USDT', 'DOGS/USDT', 'TURBO/USDT', 'COW/USDT'
]

# --- PARÁMETROS DE TRADING Y GESTIÓN DE RIESGO ---
TIMEFRAME = '1m'
TRADE_AMOUNT_USDT = 10.0      # Capital en USDT asignado por cada operación simultánea
STOP_LOSS_PCT = 0.05         # 5% de stop loss inicial
TAKE_PROFIT_PCT = 0.10       # 10% de take profit initial
TRAILING_ACTIVATION = 0.02   # Activar trailing stop al 2% de ganancia
TRAILING_DISTANCE = 0.01     # Distancia del trailing stop (1%)

# --- RUTAS DE ARCHIVOS Y MODELO ---
MODEL_PATH = 'ppo_memecoin_bot.zip'
STATE_FILE = 'bot_state.json'
TRADE_LOG_FILE = 'trade_actions_log.csv'

# --- DISCORD ---
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1547720496479469578/IGJaA36bBJjHIhdNwZYl8-OV8PNa9ivZsPf0zvKbo3383oHdSSNIMeiqnpn0FOCAC9Lx"