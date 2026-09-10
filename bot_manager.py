import json
import os
import sys
import datetime
import time
import numpy as np
import pandas as pd
import requests  # <- Necesario para enviar peticiones al Webhook de Discord
from stable_baselines3 import PPO
from exchange_api import BinanceAPI
import daily_pipeline
import config

api = BinanceAPI()

def send_discord_message(content):
    """Envía un mensaje a Discord usando un Webhook."""
    if not hasattr(config, 'DISCORD_WEBHOOK_URL') or not config.DISCORD_WEBHOOK_URL:
        return
    try:
        payload = {"content": content}
        requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"[ERROR DISCORD] No se pudo enviar el mensaje: {e}")

def load_state():
    if os.path.exists(config.STATE_FILE):
        try:
            with open(config.STATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('active_positions', []), data.get('initial_capital', None), data.get('historical_realized_pnl', 0.0)
        except Exception:
            pass
    return [], None, 0.0

def save_state(active_positions, initial_capital, historical_realized_pnl):
    try:
        with open(config.STATE_FILE, 'w') as f:
            json.dump({
                'active_positions': active_positions,
                'initial_capital': initial_capital,
                'historical_realized_pnl': historical_realized_pnl
            }, f)
    except Exception as e:
        print(f"[ERROR GUARDANDO ESTADO] {e}")

def log_trade_action(timestamp, symbol, action_type, entry, exit_price, amount, pnl_usdt):
    file_exists = os.path.exists(config.TRADE_LOG_FILE)
    df_new = pd.DataFrame([{
        'timestamp': timestamp,
        'symbol': symbol,
        'action': action_type,
        'entry_price': entry,
        'exit_price': exit_price,
        'amount': amount,
        'pnl_usdt': pnl_usdt
    }])
    df_new.to_csv(config.TRADE_LOG_FILE, mode='a', header=not file_exists, index=False)

def run_pipeline():
    active_positions, initial_capital, historical_realized_pnl = load_state()
    now = datetime.datetime.now()

    dfs, current_prices = api.fetch_ohlcv_data(config.MEMECOINS, timeframe=config.TIMEFRAME, limit=200)
    usdt_balance = api.get_balance()

    if len(dfs) == 0 or not current_prices:
        print(f"[{now}] [ADVERTENCIA] Sin datos suficientes de mercado en este ciclo.")
        return None, None, None, None # Para control de reportes

    if not os.path.exists(config.MODEL_PATH):
        print(f"[{now}] [INFO] Generando modelo inicial...")
        daily_pipeline.run_daily_retrain()

    model = PPO.load(config.MODEL_PATH)

    total_invested_value = sum([p['amount'] * current_prices[p['symbol']] for p in active_positions if p['symbol'] in current_prices])
    total_portfolio = usdt_balance + total_invested_value
    if initial_capital is None:
        initial_capital = total_portfolio

    # 1. Gestión de posiciones activas y cierres
    surviving_positions = []
    positions_summary_text = []
    realized_this_cycle = 0.0

    for i, pos in enumerate(active_positions):
        sym = pos['symbol']
        if sym not in current_prices:
            surviving_positions.append(pos)
            continue
            
        price = current_prices[sym]
        entry = pos['entry_price']
        amount = pos['amount']
        
        if price > pos['highest_price']:
            pos['highest_price'] = price
            profit_pct = (price - entry) / entry
            if profit_pct >= config.TRAILING_ACTIVATION:
                new_sl = price * (1 - config.TRAILING_DISTANCE)
                if new_sl > pos['sl_price']:
                    pos['sl_price'] = new_sl

        pnl_pct = ((price - entry) / entry) * 100
        pnl_usdt = (price - entry) * amount
        current_value = amount * price
        
        positions_summary_text.append(f"   └─ #{i+1} Par: {sym} | Valor: {current_value:.2f} USDT | P&L: {pnl_usdt:+.2f} USDT ({pnl_pct:+.2f}%)")

        exit_reason = None
        if price <= pos['sl_price']:
            exit_reason = "STOP LOSS / TRAILING"
        elif price >= pos['tp_price']:
            exit_reason = "TAKE PROFIT"

        if exit_reason:
            try:
                api.market_sell(sym, amount)
                realized_this_cycle += pnl_usdt
                log_trade_action(now, sym, exit_reason, entry, price, amount, pnl_usdt)
                msg_cierre = f"🔴 [{now}] **CIERRE** {sym} cerrado por {exit_reason} | P&L: {pnl_usdt:+.2f} USDT"
                print(f"\n{msg_cierre}")
                send_discord_message(msg_cierre)
            except Exception as e:
                print(f"[{now}] [ERROR] No se pudo vender {sym}: {e}")
        else:
            surviving_positions.append(pos)

    active_positions = surviving_positions
    historical_realized_pnl += realized_this_cycle

    # 2. Inferencia del Modelo (Agresiva)
    obs = []
    for symbol in config.MEMECOINS:
        if symbol in dfs and not dfs[symbol].empty:
            row = dfs[symbol].iloc[-1]
            obs.extend([row['returns'], row['rsi'], row['volatility'], row['sma_fast_dist'], row['sma_slow_dist']])
        else:
            obs.extend([0.0, 50.0, 0.0, 0.0, 0.0])

    obs.append(usdt_balance / (initial_capital if initial_capital else 1000))
    obs.append(len(active_positions))
    obs.extend([0.0, 0.0, 0.0])  
    
    expected_dim = model.observation_space.shape[0]
    if len(obs) < expected_dim:
        obs.extend([0.0] * (expected_dim - len(obs)))
    elif len(obs) > expected_dim:
        obs = obs[:expected_dim]

    action, _ = model.predict(np.array(obs, dtype=np.float32), deterministic=True)
    
    if action > 0:
        action_idx = action - 1
        if action_idx < len(config.MEMECOINS):
            target_sym = config.MEMECOINS[action_idx]
            if target_sym in current_prices and usdt_balance >= config.TRADE_AMOUNT_USDT:
                price = current_prices[target_sym]
                amount_to_buy = config.TRADE_AMOUNT_USDT / price
                try:
                    api.market_buy(target_sym, amount_to_buy)
                    active_positions.append({
                        'symbol': target_sym,
                        'entry_price': price,
                        'amount': amount_to_buy,
                        'highest_price': price,
                        'sl_price': price * (1 - config.STOP_LOSS_PCT),
                        'tp_price': price * (1 + config.TAKE_PROFIT_PCT)
                    })
                    msg_compra = f"🟢 [{now}] **COMPRA** Abierta posición en {target_sym} por {config.TRADE_AMOUNT_USDT} USDT"
                    print(msg_compra)
                    send_discord_message(msg_compra)
                except Exception as e:
                    print(f"[{now}] [ERROR AL COMPRAR] {e}")

    total_pnl_usdt = total_portfolio - initial_capital
    total_pnl_pct = (total_pnl_usdt / initial_capital) * 100 if initial_capital > 0 else 0.0

    save_state(active_positions, initial_capital, historical_realized_pnl)

    # Consola local
    print(f"\n================ [{now}] ================")
    print(f"Saldo Actual USDT: {usdt_balance:.2f} USDT | Cartera Total: {total_portfolio:.2f} USDT")
    print(f"Órdenes abiertas ({len(active_positions)}):")
    if positions_summary_text:
        for line in positions_summary_text: print(line)
    else:
        print("   └─ Ninguna orden abierta actualmente.")
    print("--------------------------------------------------")
    print(f"P&L Total del Día (Actual): {total_pnl_usdt:+.2f} USDT ({total_pnl_pct:+.2f}%)")
    print(f"P&L Histórico Acumulado:     {historical_realized_pnl:+.2f} USDT")
    print("==================================================")

    # Retornamos datos para armar el reporte de Discord si se requiere
    return total_portfolio, usdt_balance, total_pnl_usdt, total_pnl_pct, active_positions

def main_daemon():
    print("[DAEMON] Bot ejecutándose cada 1 minuto (Estrategia Agresiva + Logging CSV + Discord).")
    
    # Mensaje inicial al encender el bot
    send_discord_message("🤖 **Bot iniciado / reiniciado con éxito.** Monitoreo activo.")
    
    last_retrained_date = None
    counter_minutes = 0  # Para controlar el envío cada hora (60 minutos)

    while True:
        try:
            now = datetime.datetime.now()
            
            # Verificamos si es medianoche (00:00) para reentrenamiento
            if now.hour == 0 and now.minute == 0 and (last_retrained_date != now.date()):
                msg_ok = f"[{now}] [00:00] **OK**. Actualizando modelo nocturno, pausando y reiniciando ciclo..."
                print(f"\n{msg_ok}")
                send_discord_message(msg_ok)
                
                try:
                    daily_pipeline.run_daily_retrain()
                except Exception as e:
                    error_msg = f"[ERROR EN REENTRENAMIENTO NOCTURNO] {e}"
                    print(error_msg)
                    send_discord_message(f"⚠️ {error_msg}")
                
                last_retrained_date = now.date()
                
                resume_msg = f"[{now}] [DAEMON] Reentrenamiento diario finalizado. Bot prendido y operativo nuevamente."
                print(resume_msg)
                send_discord_message(f"✅ {resume_msg}")
                
                counter_minutes = 0 # Reiniciar contador de hora
                time.sleep(60)
            else:
                res = run_pipeline()
                
                # Cada 60 minutos mandamos un reporte resumen a Discord
                if counter_minutes >= 60 and res is not None:
                    total_portfolio, usdt_balance, total_pnl_usdt, total_pnl_pct, active_positions = res
                    reporte_hora = (
                        f"📊 **Reporte Horario del Bot**\n"
                        f"• Cartera Total: `{total_portfolio:.2f} USDT`\n"
                        f"• Saldo USDT: `{usdt_balance:.2f} USDT`\n"
                        f"• Posiciones Abiertas: `{len(active_positions)}`\n"
                        f"• P&L del Día: `{total_pnl_usdt:+.2f} USDT ({total_pnl_pct:+.2f}%)`"
                    )
                    send_discord_message(reporte_hora)
                    counter_minutes = 0
                
                counter_minutes += 1
                
        except Exception as e:
            err_msg = f"[ERROR CRÍTICO EN BUCLE PRINCIPAL] {e}"
            print(err_msg, file=sys.stderr)
            send_discord_message(f"🚨 {err_msg}")

        time.sleep(60)

if __name__ == "__main__":
    main_daemon()