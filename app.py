import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="İnteraktif EKG Simülatörü", layout="wide")

st.title("❤️ İnteraktif EKG (Elektrokardiyogram) Simülatörü")
st.markdown("""
Bu simülatör, farklı kalp ritimlerini ve parametrelerini test etmenizi sağlar. 
Yandaki menüyü kullanarak nabzı, ritim tipini ve sinyal gürültüsünü değiştirebilirsiniz.
""")

# --- Kenar Çubuğu (Kontroller) ---
st.sidebar.header("🎛️ Simülatör Ayarları")
heart_rate = st.sidebar.slider("Kalp Atış Hızı (BPM)", min_value=30, max_value=180, value=75, step=1)
rhythm_type = st.sidebar.selectbox(
    "Ritim Türü",
    ["Normal Sinüs Ritmi", "Sinüs Taşikardisi (Hızlı)", "Sinüs Bradikardisi (Yavaş)", "Atriyal Fibrilasyon (Düzensiz)"]
)
noise_level = st.sidebar.slider("Parazit / Gürültü Seviyesi", min_value=0.0, max_value=0.5, value=0.05, step=0.01)
show_grid = st.sidebar.checkbox("EKG Izgarasını Göster", value=True)

# --- EKG Sinyal Üretici Fonksiyon ---
def generate_ecg(duration=10, fs=500, hr=75, rhythm="Normal Sinüs Ritmi", noise=0.05):
    num_samples = duration * fs
    t = np.linspace(0, duration, num_samples)
    
    # Ritim türüne göre beat aralıkları (RR aralığı) belirleme
    if rhythm == "Sinüs Taşikardisi (Hızlı)":
        hr = max(hr, 100)
    elif rhythm == "Sinüs Bradikardisi (Yavaş)":
        hr = min(hr, 60)
        
    avg_interval = 60.0 / hr
    
    # Kalp atış zamanlarını oluştur (RR düzensizliği AFib için eklenir)
    beat_times = []
    current_time = 0.5
    while current_time < duration - 1:
        if rhythm == "Atriyal Fibrilasyon (Düzensiz)":
            # AFib için düzensiz aralıklar
            interval = np.random.normal(avg_interval, avg_interval * 0.25)
        else:
            # Normal varyasyon (solunum sinüs aritmisi etkisi)
            interval = np.random.normal(avg_interval, 0.03)
        
        current_time += max(0.3, interval)
        beat_times.append(current_time)
        
    signal = np.zeros_codes = np.zeros_like(t)
    
    # Her bir vuruş için P-Q-R-S-T dalgalarını yerleştir
    for bt in beat_times:
        # P dalgası
        signal += 0.15 * np.exp(-((t - (bt - 0.16))**2) / (0.01**2))
        # Q dalgası
        signal -= 0.10 * np.exp(-((t - (bt - 0.04))**2) / (0.003**2))
        # R dalgası (Ana sivri uç)
        signal += 1.20 * np.exp(-((t - bt)**2) / (0.004**2))
        # S dalgası
        signal -= 0.25 * np.exp(-((t - (bt + 0.04))**2) / (0.004**2))
        # T dalgası
        signal += 0.30 * np.exp(-((t - (bt + 0.25))**2) / (0.03**2))
        
        # AFib durumunda P dalgalarını yok et / kaotik dalgalar ekle
        if rhythm == "Atriyal Fibrilasyon (Düzensiz)":
            signal += np.random.normal(0, 0.05, len(t)) * np.exp(-((t - bt)**2) / (0.1**2))

    # Temel çizgi dalgalanması (solunum artefaktı)
    baseline_wander = 0.1 * np.sin(2 * np.pi * 0.2 * t)
    signal += baseline_wander
    
    # Elektrot gürültüsü ekleme
    signal += np.random.normal(0, noise, num_samples)
    
    return t, signal

# --- Sinyali Çizdirme ---
t, ecg_signal = generate_ecg(hr=heart_rate, rhythm=rhythm_type, noise=noise_level)

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(t, ecg_signal, color="#d63031", linewidth=1.2)

if show_grid:
    # EKG kağıdı tarzı kareler
    ax.set_xticks(np.arange(0, 11, 0.2))
    ax.set_yticks(np.arange(-1.5, 2.0, 0.5))
    ax.grid(True, which='both', color='#ff7675', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.minorticks_on()
    ax.grid(True, which='minor', color='#ff7675', linestyle=':', linewidth=0.3, alpha=0.3)
else:
    ax.grid(True, linestyle='--', alpha=0.6)

ax.set_title(f"Simüle Edilen EKG Kaydı - Ritim: {rhythm_type} ({heart_rate} BPM)", fontsize=14, fontweight='bold')
ax.set_xlabel("Zaman (saniye)")
ax.set_ylabel("Genlik (mV)")
ax.set_xlim(0, 10)

st.pyplot(fig)

# --- Bilgilendirme Alanı ---
col1, col2, col3 = st.columns(3)
col1.metric("Anlık Nabız", f"{heart_rate} BPM")
col2.metric("Seçilen Ritim", rhythm_type)
col3.metric("Durum", "Normal" if "Normal" in rhythm_type else "Kritik / Düzensiz")

st.markdown("---")
st.markdown("### 💡 Bilgi Notu")
st.info("""
- **P Dalgası:** Kulakçıkların (atriyum) kasılması.
- **QRS Kompleksi:** Karıncıkların (ventrikül) kasılması (en sivri büyük dalga).
- **T Dalgası:** Karıncıkların yeniden dinlenme (polarizasyon) evresi.
""")