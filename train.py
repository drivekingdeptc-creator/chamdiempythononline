import cv2
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="VDC - HEPC Scanner V0.12", layout="wide")
st.title("🚀 HEPC Click-Scanner V0.12")
st.write("Giảng viên: **Trần Công Đẹp** | Tính năng: Định vị 4 điểm cho 2 vùng & Tự động lưu tọa độ")

# --- KHỞI TẠO LƯU TRỮ TỌA ĐỘ ---
if "diem_click" not in st.session_state:
    st.session_state.diem_click = []

# --- CẤU HÌNH ---
st.sidebar.header("⚙️ CẤU HÌNH ĐÁP ÁN")
input_dap_an = st.sidebar.text_area("Nhập dãy đáp án chuẩn:", value="ABCD")
DAP_AN_LIST = list(input_dap_an.upper().replace(" ", ""))

if st.sidebar.button("🔄 Xóa tọa độ (Làm mới lưới)"):
    st.session_state.diem_click = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 **Mẹo chấm 77 bài siêu tốc:** Anh chỉ cần click 4 điểm cho bài ĐẦU TIÊN. Các bài sau chỉ cần tải ảnh lên, máy sẽ tự áp dụng lại tọa độ cũ và chấm điểm ngay lập tức!")

uploaded_file = st.sidebar.file_uploader("Tải phiếu làm bài lên...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img_pil = Image.open(uploaded_file).convert("RGB")
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    img_hien_thi = img_cv.copy()
    
    # --- BƯỚC 1: LẤY 4 ĐIỂM TỌA ĐỘ (CHỈ LÀM LẦN ĐẦU) ---
    if len(st.session_state.diem_click) < 4:
        st.subheader("📍 CHẾ ĐỘ THIẾT LẬP LƯỚI: Click chọn 4 điểm")
        st.markdown("""
        **VÙNG 1 (Câu 1-20):**
        1️⃣ Góc TRÊN-TRÁI
        2️⃣ Góc DƯỚI-PHẢI
        
        **VÙNG 2 (Câu 21-40):**
        3️⃣ Góc TRÊN-TRÁI
        4️⃣ Góc DƯỚI-PHẢI
        """)
        
        # Bắt tọa độ click, thay đổi key để component cập nhật đúng
        value = streamlit_image_coordinates(img_pil, key=f"clicker_{len(st.session_state.diem_click)}")
        
        if value is not None:
            toa_do = (value["x"], value["y"])
            if toa_do not in st.session_state.diem_click:
                st.session_state.diem_click.append(toa_do)
                st.rerun()

        # Vẽ chấm đỏ để theo dõi
        for idx, pt in enumerate(st.session_state.diem_click):
            cv2.circle(img_hien_thi, pt, 8, (0, 0, 255), -1)
            cv2.putText(img_hien_thi, str(idx+1), (pt[0]+10, pt[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

        st.image(img_hien_thi, channels="BGR", use_container_width=True)
        st.warning(f"⏳ Đang ghi nhận... Đã chọn {len(st.session_state.diem_click)}/4 điểm.")

    # --- BƯỚC 2: ĐÃ CÓ TỌA ĐỘ -> TỰ ĐỘNG CHIA LƯỚI VÀ CHẤM ---
    else:
        p1, p2, p3, p4 = st.session_state.diem_click
        
        # Lấy thông số Vùng 1
        v1_x_min, v1_y_min = min(p1[0], p2[0]), min(p1[1], p2[1])
        v1_x_max, v1_y_max = max(p1[0], p2[0]), max(p1[1], p2[1])
        v1_w = v1_x_max - v1_x_min
        v1_h = v1_y_max - v1_y_min
        
        # Lấy thông số Vùng 2
        v2_x_min, v2_y_min = min(p3[0], p4[0]), min(p3[1], p4[1])
        v2_x_max, v2_y_max = max(p3[0], p4[0]), max(p3[1], p4[1])
        v2_w = v2_x_max - v2_x_min
        v2_h = v2_y_max - v2_y_min
        
        # Vẽ khung lớn ngoài cùng
        cv2.rectangle(img_hien_thi, (v1_x_min, v1_y_min), (v1_x_max, v1_y_max), (0, 255, 0), 3)
        cv2.rectangle(img_hien_thi, (v2_x_min, v2_y_min), (v2_x_max, v2_y_max), (0, 255, 0), 3)

        # Tiền xử lý đếm mực
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        ket_qua = []
        labels = ["A", "B", "C", "D"]
        
        danh_sach_vung = [
            {"x": v1_x_min, "y": v1_y_min, "w": v1_w, "h": v1_h},
            {"x": v2_x_min, "y": v2_y_min, "w": v2_w, "h": v2_h}
        ]
        
        for vung in danh_sach_vung:
            chieu_cao_1_cau = vung['h'] / 20
            chieu_rong_1_o = vung['w'] / 5 # 5 cột (STT, A, B, C, D)
            
            for dong in range(20):
                muc_trong_4_o = []
                for cot_abcd in range(1, 5): # Quét cột A, B, C, D
                    x1 = int(vung['x'] + cot_abcd * chieu_rong_1_o)
                    y1 = int(vung['y'] + dong * chieu_cao_1_cau)
                    x2 = int(x1 + chieu_rong_1_o)
                    y2 = int(y1 + chieu_cao_1_cau)
                    
                    # Vẽ lưới nhỏ màu xanh dương
                    cv2.rectangle(img_hien_thi, (x1, y1), (x2, y2), (255, 0, 0), 1)
                    
                    vung_muc = thresh[y1:y2, x1:x2]
                    muc_trong_4_o.append(cv2.countNonZero(vung_muc))
                
                o_nhieu_muc_nhat = np.argmax(muc_trong_4_o)
                ket_qua.append(labels[o_nhieu_muc_nhat] if muc_trong_4_o[o_nhieu_muc_nhat] > 30 else "Trống")
        
        # --- HIỂN THỊ KẾT QUẢ ---
        col_img, col_res = st.columns([1, 1])
        with col_img:
            st.success("✅ Đã áp dụng lưới tọa độ tự động!")
            st.image(img_hien_thi, channels="BGR", use_container_width=True)
            
        with col_res:
            st.subheader("📝 Bảng kết quả")
            score = 0
            cot_hien_thi = st.columns(4)
            for i, res in enumerate(ket_qua[:len(DAP_AN_LIST)]):
                dung = DAP_AN_LIST[i]
                is_ok = (res == dung)
                if is_ok: score += 1
                with cot_hien_thi[i % 4]:
                    st.write(f"C{i+1}: **{res}** {'✅' if is_ok else '❌'}")
                    
            st.metric("TỔNG ĐIỂM", f"{(score/len(DAP_AN_LIST)*10):.2f}/10", f"Số câu đúng: {score}/{len(DAP_AN_LIST)}")
