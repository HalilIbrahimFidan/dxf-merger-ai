import streamlit as st
import ezdxf
from ezdxf.addons import Importer
import ezdxf.bbox
import os
import tempfile
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="DXF Smart Merger", page_icon="📐", layout="wide")

# --- DİL SÖZLÜĞÜ (TRANSLATIONS) ---
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
        "metrics_max_h": "Max Height"
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
        "metrics_max_h": "Maksimum Yükseklik"
    }
}

# --- SOL MENÜ (SIDEBAR) & DİL SEÇİMİ ---
with st.sidebar:
    st.header("🌐 Language / Dil")
    selected_lang = st.radio("", ["🇬🇧 English", "🇹🇷 Türkçe"], label_visibility="collapsed")
    
    # Seçilen dile göre dictionary anahtarını belirle
    lang = "tr" if "Türkçe" in selected_lang else "en"
    t = locales[lang]

    st.markdown("---")
    st.markdown(f"### {t['about_title']}")
    st.info(t['about_text'])
    st.markdown(t['vibecoding'])

# --- ANA EKRAN (MAIN UI) ---
st.title(t['title'])
st.markdown(f"*{t['subtitle']}*")
st.markdown("---")

uploaded_files = st.file_uploader(t['upload_label'], type=['dxf'], accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)} {t['processing']}")
    progress_bar = st.progress(0)
    
    results_data = []
    max_w_overall = 0.0
    max_h_overall = 0.0

    with tempfile.TemporaryDirectory() as temp_dir:
        master_doc = ezdxf.new('R2010') 
        master_msp = master_doc.modelspace()
        
        current_x = 0.0
        current_y = 0.0
        max_row_height = 0.0
        margin = 50.0 
        max_width = 1500.0 

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
                    
                    width = max_x - min_x
                    height = max_y - min_y
                    
                    # İstatistikleri güncelle
                    if width > max_w_overall: max_w_overall = width
                    if height > max_h_overall: max_h_overall = height
                    
                    results_data.append({
                        t['table_filename']: file.name, 
                        t['table_width']: round(width, 1), 
                        t['table_height']: round(height, 1)
                    })
                    
                    if current_x + width > max_width and current_x > 0:
                        current_x = 0
                        current_y += max_row_height + margin
                        max_row_height = 0
                        
                    target_x = current_x
                    target_y = current_y
                    
                    offset_x = target_x - min_x
                    offset_y = target_y - min_y
                    
                    for entity in msp:
                        if hasattr(entity, 'translate'):
                            entity.translate(offset_x, offset_y, 0)
                            
                    # Dinamik metin (Dile göre G/Y veya W/H)
                    text_content = f"{file.name}\n{t['w_label']}: {width:.1f} mm\n{t['h_label']}: {height:.1f} mm"
                    text_height = max(10.0, height * 0.05)
                    master_msp.add_text(
                        text_content, 
                        dxfattribs={'height': text_height, 'color': 3}
                    ).set_placement((target_x, target_y + height + (margin / 2)))

                    importer = Importer(doc, master_doc)
                    importer.import_modelspace()
                    importer.finalize()
                    
                    current_x += width + margin
                    max_row_height = max(max_row_height, height)
                    
            except Exception as e:
                st.error(f"{t['error_msg']} {file.name}: {str(e)}")
            
            progress_bar.progress((index + 1) / len(uploaded_files))

        output_filepath = os.path.join(temp_dir, t['output_filename'])
        master_doc.saveas(output_filepath)
        
        with open(output_filepath, "rb") as file_to_download:
            dxf_data = file_to_download.read()

        # --- TASARIM GÜNCELLEMELERİ (METRİKLER) ---
        st.markdown("---")
        st.subheader(t['results_title'])
        
        # Üst kısıma havalı özet kutuları (Metrics) ekliyoruz
        m1, m2, m3 = st.columns(3)
        m1.metric(label=t['metrics_total'], value=f"{len(results_data)}")
        m2.metric(label=t['metrics_max_w'], value=f"{round(max_w_overall,1)} mm")
        m3.metric(label=t['metrics_max_h'], value=f"{round(max_h_overall,1)} mm")
        
        st.write("") # Boşluk
        
        # Alt kısımda tablo ve indirme butonu
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


