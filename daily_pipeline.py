# daily_pipeline.py
import os
import datetime
import time
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from exchange_api import BinanceAPI
import config

def compute_indicators(df):
    df['returns'] = df['close'].pct_change()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['volatility'] = df['returns'].rolling(window=10).std()
    sma_fast = df['close'].rolling(window=5).mean()
    sma_slow = df['close'].rolling(window=20).mean()
    df['sma_fast_dist'] = (df['close'] - sma_fast) / sma_fast
    df['sma_slow_dist'] = (df['close'] - sma_slow) / sma_slow
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def analyze_last_24h_trades():
    if not os.path.exists(config.TRADE_LOG_FILE):
        return {"trades_24h": 0, "pnl_24h": 0.0, "win_rate_24h": 0.0}
    try:
        df_logs = pd.read_csv(config.TRADE_LOG_FILE)
        if 'timestamp' not in df_logs.columns:
            return {"trades_24h": 0, "pnl_24h": 0.0, "win_rate_24h": 0.0}
            
        df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
        recent = df_logs[df_logs['timestamp'] >= cutoff]
        
        trades_count = len(recent)
        pnl_24h = recent['pnl_usdt'].sum() if 'pnl_usdt' in recent.columns else 0.0
        wins = len(recent[recent['pnl_usdt'] > 0]) if trades_count > 0 else 0
        win_rate = (wins / trades_count) * 100 if trades_count > 0 else 0.0
        
        print(f"   [ANÁLISIS 24H] Trades: {trades_count} | P&L 24h: {pnl_24h:+.2f} USDT | Win Rate: {win_rate:.1f}%")
        return {"trades_24h": trades_count, "pnl_24h": pnl_24h, "win_rate_24h": win_rate}
    except Exception as e:
        print(f"   [AVISO] Error analizando log de 24h: {e}")
        return {"trades_24h": 0, "pnl_24h": 0.0, "win_rate_24h": 0.0}

def run_daily_retrain():
    print(f"\n================ [INICIO PIPELINE DIARIO: {datetime.datetime.now()}] ================")
    api = BinanceAPI()
    
    print("\n--- PASO 1: Cargando y actualizando CSVs históricos ---")
    dfs_dict = {}
    for symbol in config.MEMECOINS:
        filename = f"hist_{symbol.replace('/', '_')}.csv"
        df = pd.DataFrame()
        
        # Intenta descargar desde la red
        try:
            df_net = api.fetch_historical_ohlcv(symbol, timeframe='1h', days_back=30)
            if not df_net.empty:
                df = df_net
                df.to_csv(filename, index=False)
        except Exception:
            pass
            
        # Si la red falla, busca el archivo local
        if df.empty and os.path.exists(filename):
            try:
                df = pd.read_csv(filename)
            except:
                pass
                
        if not df.empty:
            processed = compute_indicators(df)
            if len(processed) > 50:
                dfs_dict[symbol] = processed

    # Si no hay ningún CSV ni datos de red, generamos dataset sintético para arranque en frío
    if len(dfs_dict) == 0:
        print("\n--- [AVISO] No se encontraron CSVs ni datos de red. Generando dataset sintético inicial ---")
        dates = pd.date_range(end=datetime.datetime.now(), periods=200, freq='h')
        np.random.seed(42)
        for symbol in config.MEMECOINS:
            base_price = 1.0 + np.random.rand() * 10
            random_walk = np.cumsum(np.random.randn(200) * 0.02)
            prices = np.clip(base_price + random_walk, 0.0001, None)
            
            df_dummy = pd.DataFrame({
                'timestamp': dates,
                'open': prices,
                'high': prices * 1.01,
                'low': prices * 0.99,
                'close': prices,
                'volume': np.random.rand(200) * 10000
            })
            processed = compute_indicators(df_dummy)
            if len(processed) > 50:
                dfs_dict[symbol] = processed

    print("\n--- PASO 2: Analizando rendimiento de las últimas 24 horas ---")
    metrics_24h = analyze_last_24h_trades()

    print("\n--- PASO 3: Reentrenando modelo con política AGRESIVA (PPO) ---")
    if len(dfs_dict) > 0:
        try:
            from environment import MemecoinTradingEnv
            env = MemecoinTradingEnv(dfs_dict=dfs_dict, metrics_24h=metrics_24h)
            
            if os.path.exists(config.MODEL_PATH):
                model = PPO.load(config.MODEL_PATH, env=env)
            else:
                model = PPO(
                    "MlpPolicy", 
                    env, 
                    learning_rate=0.0005,
                    n_steps=1024,
                    batch_size=64,
                    ent_coef=0.01,  # Fomenta exploración agresiva
                    verbose=0
                )
                
            model.learn(total_timesteps=15000)
            model.save(config.MODEL_PATH)
            print("[OK] ¡Modelo agresivo reentrenado y guardado con éxito!")
        except Exception as e:
            print(f"[ERROR EN ENTRENAMIENTO] {e}.")
    else:
        print("[ADVERTENCIA] Datos insuficientes para reentrenar hoy.")

    print(f"================ [FIN PIPELINE DIARIO] ================\n")

if __name__ == "__main__":
    run_daily_retrain()