# exchange_api.py
import ccxt
import time
import pandas as pd
import config

class BybitAPI:
    def __init__(self, sandbox=None):
        sandbox_mode = config.USE_SANDBOX if sandbox is None else sandbox
        
        exchange_config = {
            'apiKey': config.BYBIT_API_KEY,
            'secret': config.BYBIT_API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        }

        self.exchange = ccxt.bybit(exchange_config)
        self.exchange.set_sandbox_mode(sandbox_mode)

    def fetch_ohlcv_data(self, symbols, timeframe='1m', limit=200):
        dfs = {}
        current_prices = {}
        for symbol in symbols:
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                if not ohlcv or len(ohlcv) < 30:
                    continue
                
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                
                current_prices[symbol] = float(df.iloc[-1]['close'])
                
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
                
                if len(df) > 0:
                    dfs[symbol] = df
            except Exception as e:
                pass
                
        return dfs, current_prices

    def fetch_historical_ohlcv(self, symbol, timeframe='1h', days_back=30):
        all_ohlcv = []
        since = int((time.time() - (days_back * 24 * 3600)) * 1000)
        now = int(time.time() * 1000)
        
        while since < now:
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
                if not ohlcv:
                    break
                since = ohlcv[-1][0] + 1
                all_ohlcv.extend(ohlcv)
                time.sleep(self.exchange.rateLimit / 1000)
            except Exception:
                time.sleep(1)
                break
                
        if not all_ohlcv:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.drop_duplicates(subset=['timestamp'], inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def get_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['free'].get('USDT', 0.0))
        except Exception:
            return 0.0

    def market_buy(self, symbol, amount):
        return self.exchange.create_market_buy_order(symbol, amount)

    def market_sell(self, symbol, amount):
        return self.exchange.create_market_sell_order(symbol, amount)