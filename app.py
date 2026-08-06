import streamlit as st
import ezdxf
from ezdxf.addons import Importer
import ezdxf.bbox
from ezdxf.enums import TextEntityAlignment
import os
import tempfile
import pandas as pd
import math

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="DXF Smart Merger", page_icon="📐", layout="wide")

# --- DİL SÖZLÜĞÜ ---
locales = {
    "en": {
        "title": "📐 DXF Smart Merger (Multi-Page & Outer Dims)",
        "subtitle": "Auto-paginates shapes into multiple A4 frames. Dimensions are on the outside, production texts strictly inside.",
        "settings": "⚙️ Settings",
        "lang_select": "🌐 Language / Dil",
        "about_title": "🤖 About this App",
        "about_text": "Built for CNC & Laser cutting. Files are automatically grouped into printable A4 frames. Name format: 'Code_Qty_Thickness_Material.dxf'.",
        "vibecoding": "✨ **Built with AI (Vibecoding)**",
        "upload_label": "Upload DXF Files here",
        "processing": "files loaded. Processing...",
        "table_filename": "File Name",
        "table_width": "W (mm)",
        "table_height": "H (mm)",
        "error_msg": "Error processing",
        "results_title": "📊 Analysis Results",
        "success_msg": "All drawings merged and grouped into A4 pages successfully!",
        "download_btn": "📥 Download Merged DXF",
        "output_filename": "Merged_MultiPage_A4.dxf",
        "metrics_total": "Total Files",
        "metrics_max_w": "Max Width",
        "metrics_max_h": "Max Height",
        "step_1": "Analyzing boundaries...",
        "step_2": "Generating A4 frames, outer dimensions, and inner labels..."
    },
    "tr": {
        "title": "📐 DXF Akıllı Birleştirici (Çoklu A4 ve Dış Ölçü)",
        "subtitle": "Parçalar A4 sayfalarına gruplanır. Ölçü okları şeklin DIŞINDA, üretim etiketleri ise şeklin İÇİNDE yer alır.",
        "settings": "⚙️ Ayarlar",
        "lang_select": "🌐 Dil / Language",
        "about_title": "🤖 Bu Uygulama Hakkında",
        "about_text": "Lazer kesim otomasyonu için tasarlanmıştır. Çıktı almayı kolaylaştırmak için sanal A4 sayfaları oluşturur.",
        "vibecoding": "✨ **Yapay Zeka (Vibecoding) ile üretildi**",
        "upload_label": "DXF Dosyalarını Buraya Yükleyin",
        "processing": "adet dosya yüklendi. İşlem başlatılıyor...",
        "table_filename": "Dosya Adı",
        "table_width": "Gen. (mm)",
        "table_height": "Yük. (mm)",
        "error_msg": "İşlenirken hata oluştu",
        "results_title": "📊 Analiz Sonuçları",
        "success_msg": "Tüm çizimler başarıyla A4 sayfalarına gruplandırıldı!",
        "download_btn": "📥 Birleştirilmiş DXF'i İndir",
        "output_filename": "Birlestirilmis_Coklu_A4.dxf",
        "metrics_total": "Toplam Dosya",
        "metrics_max_w": "Maks. Genişlik",
        "metrics_max_h": "Maks. Yükseklik",
        "step_1": "Sınırlar analiz ediliyor...",
        "step_2": "A4 Sayfaları oluşturuluyor, dış ölçüler ve iç etiketler işleniyor..."
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
st.warning("💡 **Dış Ölçülendirme & Sayfalama:** Ölçü okları şekillerin dışına (alt ve sağ) yerleştirilir. Çakışma olmaması için aralara otomatik pay bırakılır. Sayfa dolduğunda yeni bir A4 çerçevesi (Kırmızı Kutu) açılır.")

uploaded_files = st.file_uploader(t['upload_label'], type=['dxf'], accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)} {t['processing']}")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # --- YERLEŞİM AYARLARI ---
    BASE_MARGIN = 40.0 # Ölçü okları dışarıda olacağı için parçalar arasına 40mm baz boşluk bırakıyoruz
    
    results_data = []
    parsed_parts = []
    max_w_overall = 0.0
    max_h_overall = 0.0

    with tempfile.TemporaryDirectory() as temp_dir:
        # AŞAMA 1: Oku, Sınırları Belirle
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
                        "min_y": min_y,
                        "max_y": max_y
                    })
                    
                    results_data.append({
                        t['table_filename']: file.name, 
                        t['table_width']: round(w, 1), 
                        t['table_height']: round(h, 1)
                    })
            except Exception as e:
                st.error(f"{t['error_msg']} {file.name}: {str(e)}")
            
            progress_bar.progress((index + 1) / len(uploaded_files) * 0.3)

        # Matris düzeni için Yüksekliğe göre büyükten küçüğe sırala
        parsed_parts.sort(key=lambda item: item['h'], reverse=True)

        # --- A4 ÇERÇEVE (SAYFA) MATEMATİĞİ ---
        # En büyük parça dış ölçüleriyle beraber sayfaya sığmalı
        min_page_w = max(2970.0, max_w_overall + (BASE_MARGIN * 4))
        min_page_h = max(2100.0, max_h_overall + (BASE_MARGIN * 4))
        
        PAGE_H = max(min_page_h, min_page_w / 1.414)
        PAGE_W = PAGE_H * 1.414
        PAGE_GAP = PAGE_W * 0.10 # İki A4 sayfası arasındaki yatay boşluk

        # AŞAMA 2: Dizilim, DIŞ ÖLÇÜLENDİRME ve İÇ ETİKETLER
        status_text.text(t['step_2'])
        master_doc = ezdxf.new('R2010') 
        master_msp = master_doc.modelspace()
        
        page_idx = 0
        page_start_x = 0.0
        
        current_x = page_start_x + BASE_MARGIN
        current_y = -BASE_MARGIN
        max_row_height = 0.0

        for index, part in enumerate(parsed_parts):
            w = part['w']
            h = part['h']

            # Dinamik Font (Şeklin içine sığacak kadar)
            max_font_by_width = w / 15.0
            max_font_by_height = h / 8.0
            font_size = max(1.0, min(max_font_by_width, max_font_by_height))
            
            # Dinamik Boşluklar (Dışarıdaki ölçü oklarına yetecek kadar ekstra pay)
            part_spacing_x = max(BASE_MARGIN, font_size * 4)
            part_spacing_y = max(BASE_MARGIN, font_size * 4)

            # 1. SATIR TAŞMA KONTROLÜ
            if current_x + w + part_spacing_x > page_start_x + PAGE_W - BASE_MARGIN and current_x > page_start_x + BASE_MARGIN:
                current_x = page_start_x + BASE_MARGIN
                current_y -= max_row_height
                max_row_height = 0.0
                
            # 2. SAYFA TAŞMA KONTROLÜ
            if current_y - h - part_spacing_y < -PAGE_H + BASE_MARGIN and (current_x > page_start_x + BASE_MARGIN or current_y < -BASE_MARGIN):
                page_idx += 1
                page_start_x = page_idx * (PAGE_W + PAGE_GAP)
                current_x = page_start_x + BASE_MARGIN
                current_y = -BASE_MARGIN
                max_row_height = 0.0
                
            # PARÇAYI TAŞIMA (Top-Down)
            offset_x = current_x - part['min_x']
            offset_y = current_y - part['max_y'] 
            
            for entity in part['doc'].modelspace():
                if hasattr(entity, 'translate'):
                    entity.translate(offset_x, offset_y, 0)
            
            importer = Importer(part['doc'], master_doc)
            importer.import_modelspace()
            importer.finalize()

            # --- DIŞA DOĞRU ÖLÇÜLENDİRME ---
            dim_offset = font_size * 2.5 # Oklar şeklin DIŞINDAN ne kadar uzakta dursun
            
            dim_overrides = {
                "dimtxt": font_size * 0.9,
                "dimgap": font_size * 0.3,
                "dimexe": font_size * 0.2, 
                "dimexo": font_size * 0.2,
                "dimclrd": 3,
                "dimclre": 3,
                "dimclrt": 7,
                "dimdec": 1
            }

            # 1. YATAY ÖLÇÜ (Parçanın alt çeperinden DIŞARI doğru - Aşağı bakar)
            dim_w = master_msp.add_linear_dim(
                base=(current_x + (w/2), (current_y - h) - dim_offset), 
                p1=(current_x, current_y - h), 
                p2=(current_x + w, current_y - h),
                override=dim_overrides
            )
            dim_w.render()

            # 2. DİKEY ÖLÇÜ (Parçanın sağ çeperinden DIŞARI doğru - Sağa bakar)
            dim_h = master_msp.add_linear_dim(
                base=(current_x + w + dim_offset, current_y - (h/2)), 
                p1=(current_x + w, current_y), 
                p2=(current_x + w, current_y - h),
                angle=90,
                override=dim_overrides
            )
            dim_h.render()
                    
            # --- ŞEKLİN TAM MERKEZİNE YAZILACAK ÜRETİM ETİKETLERİ ---
            display_name = os.path.splitext(part['name'])[0]
            file_parts = display_name.split('_')
            
            if len(file_parts) >= 4:
                line1_str = file_parts[0]
                adet_val = file_parts[1] if "adet" in file_parts[1].lower() else f"{file_parts[1]}Adet"
                kalinlik_val = file_parts[2] if "mm" in file_parts[2].lower() else f"{file_parts[2]}mm"
                line2_str = f"{adet_val} / {kalinlik_val}"
                line3_str = file_parts[3]
            else:
                line1_str = display_name
                line2_str = " "
                line3_str = " "

            # Şeklin Mutlak Merkezi (İç Etiket)
            center_x = current_x + (w / 2)
            center_y = current_y - (h / 2)

            line1_y = center_y + (font_size * 1.5)
            line2_y = center_y
            line3_y = center_y - (font_size * 1.5)
            
            master_msp.add_text(line1_str, dxfattribs={'height': font_size, 'color': 2}).set_placement((center_x, line1_y), align=TextEntityAlignment.MIDDLE_CENTER)
            
            if line2_str.strip():
                master_msp.add_text(line2_str, dxfattribs={'height': font_size * 0.9, 'color': 7}).set_placement((center_x, line2_y), align=TextEntityAlignment.MIDDLE_CENTER)
            if line3_str.strip():
                master_msp.add_text(line3_str, dxfattribs={'height': font_size * 0.9, 'color': 4}).set_placement((center_x, line3_y), align=TextEntityAlignment.MIDDLE_CENTER)
            
            # Bir Sonraki Parça İçin X'i ve Satır Yüksekliğini Güncelle
            current_x += w + part_spacing_x
            max_row_height = max(max_row_height, h + part_spacing_y)

            progress_bar.progress(0.3 + ((index + 1) / len(parsed_parts) * 0.7))

        # --- A4 ÇERÇEVELERİNİ ÇİZME (KIRMIZI KILAVUZ) ---
        for p in range(page_idx + 1):
            px = p * (PAGE_W + PAGE_GAP)
            # Kırmızı Renkte A4 Çerçevesi (1 = Kırmızı)
            frame_points = [(px, 0), (px + PAGE_W, 0), (px + PAGE_W, -PAGE_H), (px, -PAGE_H), (px, 0)]
            master_msp.add_lwpolyline(frame_points, dxfattribs={'color': 1})
            
            # Sayfa Başlığı (Tepede ortalanmış)
            master_msp.add_text(f"SAYFA {p+1}", dxfattribs={'height': PAGE_H * 0.02, 'color': 2}).set_placement((px + PAGE_W/2, PAGE_H * 0.02), align=TextEntityAlignment.BOTTOM_CENTER)

        # Çıktıyı Kaydet
        output_filepath = os.path.join(temp_dir, t['output_filename'])
        master_doc.saveas(output_filepath)
        
        with open(output_filepath, "rb") as file_to_download:
            dxf_data = file_to_download.read()
            
        status_text.empty()

        # --- TASARIM & SONUÇLAR ---
        st.markdown("---")
        st.subheader(t['results_title'])
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(label=t['metrics_total'], value=f"{len(results_data)}")
        m2.metric(label="Oluşturulan A4 Sayfası", value=f"{page_idx + 1} Adet")
        m3.metric(label=t['metrics_max_w'], value=f"{round(max_w_overall,1)} mm")
        m4.metric(label=t['metrics_max_h'], value=f"{round(max_h_overall,1)} mm")
        
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


