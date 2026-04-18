import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="VDC - Chấm điểm Siêu tốc", layout="wide")

st.title("🚀 HEPC Fast-Grader V0.8")
st.write("Giảng viên: **Trần Công Đẹp** | Cách dùng: Nhìn ảnh và Click vào đáp án đúng")

# --- CẤU HÌNH ---
st.sidebar.header("📝 Đáp án chuẩn")
dap_an_raw = st.sidebar.text_area("Nhập dãy đáp án (VD: ABCD...):", value="ABCD")
DAP_AN_LIST = list(dap_an_raw.upper())

if "kq_hocvien" not in st.session_state:
    st.session_state.kq_hocvien = {}

uploaded_file = st.sidebar.file_uploader("Tải phiếu làm bài...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    col_img, col_control = st.columns([2, 1])
    
    with col_img:
        st.subheader("🖼️ Ảnh bài làm")
        st.image(uploaded_file, use_container_width=True)

    with col_control:
        st.subheader("✍️ Bảng chấm điểm")
        st.info("Nhìn ảnh bên trái và tích vào ô học viên chọn:")
        
        score = 0
        for i, dung in enumerate(DAP_AN_LIST):
            # Tạo 4 nút bấm trên một hàng cho mỗi câu
            st.write(f"**Câu {i+1}** (Đúng: {dung})")
            choice = st.radio(f"Chọn cho câu {i+1}", ["A", "B", "C", "D", "Chưa chọn"], 
                              index=4, horizontal=True, key=f"q_{i}", label_visibility="collapsed")
            
            st.session_state.kq_hocvien[i] = choice
            if choice == dung:
                score += 1
        
        st.divider()
        st.sidebar.metric("TỔNG ĐIỂM", f"{(score/len(DAP_AN_LIST)*10):.2f}/10")
        st.sidebar.success(f"Số câu đúng: {score}/{len(DAP_AN_LIST)}")
        
        if st.button("💾 XUẤT KẾT QUẢ"):
            st.balloons()
            st.write("Đã ghi nhận kết quả vào danh sách!")