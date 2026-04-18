import cv2
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="VDC - HEPC Click Scanner", layout="wide")
st.title("🚀 HEPC Click-Scanner V0.11")
st.write("Giảng viên: **Trần Công Đẹp** | Tính năng: Click 2 điểm để tạo mặt nạ chấm điểm")

# --- QUẢN LÝ TỌA ĐỘ CLICK ---
if "diem_click" not in st.session_state:
    st.session_state.diem_click = []

# --- CẤU HÌNH ---
st.sidebar.header("⚙️ CẤU HÌNH ĐÁP ÁN")
input_dap_an = st.sidebar.text_area("Nhập dãy đáp án (VD: ABCD...):", value="ABCD")
DAP_AN_LIST = list(input_dap_an.upper().replace(" ", ""))

if st.sidebar.button("🔄 Xóa chọn lại tọa độ"):
    st.session_state.diem_click = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("📌 Hướng dẫn: Nhấn vào 2 điểm trên ảnh để tạo khung bao quanh toàn bộ 40 câu.")

uploaded_file = st.sidebar.file_uploader("Tải phiếu làm bài lên...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img_pil = Image.open(uploaded_file).convert("RGB")
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    
    st.subheader("📍 BƯỚC 1: Click chọn 2 góc của bảng trả lời")
    st.write("**Click 1:** Góc trên cùng bên trái (Sát chữ Câu 1)")
    st.write("**Click 2:** Góc dưới cùng bên phải (Sát ô D của Câu 40)")
    
    # Hiển thị ảnh và bắt sự kiện Click chuột
    value = streamlit_image_coordinates(img_pil, key="clicker")
    
    if value is not None:
        toa_do = (value["x"], value["y"])
        # Lưu tọa độ nếu chưa có trong danh sách và chưa quá 2 điểm
        if toa_do not in st.session_state.diem_click and len(st.session_state.diem_click) < 2:
            st.session_state.diem_click.append(toa_do)
            st.rerun()

    # Vẽ các điểm đã click lên ảnh hiển thị
    img_hien_thi = img_cv.copy()
    for pt in st.session_state.diem_click:
        cv2.circle(img_hien_thi, pt, 8, (0, 0, 255), -1)

    if len(st.session_state.diem_click) < 2:
        st.image(img_hien_thi, channels="BGR", use_container_width=True)
        st.warning(f"Đã chấm {len(st.session_state.diem_click)}/2 điểm. Anh hãy click tiếp vào ảnh.")
    
    # --- BƯỚC 2: TỰ ĐỘNG CHIA LƯỚI & CHẤM ĐIỂM ---
    elif len(st.session_state.diem_click) == 2:
        p1, p2 = st.session_state.diem_click
        
        # Xác định tọa độ khung lớn bao quanh cả 2 vùng
        x_min, y_min = min(p1[0], p2[0]), min(p1[1], p2[1])
        x_max, y_max = max(p1[0], p2[0]), max(p1[1], p2[1])
        
        # Vẽ viền xanh lá cho khung lớn
        cv2.rectangle(img_hien_thi, (x_min, y_min), (x_max, y_max), (0, 255, 0), 3)
        
        # Tính toán chia cắt
        chieu_rong_tong = x_max - x_min
        chieu_cao_tong = y_max - y_min
        
        rong_1_vung = chieu_rong_tong / 2 # Chia đôi màn hình cho 2 cột
        chieu_cao_1_cau = chieu_cao_tong / 20 # Bỏ qua header, chia thẳng 20 dòng
        chieu_rong_1_o = rong_1_vung / 5 # 5 cột nhỏ (STT, A, B, C, D)
        
        # Tiền xử lý đếm mực
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        ket_qua = []
        labels = ["A", "B", "C", "D"]
        
        for vung in range(2): # 0 là câu 1-20, 1 là câu 21-40
            x_bat_dau_vung = x_min + (vung * rong_1_vung)
            
            for dong in range(20):
                muc_trong_4_o = []
                for cot_abcd in range(1, 5): # Chỉ lấy cột 1,2,3,4 (Bỏ qua cột 0 là STT)
                    x1 = int(x_bat_dau_vung + cot_abcd * chieu_rong_1_o)
                    y1 = int(y_min + dong * chieu_cao_1_cau)
                    x2 = int(x1 + chieu_rong_1_o)
                    y2 = int(y1 + chieu_cao_1_cau)
                    
                    # Vẽ ô lưới nhỏ màu xanh dương
                    cv2.rectangle(img_hien_thi, (x1, y1), (x2, y2), (255, 0, 0), 1)
                    
                    # Đếm mực trong ô
                    vung_muc = thresh[y1:y2, x1:x2]
                    muc_trong_4_o.append(cv2.countNonZero(vung_muc))
                
                # Ô nào nhiều mực nhất thì ghi nhận
                o_nhieu_muc_nhat = np.argmax(muc_trong_4_o)
                ket_qua.append(labels[o_nhieu_muc_nhat] if muc_trong_4_o[o_nhieu_muc_nhat] > 30 else "Trống")
        
        st.success("Đã áp lưới thành công! Hãy kiểm tra các ô vuông nhỏ màu xanh trên ảnh.")
        st.image(img_hien_thi, channels="BGR", use_container_width=True)
        
        # --- BƯỚC 3: HIỂN THỊ ĐIỂM ---
        st.divider()
        st.subheader("📝 Bảng kết quả")
        score = 0
        cot_hien_thi = st.columns(4)
        for i, res in enumerate(ket_qua[:len(DAP_AN_LIST)]):
            dung = DAP_AN_LIST[i]
            is_ok = (res == dung)
            if is_ok: score += 1
            with cot_hien_thi[i % 4]:
                st.write(f"C{i+1}: **{res}** {'✅' if is_ok else '❌'}")
                
        st.sidebar.metric("TỔNG ĐIỂM", f"{(score/len(DAP_AN_LIST)*10):.2f}/10")
        st.sidebar.write(f"Số câu đúng: {score}/{len(DAP_AN_LIST)}")
