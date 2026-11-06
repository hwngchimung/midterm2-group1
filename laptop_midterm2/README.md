# Mid-term 2 - Đề 6: Laptop Price

Bộ tài liệu hỗ trợ phân tích theo bốn giai đoạn ở mục II của đề. Các kết quả được tính từ file CSV do người học cung cấp. Báo cáo đã có bìa với logo NEU, AEP và thông tin Nhóm 1; cần bổ sung đường dẫn GitHub public, rà soát nội dung và kiểm tra Run all trên Colab trước khi nộp.

Đại học Kinh tế Quốc dân - Viện Đào tạo Tiên tiến, Chất lượng cao và POHE. Học phần: Khoa học dữ liệu.

| Thành viên Nhóm 1 | Mã sinh viên |
| --- | --- |
| Trần Hương Nhi | 11243708 |
| Nguyễn Thúy Anh | 11243888 |
| Trần Minh Ngọc | 11242573 |
| Đàm Phương Linh | 11243309 |

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

## Nguồn

Đề Mid-Term 2 do giảng viên cung cấp, mục II. URL tập dữ liệu theo đề: [Laptop Price - muhammetvarl, Kaggle](https://www.kaggle.com/datasets/muhammetvarl/laptop-price). Các thống kê được tính trực tiếp từ bản CSV đi kèm; không suy đoán thời điểm thu thập mà file không cung cấp.

Tài liệu phương pháp: [Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html), [Mann-Whitney U](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html), [Kruskal-Wallis](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html).

Logo lấy từ [Hệ thống nhận diện NEU](https://neu.edu.vn/he-thong-nhan-dien/) và [website Viện AEP](https://aep.neu.edu.vn/). URL ảnh cụ thể và cách trích xuất ảnh gốc được ghi tại `assets/branding/sources.json`. Thông tin trường, nhóm và thành viên được lưu trong `project.json` để cập nhật bìa nhất quán.
