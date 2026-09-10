# environment.py
import gymnasium as gym
import numpy as np
import pandas as pd
import config

class MemecoinTradingEnv(gym.Env):
    metadata = {'render_modes': ['human']}

    def __init__(self, dfs_dict, metrics_24h=None, initial_balance=1000.0, fee=0.00075):
        super(MemecoinTradingEnv, self).__init__()
        self.dfs = dfs_dict
        self.symbols = list(self.dfs.keys())
        self.metrics_24h = metrics_24h or {"trades_24h": 0, "pnl_24h": 0.0, "win_rate_24h": 0.0}
        self.initial_balance = initial_balance
        self.trade_amount = config.TRADE_AMOUNT_USDT
        self.fee = fee
        
        # Espacio discreto: 0 = Hold, 1..N = Comprar símbolo i
        self.action_space = gym.spaces.Discrete(1 + len(self.symbols))
        
        # Estado: 5 indicadores por cada coin + saldo + posiciones + 3 métricas de rendimiento 24h
        obs_shape = (len(self.symbols) * 5 + 2 + 3,)
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=obs_shape, 
            dtype=np.float32
        )
        
        self.current_step = 50
        self.max_steps = min([len(df) for df in self.dfs.values()]) - 1 if self.dfs else 100
        self.balance = initial_balance
        self.positions = []

    def reset(self, seed=None):
        super().reset(seed=seed)
        self.current_step = 50
        self.balance = self.initial_balance
        self.positions = []
        return self._get_observation(), {}

    def _get_observation(self):
        obs = []
        for symbol in self.symbols:
            row = self.dfs[symbol].iloc[self.current_step]
            obs.extend([
                row['returns'],
                row['rsi'],
                row['volatility'],
                row['sma_fast_dist'],
                row['sma_slow_dist']
            ])
        obs.append(self.balance / self.initial_balance)
        obs.append(len(self.positions))
        
        # Inyección de métricas recientes de las últimas 24 horas
        obs.append(self.metrics_24h.get("pnl_24h", 0.0) / 100.0)
        obs.append(self.metrics_24h.get("win_rate_24h", 0.0) / 100.0)
        obs.append(float(self.metrics_24h.get("trades_24h", 0)) / 10.0)
        
        return np.array(obs, dtype=np.float32)

    def step(self, action):
        reward = 0
        self.current_step += 1
        done = self.current_step >= self.max_steps
        truncated = False

        current_prices = {sym: self.dfs[sym].iloc[self.current_step]['close'] for sym in self.symbols}
        
        surviving_positions = []
        for pos in self.positions:
            sym = pos['symbol']
            price = current_prices[sym]
            entry = pos['entry_price']
            
            if price > pos['highest_price']:
                pos['highest_price'] = price
                if (price - entry) / entry >= config.TRAILING_ACTIVATION:
                    new_sl = price * (1 - config.TRAILING_DISTANCE)
                    if new_sl > pos['sl_price']:
                        pos['sl_price'] = new_sl

            pnl_pct = (price - entry) / entry
            if price <= pos['sl_price'] or price >= pos['tp_price']:
                closed_value = self.trade_amount * (1 + pnl_pct) * (1 - self.fee)
                self.balance += closed_value
                reward += pnl_pct * 100
            else:
                surviving_positions.append(pos)
        
        self.positions = surviving_positions

        if action > 0:
            action_idx = action - 1
            if action_idx < len(self.symbols):
                target_sym = self.symbols[action_idx]
                if self.balance >= self.trade_amount:
                    self.balance -= self.trade_amount
                    price = current_prices[target_sym]
                    self.positions.append({
                        'symbol': target_sym,
                        'entry_price': price,
                        'amount': self.trade_amount / price,
                        'highest_price': price,
                        'sl_price': price * (1 - config.STOP_LOSS_PCT),
                        'tp_price': price * (1 - config.TAKE_PROFIT_PCT)
                    })
                    reward += 0.2  # Incentivo por política activa

        return self._get_observation(), reward, done, truncated, {}