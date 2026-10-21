import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Klinik Düzeyde İleri EKG Simülatörü - Wave-Maven Modülü", layout="wide")

st.title("🫀 Klinik ve Akademik EKG Simülatörü (Vaka Tabanlı Analiz)")
st.markdown("""
Bu araç; Harvard ECG Wave-Maven benzeri olgu örnekleri baz alınarak, aynı patolojinin **farklı klinik varyantlarını** 
(Örn: Anterior vs. İnferior STEMI, Hızlı vs. Kontrollü AFib) inceleyebilmeniz için geliştirilmiştir.
""")

# --- Kenar Çubuğu: Vaka ve Parametre Seçimi ---
st.sidebar.header("🎛️ Vaka ve Ritim Parametreleri")

category = st.sidebar.selectbox(
    "Klinik Patoloji Kategorisi",
    [
        "Akut Koroner Sendromlar (STEMI Varyantları)",
        "Atriyalaritmi ve Fibrilasyon Varyantları",
        "İletim Bozuklukları ve AV Bloklar",
        "İntraventriküler İletim (Dal Blokları)"
    ]
)

# Kategoriye göre alt vaka örnekleri
if category == "Akut Koroner Sendromlar (STEMI Varyantları)":
    rhythm_type = st.sidebar.selectbox("Spesifik Vaka Örneği", [
        "Vaka 1: Akut Anterior STEMI (V1-V4 Elevasyon & Q Dalgaları)",
        "Vaka 2: Akut İnferior STEMI (DII, DIII, aVF Elevasyon & Reciprok Depresyon)"
    ])
elif category == "Atriyalaritmi ve Fibrilasyon Varyantları":
    rhythm_type = st.sidebar.selectbox("Spesifik Vaka Örneği", [
        "Vaka 1: Hızlı Ventriküler Yanıtlı AFib (RVR - Kaotik Çizgi)",
        "Vaka 2: Kontrollü Ventriküler Yanıtlı AFib (Normokratik AFib)"
    ])
elif category == "İletim Bozuklukları ve AV Bloklar":
    rhythm_type = st.sidebar.selectbox("Spesifik Vaka Örneği", [
        "Vaka 1: Birinci Derece AV Blok (Sabit Uzamış PR > 200ms)",
        "Vaka 2: İkinci Derece Tip 1 (Wenckebach) AV Blok"
    ])
else:
    rhythm_type = st.sidebar.selectbox("Spesifik Vaka Örneği", [
        "Vaka 1: Sol Dal Bloğu (LBBB - Geniş QRS, V5-V6 Çentikli R)",
        "Vaka 2: Sağ Dal Bloğu (RBBB - V1-V2'de RSR' Müşerref)"
    ])

heart_rate = st.sidebar.slider("Kalp Atış Hızı (BPM)", min_value=30, max_value=180, value=80, step=1)
noise_level = st.sidebar.slider("Artefakt / Gürültü Seviyesi", min_value=0.0, max_value=0.15, value=0.02, step=0.01)
show_grid = st.sidebar.checkbox("Standart Tıbbi EKG Izgarası", value=True)

# --- Gelişmiş Sinyal ve Vaka Üretici Fonksiyon ---
def generate_case_ecg(duration=10, fs=1000, hr=80, vaka=""):
    num_samples = duration * fs
    t = np.linspace(0, duration, num_samples)
    
    avg_interval = 60.0 / hr
    beat_times = []
    current_time = 0.5
    
    while current_time < duration - 1:
        if "AFib" in vaka:
            if "Hızlı" in vaka:
                interval = np.random.uniform(0.3, 0.5)
            else:
                interval = np.random.uniform(0.6, 1.0)
        elif "Wenckebach" in vaka:
            # Wenckebach ritmi için progresif kısalan RR
            interval = avg_interval + np.random.normal(0, 0.05)
        else:
            interval = np.random.normal(avg_interval, 0.01)
            
        current_time += max(0.25, interval)
        beat_times.append(current_time)
        
    signal = np.zeros_like(t)
    
    # Temel morfoloji parametreleri
    pr_val = 0.16
    qrs_w = 0.004
    st_shift = 0.0
    t_amp = 0.3
    
    # Vakaya özel elektrofizyolojik modifikasyonlar
    if "Anterior STEMI" in vaka:
        st_shift = 0.75 # Belirgin Pardee dalgası / ST elevasyonu
    elif "İnferior STEMI" in vaka:
        st_shift = 0.60 # İnferior derivasyon benzeri yüksek ST
    elif "Birinci Derece" in vaka:
        pr_val = 0.28 # >200ms uzamış PR
    elif "Sol Dal Bloğu" in vaka:
        qrs_w = 0.011 # Genişlemiş QRS
    elif "Sağ Dal Bloğu" in vaka:
        qrs_w = 0.009

    for i, bt in enumerate(beat_times):
        # Wenckebach simülasyonu için her 4. atımda blok (P var, QRS yok)
        if "Wenckebach" in vaka and (i % 4 == 3):
            # Sadece P dalgası var, QRS düşmüş
            signal += 0.15 * np.exp(-((t - (bt - pr_val))**2) / (0.01**2))
            continue

        # P Dalgası
        if "AFib" not in vaka:
            signal += 0.15 * np.exp(-((t - (bt - pr_val))**2) / (0.012**2))
        else:
            # Kaotik fibrilasyon dalgalacıkları
            signal += np.random.normal(0, 0.02, len(t)) * np.exp(-((t - bt)**2) / (0.15**2))

        # Q ve R Dalgaları
        signal -= 0.1 * np.exp(-((t - (bt - 0.03))**2) / (0.002**2))
        
        if "Sol Dal Bloğu" in vaka:
            signal += 1.4 * np.exp(-((t - bt)**2) / qrs_w)
            signal += 1.2 * np.exp(-((t - (bt + 0.04))**2) / qrs_w) # Çentikli R
        elif "Sağ Dal Bloğu" in vaka:
            signal += 1.1 * np.exp(-((t - (bt - 0.01))**2) / qrs_w)
            signal += 1.3 * np.exp(-((t - (bt + 0.03))**2) / qrs_w) # RSR'
        else:
            signal += 1.3 * np.exp(-((t - bt)**2) / qrs_w)
            
        # S Dalgası
        signal -= 0.3 * np.exp(-((t - (bt + 0.035))**2) / (0.004**2))
        
        # ST Segmenti Değişiklikleri (STEMI)
        if st_shift > 0:
            st_box = np.exp(-((t - (bt + 0.08))**2) / (0.025**2))
            signal += st_shift * st_box
            
        # T Dalgası
        if "Sol Dal Bloğu" in vaka:
            t_amp = -0.4 # Diskordan T inversiyonu
        signal += t_amp * np.exp(-((t - (bt + 0.22))**2) / (0.035**2))

    # Gürültü ve bazal hat
    signal += 0.04 * np.sin(2 * np.pi * 0.2 * t)
    signal += np.random.normal(0, noise_level, num_samples)
    
    return t, signal

