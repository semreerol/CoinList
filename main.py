import os
import requests
from datetime import datetime

# --- 1. DEĞİŞKENLERİ ORTAM DEĞİŞKENLERİNDEN (ENV) ÇEK ---
# GitHub Actions yml dosyasındaki 'env' kısmından buraya aktarılır.
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(gainers, losers):
    # --- 2. GÜVENLİK KONTROLÜ ---
    # Eğer token okunamazsa işlem yapma ve hata ver.
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("KRİTİK HATA: Token veya Chat ID okunamadı! GitHub Secret'ları kontrol et.")
        return

    if gainers is None or losers is None:
        return

    # Mesaj Başlığı
    date_str = datetime.now().strftime('%d-%m-%Y %H:%M')
    message = f"📊 **BYBIT GÜNLÜK RAPORU** ({date_str})\n\n"

    # Yükselenler Bölümü
    message += "🚀 **EN ÇOK YÜKSELENLER (TOP 5)**\n"
    for _, row in gainers.iterrows():
        # format_volume fonksiyonunun tanımlı olduğunu varsayıyorum
        # Eğer hata alırsan buraya basit bir f-string koyabilirsin.
        vol_str = f"{row['Volume']:,.0f}" 
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
        vol_str = f"{row['Volume']:,.0f}"
        message += (
            f"🔸 *{row['Symbol']}*\n"
            f"   Fiyat: {row['Price']}$\n"
            f"   Değişim: %{row['Change']:.2f} 🔴\n"
            f"   Hacim: {vol_str}\n"
        )

    # --- 3. URL OLUŞTURMA VE GÖNDERME ---
    # Token'ı buraya f-string ile yerleştiriyoruz.
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        # Debug için URL'yi yazdırma (Güvenlik için token'ı gizle)
        print("Telegram isteği gönderiliyor...") 
        
        r = requests.post(url, data=payload)
        
        if r.status_code == 200:
            print("✅ Telegram bildirimi başarıyla gönderildi!")
        else:
            # Hata detayını gör
            print(f"❌ Telegram Hatası (Kod: {r.status_code}): {r.text}")
            
    except Exception as e:
        print(f"❌ İstek Hatası: {e}")

# --- Çalıştırma ---
if __name__ == "__main__":
    # get_market_data fonksiyonunun çalıştığını varsayıyoruz
    # Eğer test etmek istersen, verileri manuel oluşturabilirsin.
    try:
        top_gainers, top_losers = get_market_data()
        send_telegram_message(top_gainers, top_losers)
    except NameError:
        print("Uyarı: 'get_market_data' fonksiyonu bulunamadı, kodun geri kalanı ile birleştirin.")
