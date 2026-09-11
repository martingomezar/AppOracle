# download_history.py
import os
import pandas as pd
import numpy as np
from exchange_api import BybitAPI
import config

def download_all():
    api = BybitAPI()
    os.makedirs('data', exist_ok=True)
    
    print("Iniciando descarga de datos históricos desde Bybit Testnet...")
    for symbol in config.SYMBOLS:
        safe_name = symbol.replace('/', '_')
        filename = f"data/hist_{safe_name}.csv"
        print(f"Descargando {symbol} ({config.HISTORICAL_DAYS} días)...")
        
        df = api.fetch_historical_ohlcv(symbol, timeframe='1h', days_back=config.HISTORICAL_DAYS)
        if df.empty or len(df) < 50:
            print(f"[Aviso] No se pudieron obtener suficientes datos reales para {symbol}. Generando respaldo sintético...")
            dates = pd.date_range(end=pd.Timestamp.now(), periods=720, freq='h')
            base_price = 100.0
            price_series = base_price + np.cumsum(np.random.normal(0, 0.5, len(dates)))
            df = pd.DataFrame({
                'timestamp': dates,
                'open': price_series,
                'high': price_series + 0.5,
                'low': price_series - 0.5,
                'close': price_series,
                'volume': np.random.randint(1000, 10000, len(dates))
            })
            
        df.to_csv(filename, index=False)
        print(f"[OK] Guardado en {filename} ({len(df)} registros).")

if __name__ == '__main__':
    download_all()