# --- Çizim İşlemi ---
t, ecg_signal = generate_case_ecg(hr=heart_rate, vaka=rhythm_type)

fig, ax = plt.subplots(figsize=(14, 4.5))
ax.plot(t, ecg_signal, color="#c0392b", linewidth=1.2)

if show_grid:
    ax.set_xticks(np.arange(0, 11, 0.2))
    ax.set_yticks(np.arange(-2.5, 3.0, 0.5))
    ax.grid(True, which='both', color='#e74c3c', linestyle='-', linewidth=0.6, alpha=0.4)
    ax.minorticks_on()
    ax.grid(True, which='minor', color='#e74c3c', linestyle=':', linewidth=0.3, alpha=0.3)
else:
    ax.grid(True, linestyle='--', alpha=0.5)

ax.set_title(f"Klinik Vaka Simülasyonu | Seçilen: {rhythm_type} ({heart_rate} BPM)", fontsize=13, fontweight='bold')
ax.set_xlabel("Zaman (saniye)")
ax.set_ylabel("Amplitüt (mV)")
ax.set_xlim(0, 10)
ax.set_ylim(-2.0, 2.5)

st.pyplot(fig)

# --- Detaylı Klinik Değerlendirme Raporu ---
st.markdown("### 📋 Vaka Elektrofizyolojik Analiz Paneli")
c1, c2, c3 = st.columns(3)

if "Anterior STEMI" in rhythm_type:
    c1.metric("Tanı Grubu", "Akut Koroner Sendrom")
    c2.metric("K Lokalizasyon", "V1-V4 (Anteroseptal / Apikal)")
    c3.metric("Aciliyet", "🚨 Kod İnarktüs / Primer PCI")
    st.error("**Klinik Vaka Açıklaması:** Sol ön inen arter (LAD) tıkanıklığına sekonder gelişen hiperakut evre; J noktasından itibaren kubbeleşen ST elevasyonu ve reciprokal değişiklikler izlenmektedir.")
elif "İnferior STEMI" in rhythm_type:
    c1.metric("Tanı Grubu", "Akut Koroner Sendrom")
    c2.metric("K Lokalizasyon", "DII, DIII, aVF (İnferior duvar)")
    c3.metric("Aciliyet", "🚨 Kod İnarktüs / Sağ Ventrikül İskemi Kontrolü")
    st.error("**Klinik Vaka Açıklaması:** Sağ koroner arter (RCA) veya LCX tutulumuna bağlı inferior yüzde akut transmural hasar bulguları mevcuttur.")
elif "AFib" in rhythm_type:
    c1.metric("Tanı Grubu", "Supraventriküler Aritmi")
    c2.metric("K Lokalizasyon", "Atriyal Kaos")
    c3.metric("Aciliyet", "⚠️ Hız Kontrolü / Antikoagülasyon")
    st.warning("**Klinik Vaka Açıklaması:** P dalgaları silinmiş, atriyal aktivite kaotik fibrilatör dalgalarla yer değiştirmiştir. R-R aralıkları mutlak düzensizdir.")
elif "Blok" in rhythm_type:
    c1.metric("Tanı Grubu", "İletim Sistemi Patolojisi")
    c2.metric("K Lokalizasyon", "AV Düğüm / His-Purkinje Sistemi")
    c3.metric("Aciliyet", "⚠️ Yakın İzlem / Pacemaker Değerlendirmesi")
    st.info("**Klinik Vaka Açıklaması:** İletim sistemindeki gecikme veya blok seviyesine bağlı olarak QRS genişlemesi ya da PR uzaması tablosudur.")
else:
    c1.metric("Tanı Grubu", "İntraventriküler İletim")
    c2.metric("K Lokalizasyon", "Dal Blokları (LBBB/RBBB)")
    c3.metric("Aciliyet", "🔍 Etyolojik İnceleme")
    st.success("**Klinik Vaka Açıklaması:** Ventriküler depolarizasyon vektörlerindeki sapmaya bağlı genişlemiş QRS kompleksleri ve morfolojik değişiklikler izlenmektedir.")
