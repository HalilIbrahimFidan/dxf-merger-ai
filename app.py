import streamlit as st
import ezdxf
from ezdxf.addons import Importer
import ezdxf.bbox
import os
import tempfile
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="DXF Smart Merger", page_icon="📐", layout="wide")

# --- DİL SÖZLÜĞÜ ---
locales = {
    "en": {
        "title": "📐 DXF Smart Merger & Measurer",
        "subtitle": "Upload your 2D DXF drawings. The system will automatically extract their boundaries (W x H), label them, and merge them into a single DXF file.",
        "settings": "⚙️ Settings",
        "lang_select": "🌐 Language / Dil",
        "about_title": "🤖 About this App",
        "about_text": "This tool automatically measures and merges 2D DXF drawings exported from CAD software like SolidWorks.",
        "vibecoding": "✨ **Built with AI (Vibecoding)**",
        "upload_label": "Upload DXF Files here",
        "processing": "files loaded. Processing...",
        "table_filename": "File Name",
        "table_width": "Width (mm)",
        "table_height": "Height (mm)",
        "error_msg": "Error processing",
        "results_title": "📊 Analysis Results",
        "success_msg": "All drawings have been successfully merged!",
        "download_btn": "📥 Download Merged DXF",
        "output_filename": "Merged_Drawings.dxf",
        "w_label": "W",
        "h_label": "H",
        "metrics_total": "Total Files",
        "metrics_max_w": "Max Width",
        "metrics_max_h": "Max Height",
        "step_1": "Analyzing and sorting files...",
        "step_2": "Merging and generating layout..."
    },
    "tr": {
        "title": "📐 DXF Akıllı Birleştirici",
        "subtitle": "2D DXF çizimlerinizi yükleyin. Sistem otomatik olarak dış sınır ölçülerini (G x Y) bulur, etiketler ve hepsini tek bir DXF dosyasında birleştirir.",
        "settings": "⚙️ Ayarlar",
        "lang_select": "🌐 Dil / Language",
        "about_title": "🤖 Bu Uygulama Hakkında",
        "about_text": "Bu araç, SolidWorks gibi CAD yazılımlarından alınan 2D DXF çizimlerini otomatik ölçer ve tek dosyada toplar.",
        "vibecoding": "✨ **Yapay Zeka (Vibecoding) ile üretildi**",
        "upload_label": "DXF Dosyalarını Buraya Yükleyin",
        "processing": "adet dosya yüklendi. İşlem başlatılıyor...",
        "table_filename": "Dosya Adı",
        "table_width": "Genişlik (mm)",
        "table_height": "Yükseklik (mm)",
        "error_msg": "İşlenirken hata oluştu",
        "results_title": "📊 Analiz Sonuçları",
        "success_msg": "Tüm çizimler başarıyla birleştirildi!",
        "download_btn": "📥 Birleştirilmiş DXF'i İndir",
        "output_filename": "Birlestirilmis_Cizimler.dxf",
        "w_label": "G",
        "h_label": "Y",
        "metrics_total": "Toplam Dosya",
        "metrics_max_w": "Maksimum Genişlik",
        "metrics_max_h": "Maksimum Yükseklik",
        "step_1": "Dosyalar analiz ediliyor ve sıralanıyor...",
        "step_2": "Çizimler birleştiriliyor ve yerleştiriliyor..."
    }
}

# --- SOL MENÜ & DİL SEÇİMİ ---
with st.sidebar:
    st.header("🌐 Language / Dil")
    selected_lang = st.radio("", ["🇬🇧 English", "🇹🇷 Türkçe"], label_visibility="collapsed")
    lang = "tr" if "Türkçe" in selected_lang else "en"
    t = locales[lang]

    st.markdown("---")
    st.markdown(f"### {t['about_title']}")
    st.info(t['about_text'])
    st.markdown(t['vibecoding'])

# --- ANA EKRAN ---
st.title(t['title'])
st.markdown(f"*{t['subtitle']}*")
st.markdown("---")

