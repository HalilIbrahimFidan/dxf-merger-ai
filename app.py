import streamlit as st
import ezdxf
from ezdxf.addons import Importer
import ezdxf.bbox
from ezdxf.enums import TextEntityAlignment
import os
import tempfile
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="DXF Smart Merger", page_icon="📐", layout="wide")

# --- DİL SÖZLÜĞÜ ---
locales = {
    "en": {
        "title": "📐 DXF Smart Merger & Measurer",
        "subtitle": "Upload 2D DXF files. The system creates dimension lines and multi-line production labels (Code, Qty, Thickness, Material) from filenames.",
        "settings": "⚙️ Settings",
        "lang_select": "🌐 Language / Dil",
        "about_title": "🤖 About this App",
        "about_text": "Built for sheet metal and CNC operations. Name your files like 'Code_Qty_Thickness_Material.dxf' (e.g., 103-01-008_5_2_Steel.dxf) for auto-labeling.",
        "vibecoding": "✨ **Built with AI (Vibecoding)**",
        "upload_label": "Upload DXF Files here",
        "processing": "files loaded. Processing...",
        "table_filename": "File Name",
        "table_width": "Width (mm)",
        "table_height": "Height (mm)",
        "error_msg": "Error processing",
        "results_title": "📊 Analysis Results",
        "success_msg": "All drawings merged with dimensions and production labels!",
        "download_btn": "📥 Download Merged DXF",
        "output_filename": "Merged_Drawings.dxf",
        "metrics_total": "Total Files",
        "metrics_max_w": "Max Width",
        "metrics_max_h": "Max Height",
        "step_1": "Analyzing and sorting files...",
        "step_2": "Generating dimension lines and labels..."
    },
    "tr": {
        "title": "📐 DXF Akıllı Birleştirici (Üretim Modu)",
        "subtitle": "2D DXF çizimlerinizi yükleyin. Sistem ölçülendirme okları ekler ve dosya adından (Kod_Adet_Kalınlık_Malzeme) üretim etiketlerini oluşturur.",
        "settings": "⚙️ Ayarlar",
        "lang_select": "🌐 Dil / Language",
        "about_title": "🤖 Bu Uygulama Hakkında",
        "about_text": "Lazer kesim otomasyonu için tasarlanmıştır. Otomatik etiketleme için dosyalarınızı 'Kod_Adet_Kalınlık_Malzeme.dxf' şeklinde isimlendirin. (Örn: 103-01-008_1_1.5_DKPSac.dxf)",
        "vibecoding": "✨ **Yapay Zeka (Vibecoding) ile üretildi**",
        "upload_label": "DXF Dosyalarını Buraya Yükleyin",
        "processing": "adet dosya yüklendi. İşlem başlatılıyor...",
        "table_filename": "Dosya Adı",
        "table_width": "Genişlik (mm)",
        "table_height": "Yükseklik (mm)",
        "error_msg": "İşlenirken hata oluştu",
        "results_title": "📊 Analiz Sonuçları",
        "success_msg": "Tüm çizimler ölçülendirildi ve üretim etiketleriyle birleştirildi!",
        "download_btn": "📥 Birleştirilmiş DXF'i İndir",
        "output_filename": "Birlestirilmis_Cizimler.dxf",
        "metrics_total": "Toplam Dosya",
        "metrics_max_w": "Maksimum Genişlik",
        "metrics_max_h": "Maksimum Yükseklik",
        "step_1": "Dosyalar analiz ediliyor ve boylarına göre sıralanıyor...",
        "step_2": "Çizimler birleştiriliyor, ölçü ve etiketler ekleniyor..."
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

st.warning("💡 **İpucu:** Çizimlerin altına üretim bilgilerinin otomatik yazılması için dosyalarınızı şu formatta isimlendirin: **Kod_Adet_Kalınlık_Malzeme** (Örnek: `103-01-008_10_1.5_DKPSac.dxf`)")

uploaded_files = st.file_uploader(t['upload_label'], type=['dxf'], accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)} {t['processing']}")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # --- YERLEŞİM (LAYOUT) AYARLARI ---
    MARGIN_X = 200.0          
    MARGIN_Y = 350.0  # Alt alta 3 satır yazı ve ölçü okları geleceği için boşluk iyice artırıldı
    MAX_ROW_WIDTH = 2500.0    

    results_data = []
    parsed_parts = []
    max_w_overall = 0.0
    max_h_overall = 0.0

    with tempfile.TemporaryDirectory() as temp_dir:
        # AŞAMA 1: Oku ve Sırala
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
            
            progress_bar.progress((index + 1) / len(uploaded_files) * 0.5)

        parsed_parts.sort(key=lambda item: item['h'], reverse=True)

        # AŞAMA 2: Dizilim, Gerçek Ölçülendirme ve Üretim Etiketleri
        status_text.text(t['step_2'])
        master_doc = ezdxf.new('R2010') 
        master_msp = master_doc.modelspace()
        
        current_x = 0.0
        current_y = 0.0
        max_row_height = 0.0

        for index, part in enumerate(parsed_parts):
            w = part['w']
            h = part['h']

            if current_x + w > MAX_ROW_WIDTH and current_x > 0:
                current_x = 0.0
                current_y -= (max_row_height + MARGIN_Y)
                max_row_height = 0.0
                
            offset_x = current_x - part['min_x']
            offset_y = current_y - part['min_y']
            
            for entity in part['doc'].modelspace():
                if hasattr(entity, 'translate'):
                    entity.translate(offset_x, offset_y, 0)
            
            importer = Importer(part['doc'], master_doc)
            importer.import_modelspace()
            importer.finalize()

            # --- DİNAMİK BOYUTLAR ---
            dynamic_text_height = max(5.0, min(w * 0.05, 25.0))
            dim_offset_x = max(20.0, w * 0.1)
            dim_offset_y = max(20.0, h * 0.1)

            dim_overrides = {
                "dimtxt": dynamic_text_height * 0.8,
                "dimgap": dynamic_text_height * 0.3,
                "dimexe": dynamic_text_height * 0.4,
                "dimexo": dynamic_text_height * 0.4,
                "dimclrd": 3,  # Yeşil ölçü okları
                "dimclre": 3,
                "dimclrt": 7,  # Beyaz ölçü yazısı
                "dimdec": 1
            }

            # 1. YATAY ÖLÇÜLENDİRME
            dim_w = master_msp.add_linear_dim(
                base=(current_x + (w/2), current_y - dim_offset_y), 
                p1=(current_x, current_y), 
                p2=(current_x + w, current_y),
                override=dim_overrides
            )
            dim_w.render()

            # 2. DİKEY ÖLÇÜLENDİRME
            dim_h = master_msp.add_linear_dim(
                base=(current_x + w + dim_offset_x, current_y + (h/2)), 
                p1=(current_x + w, current_y), 
                p2=(current_x + w, current_y + h),
                angle=90,
                override=dim_overrides
            )
            dim_h.render()
                    
            # 3. ÇOK SATIRLI ÜRETİM ETİKETİ (Kod - Adet/Kalınlık - Malzeme)
            display_name = os.path.splitext(part['name'])[0]
            file_parts = display_name.split('_')
            
            # Alt çizgi ile ayrılmış 4 veri varsa parçala
            if len(file_parts) >= 4:
                line1_str = file_parts[0]  # Kod
                
                # Adet ve mm kelimeleri yoksa otomatik ekle
                adet_val = file_parts[1] if "adet" in file_parts[1].lower() else f"{file_parts[1]}Adet"
                kalinlik_val = file_parts[2] if "mm" in file_parts[2].lower() else f"{file_parts[2]}mm"
                
                line2_str = f"{adet_val} / {kalinlik_val}"
                line3_str = file_parts[3]  # Malzeme
            else:
                # İsimlendirme kuralına uyulmamışsa şablon göster
                line1_str = display_name
                line2_str = "? Adet / ? mm"
                line3_str = "Belirtilmedi"

            # Yazıların Y pozisyonları (Alt alta hizalama)
            line1_y = current_y - dim_offset_y - (dynamic_text_height * 2.5)
            line2_y = line1_y - (dynamic_text_height * 1.5)
            line3_y = line2_y - (dynamic_text_height * 1.5)
            
            center_x = current_x + (w / 2)

            # 1. Satır: Kod (Sarı Renk = 2)
            txt1 = master_msp.add_text(line1_str, dxfattribs={'height': dynamic_text_height, 'color': 2})
            txt1.set_placement((center_x, line1_y), align=TextEntityAlignment.MIDDLE_CENTER)

            # 2. Satır: Adet ve Kalınlık (Beyaz Renk = 7)
            txt2 = master_msp.add_text(line2_str, dxfattribs={'height': dynamic_text_height * 0.9, 'color': 7})
            txt2.set_placement((center_x, line2_y), align=TextEntityAlignment.MIDDLE_CENTER)

            # 3. Satır: Malzeme (Turkuaz Renk = 4)
            txt3 = master_msp.add_text(line3_str, dxfattribs={'height': dynamic_text_height * 0.9, 'color': 4})
            txt3.set_placement((center_x, line3_y), align=TextEntityAlignment.MIDDLE_CENTER)
            
            current_x += w + MARGIN_X
            if h > max_row_height:
                max_row_height = h

            progress_bar.progress(0.5 + ((index + 1) / len(parsed_parts) * 0.5))

        output_filepath = os.path.join(temp_dir, t['output_filename'])
        master_doc.saveas(output_filepath)
        
        with open(output_filepath, "rb") as file_to_download:
            dxf_data = file_to_download.read()
            
        status_text.empty()

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


