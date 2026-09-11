# test_connection.py
import ccxt
import config

print("Probando conexion con Bybit Testnet...")
try:
    exchange = ccxt.bybit({
        'apiKey': config.BYBIT_API_KEY,
        'secret': config.BYBIT_API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    exchange.set_sandbox_mode(True)
    
    balance = exchange.fetch_balance()
    usdt_free = balance['free'].get('USDT', 0.0)
    print(f"\n¡CONEXIÓN EXITOSA CON BYBIT TESTNET!")
    print(f"Saldo USDT disponible: {usdt_free:.2f} USDT")
    
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"Precio actual BTC/USDT en Bybit Testnet: {ticker['last']}")
except Exception as e:
    print(f"\n[ERROR DE CONEXIÓN]: {e}")