uploaded_files = st.file_uploader(t['upload_label'], type=['dxf'], accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)} {t['processing']}")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # --- YERLEŞİM (LAYOUT) AYARLARI ---
    FIXED_TEXT_HEIGHT = 15.0  # Metinlerin sabit boyutu (mm)
    MARGIN_X = 50.0           # Parçalar arası yatay boşluk
    MARGIN_Y = 100.0          # Parçalar arası dikey boşluk (Yazılar için ekstra alan)
    MAX_ROW_WIDTH = 2500.0    # Bir satırın maksimum genişliği

    results_data = []
    parsed_parts = []
    max_w_overall = 0.0
    max_h_overall = 0.0

    with tempfile.TemporaryDirectory() as temp_dir:
        # AŞAMA 1: Dosyaları oku, ölç ve listeye kaydet (Henüz çizim yapmıyoruz)
        status_text.text(t['step_1'])
        
        for index, file in enumerate(uploaded_files):
            temp_filepath = os.path.join(temp_dir, file.name)
            with open(temp_filepath, "wb") as f:
                f.write(file.getbuffer())
                
            try:
                doc = ezdxf.readfile(temp_filepath)
                msp = doc.modelspace()
                bbox = ezdxf.bbox.extents(msp)
                
                if bbox.has_data:
                    min_x, min_y, _ = bbox.extmin
                    max_x, max_y, _ = bbox.extmax
                    w = max_x - min_x
                    h = max_y - min_y
                    
                    if w > max_w_overall: max_w_overall = w
                    if h > max_h_overall: max_h_overall = h
                    
                    parsed_parts.append({
                        "name": file.name,
                        "doc": doc,
                        "w": w,
                        "h": h,
                        "min_x": min_x,
                        "min_y": min_y
                    })
                    
                    results_data.append({
                        t['table_filename']: file.name, 
                        t['table_width']: round(w, 1), 
                        t['table_height']: round(h, 1)
                    })
            except Exception as e:
                st.error(f"{t['error_msg']} {file.name}: {str(e)}")
            
            # İlk aşama ilerlemesi (0% - 50%)
            progress_bar.progress((index + 1) / len(uploaded_files) * 0.5)

        # Çizimleri Yüksekliklerine göre büyükten küçüğe sırala (Daha temiz bir grid için)
        parsed_parts.sort(key=lambda item: item['h'], reverse=True)

        # AŞAMA 2: Sıralanmış parçaları ana dosyaya yerleştir
        status_text.text(t['step_2'])
        master_doc = ezdxf.new('R2010') 
        master_msp = master_doc.modelspace()
        
        current_x = 0.0
        current_y = 0.0
        max_row_height = 0.0

        for index, part in enumerate(parsed_parts):
            # Satır sınırına ulaşıldıysa alt satıra geç
            if current_x + part['w'] > MAX_ROW_WIDTH and current_x > 0:
                current_x = 0.0
                current_y -= (max_row_height + MARGIN_Y) # Y ekseninde aşağı in
                max_row_height = 0.0
                
            # Parçayı (0,0) noktasına değil, current_x ve current_y hedefine taşı
            offset_x = current_x - part['min_x']
            offset_y = current_y - part['min_y']
            
            for entity in part['doc'].modelspace():
                if hasattr(entity, 'translate'):
                    entity.translate(offset_x, offset_y, 0)
                    
            # 1. Satır Yazı: Dosya Adı (Parçanın tam altına, ortalı)
            center_x = current_x + (part['w'] / 2)
            text_y_pos1 = current_y - 20.0
            
            name_text = master_msp.add_text(part['name'], dxfattribs={'height': FIXED_TEXT_HEIGHT, 'color': 3})
            name_text.set_placement((center_x, text_y_pos1), align='MIDDLE_CENTER')

            # 2. Satır Yazı: Ölçüler (Dosya adının biraz altına, daha küçük boyutta)
            dim_str = f"{t['w_label']}: {part['w']:.1f} mm  x  {t['h_label']}: {part['h']:.1f} mm"
            text_y_pos2 = text_y_pos1 - (FIXED_TEXT_HEIGHT * 1.5)
            
            dim_text = master_msp.add_text(dim_str, dxfattribs={'height': FIXED_TEXT_HEIGHT * 0.8, 'color': 7})
            dim_text.set_placement((center_x, text_y_pos2), align='MIDDLE_CENTER')

            # Master'a import et
            importer = Importer(part['doc'], master_doc)
            importer.import_modelspace()
            importer.finalize()
            
            # Bir sonraki parça için koordinatları hazırla
            current_x += part['w'] + MARGIN_X
            if part['h'] > max_row_height:
                max_row_height = part['h']

            # İkinci aşama ilerlemesi (50% - 100%)
            progress_bar.progress(0.5 + ((index + 1) / len(parsed_parts) * 0.5))

        # Çıktıyı kaydet
        output_filepath = os.path.join(temp_dir, t['output_filename'])
        master_doc.saveas(output_filepath)
        
        with open(output_filepath, "rb") as file_to_download:
            dxf_data = file_to_download.read()
            
        status_text.empty() # Durum yazısını temizle

        # --- TASARIM & SONUÇLAR ---
        st.markdown("---")
        st.subheader(t['results_title'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric(label=t['metrics_total'], value=f"{len(results_data)}")
        m2.metric(label=t['metrics_max_w'], value=f"{round(max_w_overall,1)} mm")
        m3.metric(label=t['metrics_max_h'], value=f"{round(max_h_overall,1)} mm")
        
        st.write("") 
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(pd.DataFrame(results_data), use_container_width=True, hide_index=True)
            
        with col2:
            st.success(t['success_msg'])
            st.download_button(
                label=t['download_btn'],
                data=dxf_data,
                file_name=t['output_filename'],
                mime="application/dxf",
                type="primary",
                use_container_width=True
            )


