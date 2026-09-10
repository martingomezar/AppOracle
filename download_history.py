# download_history.py
import os
from exchange_api import BinanceAPI

MEMECOINS = [
    'PEPE/USDT', 'DOGE/USDT', 'SHIB/USDT', 'FLOKI/USDT', 'BONK/USDT',
    'WIF/USDT', 'BOME/USDT', 'MEME/USDT', 'MYRO/USDT', 'POPCAT/USDT',
    'NEIRO/USDT', 'GOAT/USDT', 'PNUT/USDT', 'ACT/USDT', 'CHILLGUY/USDT',
    'CATI/USDT', 'DOGS/USDT', 'TURBO/USDT', 'COW/USDT'
]

def main():
    # Inicializa la API
    api = BinanceAPI(sandbox=True)
    
    # Configuración del historial
    timeframe = '1h'     # Temporalidad de las velas (ej. '1h', '15m')
    days_back = 90       # Cantidad de días hacia atrás a descargar

    print(f"Iniciando descarga de historial ({timeframe}, últimos {days_back} días)...")

    for symbol in MEMECOINS:
        print(f"Procesando {symbol}...")
        df = api.fetch_historical_ohlcv(symbol, timeframe=timeframe, days_back=days_back)
        
        if not df.empty:
            filename = f"hist_{symbol.replace('/', '_')}.csv"
            df.to_csv(filename, index=False)
            print(f"  -> Guardado con éxito: {filename} ({len(df)} registros)")
        else:
            print(f"  -> [AVISO] No se obtuvieron datos suficientes para {symbol}")

    print("\n¡Descarga completada! Ya puedes ejecutar train_model.py")

if __name__ == "__main__":
    main()