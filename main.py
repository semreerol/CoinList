import os
import requests
import pandas as pd
import json
from datetime import datetime

# --- AYARLAR ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HISTORY_FILE = "history.json"
ANALYSIS_DAYS = 10  # Son kaç güne bakılacak?

def load_history():
    """Geçmiş verileri JSON dosyasından okur."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    """Güncel verileri JSON dosyasına kaydeder ve son 10 günü tutar."""
    # Sadece son X günü tut, dosya şişmesin
    trimmed_history = history[-ANALYSIS_DAYS:]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(trimmed_history, f, indent=4)

def analyze_momentum(history, current_gainers):
    """Hangi coinlerin ısrarlı yükselişte olduğunu bulur."""
    momentum_coins = {}
    
    # Şu anki yükselenler listesindeki her coin için geçmişe bak
    for index, row in current_gainers.iterrows():
        symbol = row['Symbol']
        count = 1 # Bugün listeye girdiği için 1 ile başla
        
        for day_record in history:
            # Geçmiş kayıtlardaki 'gainers' listesinde bu coin var mı?
            if symbol in day_record.get('gainers', []):
                count += 1
        
        # Eğer coin son günlerde 2 veya daha fazla kez listeye girdiyse not al
        if count >= 2:
            momentum_coins[symbol] = count
            
    return momentum_coins

def get_market_data():
    # CoinGecko'dan veri çekme (Önceki kodun aynısı)
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "price_change_percentage_24h_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": "false"
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        
        market_data = []
        for item in data:
            symbol = item['symbol'].upper()
            if symbol in ['USDT', 'USDC', 'DAI', 'FDUSD', 'TUSD', 'WBTC']: continue # Stablecoinleri ele
            
            market_data.append({
                'Symbol': symbol,
                'Price': item['current_price'],
                'Change': item['price_change_percentage_24h'],
                'Volume': item['total_volume']
            })

        df = pd.DataFrame(market_data)
        gainers = df.sort_values(by='Change', ascending=False).head(5)
        losers = df.sort_values(by='Change', ascending=True).head(5)
        return gainers, losers

    except Exception as e:
        print(f"Hata: {e}")
        return None, None

def send_telegram_message(gainers, losers, momentum_data):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return

    date_str = datetime.now().strftime('%d-%m-%Y')
    message = f"📊 **GÜNLÜK PİYASA ANALİZİ** ({date_str})\n\n"

    # --- Yükselenler ---
    message += "🚀 **EN ÇOK YÜKSELENLER**\n"
    for _, row in gainers.iterrows():
        symbol = row['Symbol']
        
        # Analiz Notu Ekleme
        note = ""
        if symbol in momentum_data:
            count = momentum_data[symbol]
            note = f"\n🔥 _DİKKAT: Son {ANALYSIS_DAYS} günde {count}. kez listede!_"

        message += (
            f"🔹 *{symbol}* {note}\n"
            f"   Fiyat: {row['Price']}$\n"
            f"   Değişim: %{row['Change']:.2f} 🟢\n"
        )
    
    message += "\n" + "-"*20 + "\n\n"

    # --- Düşenler (Kısa tuttum) ---
    message += "🩸 **EN ÇOK DÜŞENLER**\n"
    for _, row in losers.iterrows():
        message += f"🔸 *{row['Symbol']}*: %{row['Change']:.2f} 🔴\n"

    # Gönder
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'})

if __name__ == "__main__":
    # 1. Veriyi Çek
    gainers, losers = get_market_data()
    
    if gainers is not None:
        # 2. Geçmişi Yükle
        history = load_history()
        
        # 3. Analiz Yap
        momentum = analyze_momentum(history, gainers)
        
        # 4. Mesaj Gönder
        send_telegram_message(gainers, losers, momentum)
        
        # 5. Geçmişi Güncelle ve Kaydetmek üzere hazırla
        # Sadece sembolleri kaydetsek yeterli, dosya boyutu küçük kalsın
        today_record = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "gainers": gainers['Symbol'].tolist()
        }
        history.append(today_record)
        save_history(history)
