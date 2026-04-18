import cv2
import numpy as np
import streamlit as st
from PIL import Image

st.set_page_config(page_title="VDC - HEPC Auto Scanner", layout="wide")
st.title("🚀 HEPC Auto-Scanner V0.10")
st.write("Giảng viên: **Trần Công Đẹp** | Tính năng: Tự động bẻ phẳng & Chấm điểm đám mây")

# --- HÀM TỰ ĐỘNG CẮT VÀ BẺ PHẲNG ---
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
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
    
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

# --- GIAO DIỆN CẤU HÌNH ---
st.sidebar.header("⚙️ CẤU HÌNH ĐÁP ÁN")
input_dap_an = st.sidebar.text_area("Nhập dãy đáp án (VD: ABCD...):", value="ABCD")
DAP_AN_LIST = list(input_dap_an.upper().replace(" ", ""))

st.sidebar.markdown("---")
st.sidebar.info("Mẹo: Đặt phiếu thi lên mặt bàn tối màu để camera tự động cắt chính xác nhất.")

uploaded_file = st.sidebar.file_uploader("Tải ảnh phiếu làm bài lên đây...", type=["jpg", "png", "jpeg"])

# --- XỬ LÝ ẢNH & CHẤM ĐIỂM ---
if uploaded_file:
    # Đọc ảnh từ file tải lên
    img_pil = Image.open(uploaded_file).convert("RGB")
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    img_display = img_cv.copy()
    
    # Tiền xử lý để tìm khung
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    
    # Tìm các đường viền
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    table_contour = None
    # Lọc tìm khung chữ nhật lớn nhất
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            table_contour = approx
            break
            
    if table_contour is not None:
        cv2.drawContours(img_display, [table_contour], -1, (0, 255, 0), 5)
        
        # Bẻ phẳng ảnh
        warped = four_point_transform(img_cv, table_contour.reshape(4, 2))
        warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        # Tăng cường độ tương phản mực đen
        _, thresh = cv2.threshold(warped_gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        W, H = warped.shape[1], warped.shape[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📸 Vùng nhận diện")
            st.image(img_display, channels="BGR", use_container_width=True)
        with col2:
            st.subheader("📐 Ảnh bẻ phẳng")
            st.image(warped, channels="BGR", use_container_width=True)
            
        st.success("Tuyệt vời! Đã cố định khung tự động. Đang xử lý đáp án...")
        
        results = []
        labels = ["A", "B", "C", "D"]
        
        # Thiết lập thông số lưới 
        w_half = W / 2
        row_h = H / 21 # Bảng có 1 dòng tiêu đề + 20 dòng câu hỏi
        col_w = w_half / 5 # Gồm 5 cột: STT, A, B, C, D
        
        # Quét cột 1-20 (Vùng trái) và 21-40 (Vùng phải)
        for v_idx in range(2):
            base_x = v_idx * w_half
            for r in range(1, 21): # Bỏ qua dòng 0 là tiêu đề
                px_counts = []
                for c in range(1, 5): # Chỉ lấy 4 cột đáp án (bỏ cột STT)
                    x1 = int(base_x + c * col_w)
                    y1 = int(r * row_h)
                    x2, y2 = int(x1 + col_w), int(y1 + row_h)
                    
                    roi = thresh[y1:y2, x1:x2]
                    px_counts.append(cv2.countNonZero(roi))
                    # Vẽ viền xanh lên các ô để kiểm tra độ khớp
                    cv2.rectangle(warped, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    
                max_idx = np.argmax(px_counts)
                # Ngưỡng đếm mực: lớn hơn 30 điểm ảnh màu đen thì tính là có chọn
                results.append(labels[max_idx] if px_counts[max_idx] > 30 else "Trống")
                
        st.divider()
        st.subheader("✅ Lưới quét tự động")
        st.image(warped, channels="BGR", caption="Các ô màu xanh là vùng máy đang kiểm tra vết mực")
        
        # Hiển thị kết quả chi tiết
        score = 0
        res_cols = st.columns(4)
        for i, res in enumerate(results[:len(DAP_AN_LIST)]):
            dung = DAP_AN_LIST[i]
            is_ok = (res == dung)
            if is_ok: score += 1
            with res_cols[i % 4]:
                st.write(f"C{i+1}: **{res}** {'✅' if is_ok else '❌'}")
                
        st.sidebar.metric("TỔNG ĐIỂM", f"{(score/len(DAP_AN_LIST)*10):.2f}/10")
        st.sidebar.write(f"Đúng: {score} / {len(DAP_AN_LIST)} câu")
    else:
        st.error("⚠️ Lỗi: Không tìm thấy khung bảng. Vui lòng đặt giấy lên mặt bàn có màu khác với giấy và chụp thấy rõ cả 4 góc của đường viền bảng.")
        st.image(img_display, channels="BGR", use_container_width=True)
else:
    st.info("Chờ tải ảnh phiếu thi lên để bắt đầu...")
