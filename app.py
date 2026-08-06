import streamlit as st
import ezdxf
from ezdxf.addons import Importer
import ezdxf.bbox
import os
import tempfile
import pandas as pd

# Page config
st.set_page_config(page_title="DXF Smart Merger", page_icon="📐", layout="wide")

# Sidebar for AI / Vibecoding credit
with st.sidebar:
    st.markdown("### 🤖 About this App")
    st.markdown("This tool automatically measures and merges 2D DXF drawings exported from CAD software like SolidWorks.")
    st.markdown("---")
    st.markdown("✨ **Built with AI (Vibecoding)**")
    st.markdown("Created through natural language prompting to simplify mechanical workflows.")

# Main Interface
st.title("📐 DXF Smart Merger & Measurer")
st.markdown("Upload your 2D DXF drawings. The system will automatically extract their dimensions (W x H), label them, and merge them into a single DXF file.")

# File Uploader
uploaded_files = st.file_uploader("Upload DXF Files", type=['dxf'], accept_multiple_files=True)

if uploaded_files:
    st.success(f"Successfully loaded {len(uploaded_files)} files. Processing...")
    
    progress_bar = st.progress(0)
    results_data = []

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create Master DXF document
        master_doc = ezdxf.new('R2010') 
        master_msp = master_doc.modelspace()
        
        current_x = 0.0
        current_y = 0.0
        max_row_height = 0.0
        margin = 50.0 # Margin between drawings (mm)
        max_width = 1500.0 # Maximum width before moving to a new row

        for index, file in enumerate(uploaded_files):
            temp_filepath = os.path.join(temp_dir, file.name)
            with open(temp_filepath, "wb") as f:
                f.write(file.getbuffer())
                
            try:
                # Read DXF and calculate bounding box
                doc = ezdxf.readfile(temp_filepath)
                msp = doc.modelspace()
                bbox = ezdxf.bbox.extents(msp)
                
                if bbox.has_data:
                    min_x, min_y, _ = bbox.extmin
                    max_x, max_y, _ = bbox.extmax
                    
                    width = max_x - min_x
                    height = max_y - min_y
                    
                    results_data.append({
                        "File Name": file.name, 
                        "Width (mm)": round(width, 1), 
                        "Height (mm)": round(height, 1)
                    })
                    
                    # Layout logic (Simple Nesting)
                    if current_x + width > max_width and current_x > 0:
                        current_x = 0
                        current_y += max_row_height + margin
                        max_row_height = 0
                        
                    target_x = current_x
                    target_y = current_y
                    
                    offset_x = target_x - min_x
                    offset_y = target_y - min_y
                    
                    # Move entities to target location
                    for entity in msp:
                        if hasattr(entity, 'translate'):
                            entity.translate(offset_x, offset_y, 0)
                            
                    # Add Text Label (Filename and Dimensions)
                    text_content = f"{file.name}\nW: {width:.1f} mm\nH: {height:.1f} mm"
                    text_height = max(10.0, height * 0.05)
                    master_msp.add_text(
                        text_content, 
                        dxfattribs={'height': text_height, 'color': 3}
                    ).set_placement((target_x, target_y + height + (margin / 2)))

                    # Import to master document
                    importer = Importer(doc, master_doc)
                    importer.import_modelspace()
                    importer.finalize()
                    
                    current_x += width + margin
                    max_row_height = max(max_row_height, height)
                    
            except Exception as e:
                st.error(f"Error processing {file.name}: {str(e)}")
            
            progress_bar.progress((index + 1) / len(uploaded_files))

        # Save the merged master file
        output_filename = "Merged_Drawings.dxf"
        output_filepath = os.path.join(temp_dir, output_filename)
        master_doc.saveas(output_filepath)
        
        with open(output_filepath, "rb") as file_to_download:
            dxf_data = file_to_download.read()

        st.markdown("---")
        st.subheader("📊 Analysis Results")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.dataframe(pd.DataFrame(results_data), use_container_width=True)
            
        with col2:
            st.success("All drawings have been successfully merged!")
            st.download_button(
                label="📥 Download Merged DXF",
                data=dxf_data,
                file_name=output_filename,
                mime="application/dxf",
                type="primary"
            )


