import cv2
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="VDC - HEPC Scanner V0.17", layout="wide")
st.title("🚀 HEPC Click-Scanner V0.17")
st.write("Giảng viên: **Trần Công Đẹp** | Tính năng: Tự động khóa khung giấy cỡ lớn (>70%)")

# --- HÀM HỖ TRỢ BẺ PHẲNG ---
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmin(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

# --- KHỞI TẠO LƯU TRỮ ---
if "diem_click" not in st.session_state:
    st.session_state.diem_click = []

st.sidebar.header("⚙️ CẤU HÌNH HỆ THỐNG")
input_dap_an = st.sidebar.text_area("Nhập dãy đáp án chuẩn:", value="ABCD")
DAP_AN_LIST = list(input_dap_an.upper().replace(" ", ""))

nguong_muc = st.sidebar.slider("Độ nhạy nét mực", 10, 100, 30)

bat_cat_tu_dong = st.sidebar.checkbox("✂️ Bật tự động cắt mép giấy (Phiếu >70% ảnh)", value=True)

if st.sidebar.button("🔄 Xóa tọa độ (Làm mới lưới)"):
    st.session_state.diem_click = []
    st.rerun()

uploaded_file = st.sidebar.file_uploader("Tải phiếu làm bài lên...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img_pil = Image.open(uploaded_file).convert("RGB")
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    h_orig, w_orig = img_cv.shape[:2]
    dien_tich_anh = h_orig * w_orig
    
    img_xuly = img_cv.copy()
    
    # --- BƯỚC 0: CẮT VIỀN (ÁP DỤNG QUY LUẬT 70% CỦA ANH ĐẸP) ---
    if bat_cat_tu_dong:
        gray_full = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray_full, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        paper_contour = None
        for c in contours:
            # SỬA LỖI THEO THỰC TẾ: Khung bắt buộc phải chiếm trên 60% diện tích tấm ảnh (chừa hao 10% cho anh Đẹp thao tác)
            if cv2.contourArea(c) < (dien_tich_anh * 0.60):
                continue
                
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                paper_contour = approx
                break
                
        if paper_contour is not None:
            img_xuly = four_point_transform(img_cv, paper_contour.reshape(4, 2))
            st.toast("✂️ Đã tìm thấy viền giấy lớn và bẻ phẳng!", icon="✅")
        else:
            st.toast("⚠️ Tờ giấy không đủ to (chiếm < 60% ảnh). Đang giữ nguyên ảnh gốc.", icon="⚠️")

    # Hiển thị ảnh (đã cắt hoặc giữ nguyên)
    img_hien_thi = img_xuly.copy()
    img_pil_xuly = Image.fromarray(cv2.cvtColor(img_xuly, cv2.COLOR_BGR2RGB))
    
    # --- BƯỚC 1: CLICK 4 ĐIỂM ---
    if len(st.session_state.diem_click) < 4:
        st.subheader("📍 BƯỚC 1: Click chọn 4 điểm")
        st.write("Chỉ bao quanh đúng 4 cột A, B, C, D của 2 vùng.")
        
        value = streamlit_image_coordinates(img_pil_xuly, key=f"clicker_{len(st.session_state.diem_click)}")
        
        if value is not None:
            toa_do = (value["x"], value["y"])
            if toa_do not in st.session_state.diem_click:
                st.session_state.diem_click.append(toa_do)
                st.rerun()

        for idx, pt in enumerate(st.session_state.diem_click):
            cv2.circle(img_hien_thi, pt, 8, (0, 0, 255), -1)
            cv2.putText(img_hien_thi, str(idx+1), (pt[0]+10, pt[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

        st.image(img_hien_thi, channels="BGR", use_container_width=True)
        st.warning(f"Đang ghi nhận... {len(st.session_state.diem_click)}/4 điểm.")

    # --- BƯỚC 2: CHIA LƯỚI & CHẤM ĐIỂM ---
    else:
        p1, p2, p3, p4 = st.session_state.diem_click
        
        v1_x_min, v1_y_min = min(p1[0], p2[0]), min(p1[1], p2[1])
        v1_x_max, v1_y_max = max(p1[0], p2[0]), max(p1[1], p2[1])
        v1_w = v1_x_max - v1_x_min
        v1_h = v1_y_max - v1_y_min
        
        v2_x_min, v2_y_min = min(p3[0], p4[0]), min(p3[1], p4[1])
        v2_x_max, v2_y_max = max(p3[0], p4[0]), max(p3[1], p4[1])
        v2_w = v2_x_max - v2_x_min
        v2_h = v2_y_max - v2_y_min
        
        cv2.rectangle(img_hien_thi, (v1_x_min, v1_y_min), (v1_x_max, v1_y_max), (0, 255, 0), 2)
        cv2.rectangle(img_hien_thi, (v2_x_min, v2_y_min), (v2_x_max, v2_y_max), (0, 255, 0), 2)

        gray = cv2.cvtColor(img_xuly, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 10)
        
        ket_qua = []
        labels = ["A", "B", "C", "D"]
        
        danh_sach_vung = [
            {"x": v1_x_min, "y": v1_y_min, "w": v1_w, "h": v1_h},
            {"x": v2_x_min, "y": v2_y_min, "w": v2_w, "h": v2_h}
        ]
        
        for vung in danh_sach_vung:
            chieu_cao_1_cau = vung['h'] / 20
            chieu_rong_1_o = vung['w'] / 4 
            
            margin_x = int(chieu_rong_1_o * 0.20)
            margin_y = int(chieu_cao_1_cau * 0.20)
            
            for dong in range(20):
                muc_trong_4_o = []
                for cot_abcd in range(4): 
                    x1 = int(vung['x'] + cot_abcd * chieu_rong_1_o)
                    y1 = int(vung['y'] + dong * chieu_cao_1_cau)
                    x2 = int(x1 + chieu_rong_1_o)
                    y2 = int(y1 + chieu_cao_1_cau)
                    
                    cv2.rectangle(img_hien_thi, (x1, y1), (x2, y2), (255, 0, 0), 1)
                    
                    loi_x1 = x1 + margin_x
                    loi_y1 = y1 + margin_y
                    loi_x2 = x2 - margin_x
                    loi_y2 = y2 - margin_y
                    
                    cv2.rectangle(img_hien_thi, (loi_x1, loi_y1), (loi_x2, loi_y2), (0, 255, 255), 1)
                    
                    vung_muc = thresh[loi_y1:loi_y2, loi_x1:loi_x2]
                    muc_trong_4_o.append(cv2.countNonZero(vung_muc))
                
                o_nhieu_muc_nhat = np.argmax(muc_trong_4_o)
                ket_qua.append(labels[o_nhieu_muc_nhat] if muc_trong_4_o[o_nhieu_muc_nhat] > nguong_muc else "Trống")
        
        # --- HIỂN THỊ KẾT QUẢ ---
        col_img, col_res = st.columns([1, 1])
        with col_img:
            st.success("✅ Đã cắt chuẩn và quét lõi mực thành công!")
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
