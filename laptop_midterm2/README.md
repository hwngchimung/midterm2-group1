# Mid-term 2 - Đề 6: Laptop Price

Bộ tài liệu hỗ trợ phân tích theo bốn giai đoạn ở mục II của đề. Các kết quả được tính từ file CSV do người học cung cấp. Báo cáo đã có bìa với logo NEU, AEP và thông tin Nhóm 1; cần bổ sung đường dẫn GitHub public, rà soát nội dung và kiểm tra Run all trên Colab trước khi nộp.

Đại học Kinh tế Quốc dân - Viện Đào tạo Tiên tiến, Chất lượng cao và POHE. Học phần: Khoa học dữ liệu.

| Thành viên Nhóm 1 | Mã sinh viên |
| --- | --- |
| Trần Hương Nhi | 11243708 |
| Nguyễn Thúy Anh | 11243888 |
| Trần Minh Ngọc | 11242573 |
| Đàm Phương Linh | 11243309 |

## Mở và chạy trên Google Colab

1. Mở [Google Colab](https://colab.research.google.com/), chọn Upload notebook và mở `notebooks/06_laptop_price.ipynb`.
2. Chọn Runtime > Run all. Khi notebook yêu cầu, tải lên `data/raw/laptop_price.csv`. Nếu file đã nằm ở `/content/laptop_price.csv` thì không phải tải lại.
3. Đợi tất cả ô chạy xong, đọc các bảng và diễn giải sau mỗi hình. Đầu ra được tạo trong `laptop_outputs/` của phiên Colab.
4. Lưu notebook có kết quả về máy để đưa lên repository. Phiên Colab có thể xóa file khi kết thúc, nên tải các đầu ra cần dùng trước khi thoát.

Notebook tự chứa các hàm phân tích, không cần tải `src/` lên Colab và không cần file kết quả có sẵn. Thư viện dùng là pandas, NumPy, SciPy, Matplotlib, vốn có trong môi trường Colab thông thường. Nếu môi trường đã bị thay đổi hoặc thiếu thư viện, dùng môi trường mới hoặc cài theo `requirements.txt`.

## Chạy mã nguồn trên máy

Từ thư mục chứa README này, với Python 3.10 trở lên:

```text
python -m pip install -r requirements.txt
python src/laptop_analysis.py
```

Lệnh thứ hai tái tạo bảng, hình và dữ liệu sạch. Bản CSV gốc được giữ nguyên. Phiên bản thư viện trong lần chạy được ghi vào `reports/results.json`; bootstrap dùng seed=42 và 2000 lần lặp. Notebook kiểm tra SHA-256 của CSV để tránh dùng số liệu diễn giải cũ cho một bản dữ liệu khác.

## Các file chính

| File/thư mục | Nội dung |
| --- | --- |
| `notebooks/06_laptop_price.ipynb` | Notebook đầy đủ, có code, bảng, hình và diễn giải tiếng Việt |
| `src/laptop_analysis.py` | Mã phân tích có thể chạy độc lập |
| `reports/bao_cao_phan_tich.md` | Bản thảo nội dung báo cáo, có thể chỉnh sửa |
| `output/pdf/bao_cao_laptop_ban_thao.pdf` | Bản PDF tham khảo để đọc và rà soát nội dung |
| `reports/figures/` | Bảy hình dùng trong báo cáo |
| `reports/tables/` | Kiểm tra dữ liệu, minh chứng trùng, ngoại lệ, kiểm định và độ nhạy |
| `reports/results.json` | Kết quả tổng hợp, mã băm dữ liệu và phiên bản thư viện |
| `data/raw/laptop_price.csv` | Dữ liệu gốc được cung cấp |
| `data/processed/laptop_clean.csv` | Dữ liệu sau bỏ trùng và tách đơn vị, giữ cờ IQR |

Các file trong `scripts/` dùng để dựng lại tài liệu, không phải bước bắt buộc của phân tích. Việc dựng notebook cần thêm `nbformat`; việc dựng PDF cần `reportlab`, `Pillow` và font Arial hoặc DejaVu Sans có hỗ trợ tiếng Việt. Các thư viện phụ này không cần cho Run all trên notebook đã cung cấp.

## Những lựa chọn cần hiểu khi trình bày

- Có 0 ô thiếu, vì vậy không điền Mean/Median để tạo ra một bước xử lý không cần thiết.
- Xét đủ 13 cột không có dòng trùng. Bỏ ID khỏi khóa so sánh có 28 bản ghi dư; giữ bản đầu tiên còn 1275 bản ghi. Không xóa chỉ theo tên Product.
- Có 28 bản ghi giá cao được gắn cờ IQR sau bỏ trùng. Đây là một tập khác với các bản ghi trùng. Chúng được giữ trong phân tích chính; bỏ cờ chỉ để kiểm tra độ nhạy.
- TB được quy đổi thành 1000 GB; tách SSD/HDD/Flash/Hybrid riêng và cộng đúng ổ kép.
- Không cần encoding/scaling cho các phép phân tích theo hạng. Mục II không bắt buộc mô hình dự đoán giá.
- Spearman, Mann-Whitney và Kruskal-Wallis đánh giá liên hệ/khác biệt trong mẫu; không khẳng định RAM/SSD gây ra mức tăng giá quan sát được.
- Có ba kiểm định chính, điều chỉnh Holm ở alpha=0,05. Các giả thuyết mang tính khám phá, chưa được xác nhận trên mẫu độc lập.
- Dữ liệu không có ngày giá, quốc gia hoặc doanh số, nên không trình bày như giá thị trường năm 2026 hay thị phần bán hàng.

## Hoàn thiện trước khi nộp

- Đọc, kiểm tra và điều chỉnh diễn giải để cả nhóm hiểu và bảo vệ được các quyết định.
- Bìa đã có logo NEU, AEP, tên trường/viện, học phần, đề 6 và bốn thành viên Nhóm 1. Kiểm tra tên/MSSV; bổ sung lớp và giảng viên nếu lớp có quy định riêng.
- Tạo repository GitHub của nhóm ở chế độ public; tải notebook, mã nguồn, dữ liệu cần thiết và báo cáo PDF chính thức lên đó.
- Thêm URL repository public thực tế vào báo cáo rồi xuất lại PDF. Không dùng đường dẫn ví dụ hoặc đường dẫn của notebook trong máy.
- Mở lại notebook trong một phiên Colab mới và chạy Run all, tải xuống bản đã lưu kết quả. Bản cung cấp đã được chạy kiểm tra bằng kernel Python cục bộ; Colab cần kiểm tra lại trong tài khoản của nhóm.
- Mở lại PDF chính thức để kiểm tra font tiếng Việt, logo, hình, bảng, số trang và URL GitHub. Bản hiện tại còn mang nhãn bản thảo vì chưa có URL GitHub thực tế.
- Theo thông báo giảng viên: hạn nộp **21:00, Chủ Nhật 08/11/2026**, giờ Việt Nam. Đường link tiếp nhận sẽ được giảng viên gửi ngày nộp.

## Nguồn

Đề Mid-Term 2 do giảng viên cung cấp, mục II. URL tập dữ liệu theo đề: [Laptop Price - muhammetvarl, Kaggle](https://www.kaggle.com/datasets/muhammetvarl/laptop-price). Các thống kê được tính trực tiếp từ bản CSV đi kèm; không suy đoán thời điểm thu thập mà file không cung cấp.

Tài liệu phương pháp: [Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html), [Mann-Whitney U](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html), [Kruskal-Wallis](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html).

Logo lấy từ [Hệ thống nhận diện NEU](https://neu.edu.vn/he-thong-nhan-dien/) và [website Viện AEP](https://aep.neu.edu.vn/). URL ảnh cụ thể và cách trích xuất ảnh gốc được ghi tại `assets/branding/sources.json`. Thông tin trường, nhóm và thành viên được lưu trong `project.json` để cập nhật bìa nhất quán.
