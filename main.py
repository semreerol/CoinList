import requests
from pybit.unified_trading import HTTP
import pandas as pd
from datetime import datetime

# --- AYARLAR ---
TELEGRAM_BOT_TOKEN = "BURAYA_BOT_TOKENINIZI_YAZIN"
TELEGRAM_CHAT_ID = "BURAYA_CHAT_ID_YAZIN"

def format_volume(value):
    """Hacmi okunabilir formata (Milyon/Bin) çevirir."""
    val = float(value)
    if val >= 1_000_000:
        return f"{val/1_000_000:.2f}M$"
    elif val >= 1_000:
        return f"{val/1_000:.2f}K$"
    else:
        return f"{val:.2f}$"

def get_market_data():
    session = HTTP(testnet=False)
    try:
        # Spot piyasasındaki tüm tickerları çek
        response = session.get_tickers(category="spot")
        result = response.get('result', {}).get('list', [])
        
        market_data = []
        
        for item in result:
            symbol = item['symbol']
            if symbol.endswith('USDT'):
                price_change = float(item['price24hPcnt']) * 100
                last_price = float(item['lastPrice'])
                # turnover24h = USDT cinsinden hacim
                volume = float(item['turnover24h']) 
                
                # Çok düşük hacimli (ölü) coinleri filtrelemek isterseniz:
                # if volume < 50000: continue 

                market_data.append({
                    'Symbol': symbol,
                    'Price': last_price,
                    'Change': price_change,
                    'Volume': volume
                })
        
        df = pd.DataFrame(market_data)
        
        # En çok yükselenler
        gainers = df.sort_values(by='Change', ascending=False).head(5)
        # En çok düşenler
        losers = df.sort_values(by='Change', ascending=True).head(5)
        
        return gainers, losers
    except Exception as e:
        print(f"Veri çekme hatası: {e}")
        return None, None

def send_telegram_message(gainers, losers):
    if gainers is None or losers is None:
        return

    # Mesaj Başlığı
    date_str = datetime.now().strftime('%d-%m-%Y %H:%M')
    message = f"📊 **BYBIT GÜNLÜK RAPORU** ({date_str})\n\n"

    # Yükselenler Bölümü
    message += "🚀 **EN ÇOK YÜKSELENLER (TOP 5)**\n"
    for _, row in gainers.iterrows():
        vol_str = format_volume(row['Volume'])
        message += (
            f"🔹 *{row['Symbol']}*\n"
            f"   Fiyat: {row['Price']}$\n"
            f"   Değişim: %{row['Change']:.2f} 🟢\n"
            f"   Hacim: {vol_str}\n"
        )
    
    message += "\n" + "-"*20 + "\n\n"

    # Düşenler Bölümü
    message += "🩸 **EN ÇOK DÜŞENLER (TOP 5)**\n"
    for _, row in losers.iterrows():
        vol_str = format_volume(row['Volume'])
        message += (
            f"🔸 *{row['Symbol']}*\n"
            f"   Fiyat: {row['Price']}$\n"
            f"   Değişim: %{row['Change']:.2f} 🔴\n"
            f"   Hacim: {vol_str}\n"
        )

    # Telegram'a Gönder
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown' # Kalın ve italik yazı için gerekli
    }
    
    try:
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            print("Telegram bildirimi başarıyla gönderildi!")
        else:
            print(f"Telegram hatası: {r.text}")
    except Exception as e:
        print(f"İstek hatası: {e}")

# --- Çalıştırma ---
if __name__ == "__main__":
    top_gainers, top_losers = get_market_data()
    send_telegram_message(top_gainers, top_losers)