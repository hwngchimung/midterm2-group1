"""Dựng notebook tự chứa và bản thảo báo cáo từ kết quả đã tính thật."""
from pathlib import Path
import json
import sys
import textwrap

import nbformat as nbf
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / 'project.json').read_text(encoding='utf-8'))
sys.path.insert(0, str(ROOT / "src"))
from laptop_analysis import clean_data, audit_raw, analyze, hypothesis_tests, group_summary, sensitivity_analysis

raw = pd.read_csv(ROOT / "data/raw/laptop_price.csv", encoding="latin-1")
df = clean_data(raw)
s = {**audit_raw(raw)[1], **analyze(df)}
h = hypothesis_tests(df)
ram = group_summary(df, "Ram_GB").set_index("Ram_GB")
types = group_summary(df, "TypeName").set_index("TypeName")
brands = group_summary(df, "Company").set_index("Company")


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines += ["| " + " | ".join(map(str, r)) + " |" for r in rows]
    return "\n".join(lines)


def money(x):
    return f"{x:,.2f}"


insights = {
    "01_price_distribution.png": f"Giá có phân phối lệch phải: trung bình {money(s['price_mean'])} EUR cao hơn trung vị {money(s['price_median'])} EUR; hệ số lệch {s['price_skew']:.2f}. Khoảng giữa 50% bản ghi là {money(s['price_q1'])}-{money(s['price_q3'])} EUR. Có {s['iqr_flagged']} bản ghi vượt ngưỡng IQR trên {money(s['iqr_upper'])} EUR; các điểm này được giữ lại vì có thể thuộc phân khúc cao cấp. Trung vị và IQR mô tả mức giá điển hình phù hợp hơn chỉ dùng trung bình.",
    "02_ram_price.png": f"RAM liên hệ đồng biến mạnh với giá trong mẫu (Spearman rho={s['ram_rho']:.3f}). Trung vị các nhóm 4 GB, 8 GB và 16 GB lần lượt là {money(ram.loc[4,'median'])}, {money(ram.loc[8,'median'])} và {money(ram.loc[16,'median'])} EUR, với cỡ mẫu tương ứng {int(ram.loc[4,'n'])}, {int(ram.loc[8,'n'])} và {int(ram.loc[16,'n'])}. Nhóm 24 GB chỉ có 3 bản ghi và 64 GB chỉ có 1 bản ghi, nên không suy rộng xu hướng từ hai nhóm này. Chênh lệch giữa các nhóm không phải mức tăng giá do riêng việc nâng cấp RAM.",
    "03_ssd_price.png": f"Nhóm có SSD gồm {s['ssd_n']} bản ghi, trung vị {money(s['ssd_median'])} EUR; nhóm không có SSD gồm {s['non_ssd_n']} bản ghi, trung vị {money(s['non_ssd_median'])} EUR. Chênh lệch trung vị là {money(s['ssd_median_diff'])} EUR; khoảng bootstrap phân vị 95% từ 2000 lần lấy mẫu lại là [{money(s['ssd_median_diff_ci95'][0])}; {money(s['ssd_median_diff_ci95'][1])}] EUR. Đây là chênh lệch giữa hai nhóm cấu hình, có thể chịu ảnh hưởng của RAM, CPU, hãng và loại máy; không phải chi phí lắp thêm SSD. Flash Storage không được tự gộp vào SSD.",
    "04_type_price.png": f"Workstation có trung vị {money(types.loc['Workstation','median'])} EUR (n={int(types.loc['Workstation','n'])}), Notebook {money(types.loc['Notebook','median'])} EUR (n={int(types.loc['Notebook','n'])}), Netbook {money(types.loc['Netbook','median'])} EUR (n={int(types.loc['Netbook','n'])}). Gaming và Ultrabook có trung vị lần lượt {money(types.loc['Gaming','median'])} và {money(types.loc['Ultrabook','median'])} EUR. Phân bố giữa các loại vẫn chồng lấn; loại máy giúp phân đoạn nhu cầu nhưng không quyết định hoàn toàn giá. Kiểm định tổng thể không cho biết cặp loại nào khác biệt có ý nghĩa.",
    "05_company_price.png": f"Trong các hãng có ít nhất 20 bản ghi, MSI có trung vị {money(brands.loc['MSI','median'])} EUR (n={int(brands.loc['MSI','n'])}), Apple {money(brands.loc['Apple','median'])} EUR (n={int(brands.loc['Apple','n'])}) và Acer {money(brands.loc['Acer','median'])} EUR (n={int(brands.loc['Acer','n'])}). Ngưỡng n>=20 được chọn để hạn chế diễn giải nhóm quá nhỏ, không phải tiêu chuẩn bảo đảm tính đại diện. Các hãng dưới ngưỡng vẫn được giữ trong dữ liệu và bảng đầy đủ. Đây là so sánh cơ cấu sản phẩm trong mẫu, chưa tách được phần giá gắn với thương hiệu khi cùng cấu hình.",
    "06_ppi_price.png": f"Mật độ điểm ảnh PPI có liên hệ đồng biến với giá (rho={s['ppi_rho']:.3f}), nhưng tại cùng PPI giá vẫn phân tán rộng. Màu RAM cho thấy thuộc tính màn hình và cấu hình có thể đi cùng nhau. PPI chỉ phản ánh độ sắc nét theo độ phân giải và kích thước, không đại diện đầy đủ cho chất lượng tấm nền, độ sáng hay độ chính xác màu. Không nên dùng riêng PPI để định giá.",
    "07_spearman_heatmap.png": f"Trong các biến được đưa vào heatmap, tương quan với giá nổi bật ở RAM (rho={s['ram_rho']:.3f}) và SSD_GB (rho=0.689); PPI có rho={s['ppi_rho']:.3f}. Weight_kg có rho={s['weight_rho']:.3f}, gần 0, nhưng điều này không loại trừ liên hệ phi tuyến hoặc khác biệt trong từng phân khúc. RAM và SSD_GB có rho=0.602, cho thấy các cấu hình thường đi kèm nhau. Cpu_GHz không đo đầy đủ hiệu năng CPU giữa các thế hệ. Các tương quan là mô tả, không chứng minh tác động độc lập hay nhân quả.",
}

dictionary = [
    ("laptop_ID", "Số nguyên", "Mã bản ghi; giữ để truy vết, không dùng làm biến giải thích"),
    ("Company", "Phân loại", "Hãng sản xuất; 19 giá trị"),
    ("Product", "Văn bản", "Tên sản phẩm; cùng tên có thể có nhiều cấu hình"),
    ("TypeName", "Phân loại", "Loại laptop; 6 nhóm"),
    ("Inches", "Số thực", "Kích thước đường chéo màn hình, inch"),
    ("ScreenResolution", "Văn bản", "Độ phân giải và mô tả IPS/Touchscreen"),
    ("Cpu", "Văn bản", "Nhãn CPU và xung nhịp GHz"),
    ("Ram", "Văn bản", "Dung lượng RAM, có hậu tố GB"),
    ("Memory", "Văn bản", "Dung lượng và loại từng ổ lưu trữ"),
    ("Gpu", "Văn bản", "Nhãn GPU"),
    ("OpSys", "Phân loại", "Hệ điều hành"),
    ("Weight", "Văn bản", "Trọng lượng, có hậu tố kg"),
    ("Price_euros", "Số thực", "Giá laptop theo EUR; biến kết quả phân tích"),
]

duplicate_keys = [c for c in raw if c != "laptop_ID"]
dups = raw[raw.duplicated(subset=duplicate_keys, keep=False)]
first = dups.iloc[0]
same = raw.loc[(raw[duplicate_keys] == first[duplicate_keys]).all(axis=1), "laptop_ID"].tolist()
sensitivity = sensitivity_analysis(raw, df)
# Tên cột chứa dấu chấm không phù hợp itertuples; truy cập bằng khóa.
h_rows = [[r["hypothesis"], r["test"], f"{r['statistic']:.4f}", f"{r['p_raw']:.3e}", f"{r['p_holm']:.3e}", "Bác bỏ H0" if r["reject_H0_at_0.05"] else "Chưa bác bỏ H0"] for _, r in h.iterrows()]

sections = []
sections.append(("1. Thu thập và đánh giá dữ liệu ban đầu", f"""
Đề tài 6: Laptop Price. Mục tiêu là mô tả phân khúc giá và đánh giá mối liên hệ giữa giá với RAM, lưu trữ, loại máy và màn hình. Bài này tập trung vào phân tích theo mục II của đề; không bổ sung mô hình dự đoán khi chưa có yêu cầu riêng.

Nguồn được chỉ định trong đề: [Laptop Price - Kaggle, muhammetvarl]({ 'https://www.kaggle.com/datasets/muhammetvarl/laptop-price' }). Phân tích sử dụng đúng bản CSV do người học cung cấp, không thay thế bằng phiên bản tải từ nơi khác. Một dòng được coi là một bản ghi mô tả cấu hình và giá, không coi là một giao dịch bán hàng.

Tập gốc có 1.303 dòng, 13 thuộc tính trong một file CSV, không cần ghép bảng. File được đọc với encoding latin-1 để giữ các ký tự trong nhãn sản phẩm. Không có trường thời gian ghi nhận, quốc gia, số lượng bán hay khách hàng; vì vậy không phân tích xu hướng theo thời gian hoặc thị phần bán hàng.

{table(['Thuộc tính', 'Kiểu ý nghĩa', 'Nội dung và vai trò'], dictionary)}

Kiểm tra toàn bộ 13 cột cho thấy 0 ô thiếu, 0 chuỗi rỗng sau khi bỏ khoảng trắng và 0 mã laptop_ID trùng. Có 0 dòng trùng khi xét đủ 13 cột nhưng 28 bản ghi dư khi bỏ laptop_ID khỏi khóa so sánh. Bảng chi tiết kiểu dữ liệu, số giá trị phân biệt và tỷ lệ thiếu nằm trong reports/tables/01_data_audit.csv.

Ba câu hỏi kiểm định là: RAM có liên hệ đồng biến với giá không? Nhóm có SSD có xu hướng giá cao hơn không? Phân phối giá có khác nhau giữa các TypeName không? Các kiểm định được trình bày như phân tích khám phá trên mẫu hiện có, không phải giả thuyết được đăng ký trước trên một mẫu xác nhận độc lập.
"""))
sections.append(("2. Tiền xử lý và làm sạch", f"""
Các cột Ram, Weight, Memory và ScreenResolution có thông tin số nằm trong chuỗi. Chúng không phải giá trị thiếu; vấn đề là định dạng chưa thích hợp cho tính toán. Giữ lại trường gốc và tạo các trường số để đối chiếu.

{table(['Trường mới', 'Cách tạo và giải trình'], [
('Ram_GB', '8GB thành 8; tránh so sánh theo thứ tự chuỗi'),
('Weight_kg', '1.37kg thành 1.37; giữ đơn vị kg'),
('ScreenWidth_px, ScreenHeight_px', 'Tách 2560x1600 thành 2560 và 1600'),
('PPI', 'sqrt(width^2 + height^2) / Inches; xét độ phân giải cùng kích thước'),
('IPS, Touchscreen', 'Cờ Boolean từ mô tả màn hình'),
('Cpu_GHz, Cpu_brand, Gpu_brand', 'Tách xung nhịp và nhãn hãng; GHz không đồng nghĩa hiệu năng'),
('SSD_GB, HDD_GB, Flash_GB, Hybrid_GB', 'Tách từng ổ, cộng ổ cùng loại; quy ước 1 TB = 1000 GB'),
('Has_SSD', 'SSD_GB > 0; không tự coi Flash Storage là SSD'),
('Price_IQR_flag', 'Cờ ngoài [Q1 - 1.5 IQR; Q3 + 1.5 IQR]')])}

Ví dụ Memory: 128GB SSD + 1TB HDD thành SSD_GB=128, HDD_GB=1000; 1TB HDD + 1TB HDD thành HDD_GB=2000; 1.0TB Hybrid thành Hybrid_GB=1000. Không dùng cách lấy mọi chữ số trong cả chuỗi vì sẽ làm sai ổ kép. Bộ tách báo lỗi khi gặp định dạng không nhận diện, thay vì im lặng gán 0.

Về trùng lặp, so sánh toàn bộ 12 trường ngoài ID rồi giữ bản đầu tiên, giảm từ 1.303 xuống 1.275 bản ghi. Ví dụ các ID {', '.join(map(str, same))} có cùng nội dung ngoài ID. Quyết định này tránh đếm lặp cùng cấu hình-giá trong phân tích mô tả; CSV không cung cấp thời điểm hoặc nơi niêm yết để xác nhận đây là các niêm yết độc lập. Không xóa theo Product vì cùng tên sản phẩm có thể có cấu hình khác nhau. Bảng minh chứng chứa tất cả thành viên của các nhóm trùng nằm trong 04_duplicate_evidence.csv, nên số dòng trong bảng đó lớn hơn số bản ghi bị loại.

Không điền Mean/Median vì không phát hiện giá trị thiếu. Các trường số tạo ra đều được kiểm tra thiếu và điều kiện dương khi phù hợp; không phát hiện giá không dương. Không cần one-hot encoding hoặc StandardScaler cho thống kê mô tả và kiểm định theo hạng. Không mã hóa hãng thành các số thứ tự vì sẽ tạo ra thứ bậc không có thật. Nếu sau này thêm mô hình, việc fit bộ mã hóa/chuẩn hóa phải thực hiện trên tập huấn luyện.

Sau bỏ trùng, Q1={money(s['price_q1'])}, Q3={money(s['price_q3'])}, IQR={money(s['price_q3']-s['price_q1'])} EUR. Ngưỡng dưới là {money(s['iqr_lower'])} và ngưỡng trên {money(s['iqr_upper'])} EUR. Có {s['iqr_flagged']} bản ghi ({100*s['iqr_flagged']/s['clean_rows']:.2f}%) được gắn cờ, đều ở phía giá cao. Đây là 28 cờ ngoại lệ, khác với 28 bản ghi trùng đã loại. Giữ tất cả cờ ngoại lệ trong phân tích chính vì chưa có bằng chứng sai nhập liệu; giá cao nhất {money(s['price_max'])} EUR được giữ lại. Dùng thêm phân tích độ nhạy khi bỏ các cờ để xem kết luận có bị chi phối hay không.
"""))
sections.append(("3. Phân tích và trực quan hóa", "Phạm vi các biểu đồ dưới đây là 1.275 bản ghi sau bỏ trùng, gồm cả 28 cờ IQR. Giá giữ nguyên đơn vị EUR; không quy đổi sang VND khi không có ngày giá và tỷ giá tương ứng. Các số trong nhận định được tính từ dữ liệu, không giả lập."))
titles = ["Phân phối giá", "RAM và giá", "SSD và giá", "Loại laptop và giá", "Hãng và giá", "Mật độ điểm ảnh và giá", "Tương quan giữa các thuộc tính"]
for i, ((filename, insight), title) in enumerate(zip(insights.items(), titles), 1):
    sections.append((f"3.{i}. {title}", f"![Hình {i}. {title}](figures/{filename})\n\nHình {i}. {insight}"))
sections.append(("3.8. Kiểm định giả thuyết và độ lớn khác biệt", f"""
Chọn mức ý nghĩa alpha=0,05. Do giá lệch phải và RAM là biến rời rạc, dùng kiểm định theo hạng thay vì mặc định phân phối chuẩn. Thực hiện ba kiểm định chính và điều chỉnh p-value bằng Holm cho cả họ kiểm định. Các p-value là xấp xỉ; không diễn giải p-value là xác suất H0 đúng hay là độ lớn tác động.

H1: H0 là rho(RAM, giá)=0; H1 là rho>0. Spearman một phía đo mối liên hệ đơn điệu, xử lý các giá trị RAM bằng nhau qua xếp hạng trung bình. Kết quả rho={s['ram_rho']:.3f} cho thấy liên hệ đồng biến mạnh trong mẫu.

H2: H0 là hai phân phối giá của nhóm có SSD và không SSD giống nhau; H1 là nhóm có SSD có xu hướng giá cao hơn. Mann-Whitney một phía dùng xấp xỉ có hiệu chỉnh ties. U/(n1*n0)={h.loc[1,'effect']:.3f}, tức xác suất một bản ghi SSD có giá cao hơn một bản ghi không SSD, cộng nửa xác suất bằng giá, xấp xỉ {100*h.loc[1,'effect']:.1f}% khi lấy ngẫu nhiên từ hai nhóm trong mẫu. Kiểm định này không tự động là kiểm định chênh lệch trung vị khi hình dạng phân phối khác nhau.

H3: H0 là các phân phối giá theo TypeName giống nhau; H1 là có khác biệt ở ít nhất một nhóm. Kruskal-Wallis cho H={h.loc[2,'statistic']:.3f} với 6 nhóm; nhóm nhỏ nhất có {int(types.n.min())} bản ghi. Chỉ diễn giải như khác biệt về vị trí/trung vị khi các nhóm có hình dạng phân phối tương tự; ở đây kết luận thận trọng về phân phối/thứ hạng. Epsilon-squared H=(H-k+1)/(n-k)={h.loc[2,'effect']:.3f} là chỉ số độ lớn khác biệt tổng thể. Chưa thực hiện hậu kiểm, nên không tuyên bố từng cặp đều khác biệt.

{table(['Giả thuyết', 'Kiểm định', 'Thống kê', 'p gốc', 'p Holm', 'Quyết định'], h_rows)}

Cả ba H0 đều bị bác bỏ ở alpha=0,05 sau điều chỉnh Holm. Đây là bằng chứng về liên hệ trong mẫu theo giả định các bản ghi độc lập. Cùng một dòng sản phẩm có thể xuất hiện dưới nhiều cấu hình, nên độc lập chỉ là xấp xỉ; mẫu không ngẫu nhiên cũng hạn chế suy rộng ra thị trường. Khoảng bootstrap SSD chỉ phản ánh bất định khi lấy mẫu lại từ dữ liệu hiện có và không bao gồm sai lệch chọn mẫu hoặc biến gây nhiễu.
"""))
sens_rows = [[r.scenario, int(r.n), money(r.median_eur), f"{r.ram_rho:.3f}", money(r.ssd_median_gap_eur)] for r in sensitivity.itertuples()]
sections.append(("3.9. Kiểm tra độ nhạy", f"""
{table(['Kịch bản', 'n', 'Trung vị EUR', 'rho RAM-giá', 'Chênh trung vị SSD EUR'], sens_rows)}

Khi giữ bản ghi trùng, bỏ trùng hoặc tạm loại cờ IQR, rho RAM-giá nằm trong khoảng {sensitivity.ram_rho.min():.3f}-{sensitivity.ram_rho.max():.3f}, vẫn dương mạnh. Chênh trung vị SSD vẫn dương, khoảng {money(sensitivity.ssd_median_gap_eur.min())}-{money(sensitivity.ssd_median_gap_eur.max())} EUR. Cả ba kiểm định vẫn có p Holm<0,05 ở ba kịch bản. Vì vậy hướng kết luận chính không phụ thuộc riêng vào quyết định bỏ trùng hay một số mức giá cao. Kịch bản bỏ cờ IQR chỉ là đối chiếu, không thay thế mẫu chính. Bảng 03_sensitivity.csv lưu cả p-value để kiểm tra lại.
"""))
sections.append(("4. Đánh giá tác động và khuyến nghị", f"""
Phát hiện chính: mức giá điển hình trong mẫu là trung vị {money(s['price_median'])} EUR; RAM và lưu trữ SSD liên hệ rõ với giá, còn loại laptop giúp nhận diện phân khúc. Hãng có mức giá khác nhau nhưng chưa thể quy phần chênh lệch cho riêng thương hiệu. Các khuyến nghị sau là đề xuất dựa trên cấu trúc mẫu, chưa phải hiệu quả kinh doanh đã được thử nghiệm.

Đối với người mua: xác định nhóm nhu cầu trước khi so sánh giá. Dùng các nhóm RAM 4/8/16 GB và loại laptop để chọn các máy tương đồng, rồi đối chiếu CPU, GPU, SSD và màn hình. Trung vị nhóm là mức tham khảo từ bộ dữ liệu này, không phải báo giá laptop hiện tại.

Đối với đơn vị kinh doanh: có thể xây bảng tham khảo giá theo loại máy và cấu hình, dùng trung vị/IQR để hạn chế ảnh hưởng của vài sản phẩm rất đắt. Khi rà soát mức niêm yết bất thường, xem lại mô tả cấu hình trước khi kết luận sai giá. Dữ liệu không có doanh số, lợi nhuận hoặc tồn kho, nên chưa đủ để quyết định tỷ trọng nhập hàng hay tối ưu doanh thu.

Đối với chất lượng dữ liệu: lưu dung lượng và loại ổ ở trường riêng, trọng lượng dạng số kèm đơn vị, giữ mã truy vết và kiểm tra trùng theo cấu hình-giá. Bổ sung thời điểm, nơi niêm yết, tình trạng mới/cũ, bảo hành và thế hệ CPU/GPU sẽ giúp so sánh công bằng hơn.

Giới hạn: đây là tập dữ liệu tiện lợi với cơ cấu hãng/loại máy mất cân bằng; một số nhóm chỉ 1-3 bản ghi. CSV không nêu thời điểm và khu vực giá, không có lịch sử giao dịch, thuế, giảm giá hoặc phiên bản cấu hình đầy đủ. Dữ liệu quan sát không tách được tác động độc lập của RAM, SSD hay thương hiệu. Kiểm định và bootstrap giả định độc lập xấp xỉ giữa bản ghi. Quy ước TB=1000 GB và quy tắc bỏ trùng có thể được thay đổi nếu có tài liệu nguồn rõ hơn.

Hướng mở rộng: bổ sung dữ liệu có ngày và quốc gia, thiết lập khóa sản phẩm/cấu hình rõ ràng, kiểm tra cụm theo dòng sản phẩm. Nếu thêm dự đoán giá, so sánh baseline với mô hình hồi quy bằng MAE/RMSE và cross-validation; chia nhóm theo sản phẩm để hạn chế lọt cấu hình tương tự giữa train/test; fit preprocessing trong từng fold. Phần mô hình này chưa được thực hiện và không phải kết quả của báo cáo hiện tại.
"""))
sections.append(("5. Tái lập và tài liệu tham khảo", """
Notebook 06_laptop_price.ipynb chứa mã xử lý và diễn giải; chỉ cần file laptop_price.csv để chạy, không phụ thuộc các file kết quả tạo sẵn. Các bước có comment tiếng Việt. Mã nguồn tương ứng nằm trong src/laptop_analysis.py. Cố định seed=42 cho bootstrap 2000 lần. SHA-256 của bản CSV và phiên bản thư viện được ghi trong reports/results.json; chạy trên môi trường thư viện khác có thể chênh lệch rất nhỏ về số thực hoặc biểu diễn hình.

Tài liệu dùng để xây dựng bài:

- Đề Mid-Term 2 do giảng viên cung cấp, mục II: bốn giai đoạn phân tích và yêu cầu notebook/GitHub.
- [Laptop Price, muhammetvarl, Kaggle](https://www.kaggle.com/datasets/muhammetvarl/laptop-price): URL dữ liệu theo đề; các thống kê trong bài tính trực tiếp từ CSV được cung cấp.
- [SciPy - Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html): tương quan theo hạng và kiểm định một phía.
- [SciPy - Mann-Whitney U](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html): kiểm định hai mẫu độc lập, ties và cách diễn giải.
- [SciPy - Kruskal-Wallis](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html): kiểm định tổng thể nhiều nhóm, không thay thế hậu kiểm.

Nguồn logo trên bìa: [Hệ thống nhận diện NEU](https://neu.edu.vn/he-thong-nhan-dien/) và [Viện AEP](https://aep.neu.edu.vn/). File logo AEP độ phân giải gốc được trích xuất nguyên vẹn từ ảnh nhúng trong SVG của website chính thức; thông tin nguồn nằm trong assets/branding/sources.json.

Bản thảo đã có bìa Đại học Kinh tế Quốc dân, Viện Đào tạo Tiên tiến, Chất lượng cao và POHE, cùng thông tin bốn thành viên Nhóm 1. Cần thêm URL GitHub public thực tế và rà soát lần cuối trước khi nộp. Chưa có thao tác tạo hoặc đẩy repository GitHub trong bộ tài liệu này.
"""))

report = "# Phân tích giá laptop\n\nBản thảo nội dung - Mid-term 2, đề 6\n\n"
team_intro = PROJECT['university'] + '  \n' + PROJECT['institute'] + '  \nHọc phần: ' + PROJECT['course'] + '  \n' + PROJECT['group'] + '\n\n'
team_intro += table(['Họ và tên','Mã sinh viên'], [[m['name'],m['student_id']] for m in PROJECT['members']]) + '\n\n'
report += team_intro
report += "\n\n".join(f"## {title}\n\n{textwrap.dedent(body).strip()}" for title, body in sections) + "\n"
(ROOT / "reports/bao_cao_phan_tich.md").write_text(report, encoding="utf-8")

# Notebook tự chứa: nhúng các hàm từ mã nguồn, không cần import file .py trên Colab.
nb = nbf.v4.new_notebook()
cells = [nbf.v4.new_markdown_cell("# Đề 6 - Phân tích giá laptop\n\n" +
    team_intro +
    "Bám 4 giai đoạn mục II. Dùng bản CSV được cung cấp. Chọn **Runtime → Run all**. " +
    "Nếu chưa có dữ liệu, Colab sẽ yêu cầu tải lên `laptop_price.csv`. Notebook không tải gói hoặc dữ liệu từ nguồn khác. " +
    "Mỗi biểu đồ có diễn giải bên dưới; số liệu được tái tính trong các ô lệnh.")]
cells.append(nbf.v4.new_code_cell("""# Nhập thư viện và định vị file dữ liệu trên máy hoặc Google Colab.
from pathlib import Path
from IPython.display import display, Markdown, Image
import sys
candidate_paths = [Path('laptop_price.csv'), Path('data/raw/laptop_price.csv'), Path('../data/raw/laptop_price.csv'), Path('/content/laptop_price.csv')]
DATA_PATH = next((p for p in candidate_paths if p.is_file()), None)
if DATA_PATH is None:
    try:
        from google.colab import files
    except ImportError:
        raise FileNotFoundError('Đặt laptop_price.csv cạnh notebook hoặc trong data/raw/.') from None
    uploaded = files.upload()
    DATA_PATH = Path('laptop_price.csv')
    if not DATA_PATH.is_file():
        raise FileNotFoundError('Hãy tải đúng file laptop_price.csv rồi chạy lại.')
OUTPUT = Path('laptop_outputs')
OUTPUT.mkdir(exist_ok=True)
print('Dữ liệu:', DATA_PATH.name)
"""))
source = (ROOT / "src/laptop_analysis.py").read_text(encoding="utf-8").split('if __name__ == "__main__":')[0]
chunks = source.split("# %% ")
labels = ["Thư viện và cấu hình", "Hàm đánh giá dữ liệu", "Hàm làm sạch và tách đơn vị", "Hàm kiểm định và phân tích độ nhạy", "Hàm trực quan hóa", "Hàm lưu đầu ra"]
for i, chunk in enumerate(chunks):
    if i:
        chunk = chunk.split("\n", 1)[1]
    cells.append(nbf.v4.new_markdown_cell("### " + labels[i]))
    cells.append(nbf.v4.new_code_cell(chunk.strip()))

cells.append(nbf.v4.new_markdown_cell("## 1. Thu thập và đánh giá ban đầu\n\n" + sections[0][1]))
cells.append(nbf.v4.new_code_cell("""# Đọc nguyên bản, kiểm tra kiểu dữ liệu, missing và trùng trước xử lý.
raw = pd.read_csv(DATA_PATH, encoding='latin-1')
schema, audit = audit_raw(raw)
display(raw.head())
display(schema)
display(pd.Series(audit, name='Giá trị').to_frame())
"""))
cells.append(nbf.v4.new_markdown_cell("## 2. Tiền xử lý\n\n" + sections[1][1]))
cells.append(nbf.v4.new_code_cell("""# Giữ bằng chứng trùng; sau đó tạo bộ dữ liệu sạch nhưng vẫn giữ cờ IQR.
keys = [c for c in raw if c != 'laptop_ID']
duplicates = raw.loc[raw.duplicated(subset=keys, keep=False)]
display(duplicates.head(10))
clean = clean_data(raw)
summary = {**audit, **analyze(clean)}
display(clean[['Ram', 'Ram_GB', 'Weight', 'Weight_kg', 'Memory', 'SSD_GB', 'HDD_GB', 'Flash_GB', 'Hybrid_GB']].head(10))
display(pd.Series(summary, name='Kết quả').to_frame())
display(clean.loc[clean.Price_IQR_flag, ['laptop_ID','Company','Product','TypeName','Ram','Memory','Price_euros']].sort_values('Price_euros', ascending=False).head(10))
assert len(raw) == 1303 and len(clean) == 1275, 'File dữ liệu khác bản được dùng cho bản thảo; cần rà soát lại số liệu diễn giải.'
assert hashlib.sha256(DATA_PATH.read_bytes()).hexdigest() == 'e5cd3296b994d10e27ada65b4af529725b3e1bdd320e61ec7fb4fe6bfa4fc7c4', 'Dữ liệu đã đổi; cần cập nhật phần diễn giải.'
"""))
cells.append(nbf.v4.new_markdown_cell("## 3. Phân tích và trực quan hóa\n\nCác số liệu diễn giải bên dưới áp dụng cho bản CSV đi kèm. Nếu đổi dữ liệu, hãy cập nhật nhận định dựa trên các bảng được tái tính."))
cells.append(nbf.v4.new_code_cell("""# Vẽ và lưu bảy hình, tính lại thống kê nhóm để đối chiếu với diễn giải.
make_figures(clean, OUTPUT / 'figures')
for field in ['Ram_GB', 'Has_SSD', 'TypeName', 'Company']:
    display(group_summary(clean, field))
"""))
for i, (filename, insight) in enumerate(insights.items(), 1):
    cells.append(nbf.v4.new_markdown_cell(f"### Hình {i}. {titles[i-1]}\n\nCâu hỏi: {titles[i-1]} có đặc điểm hoặc liên hệ gì trong mẫu?"))
    cells.append(nbf.v4.new_code_cell(f"# Hiển thị hình đã tính từ clean.\ndisplay(Image(filename=str(OUTPUT / 'figures/{filename}')))"))
    cells.append(nbf.v4.new_markdown_cell("**Diễn giải:** " + insight))
cells.append(nbf.v4.new_markdown_cell("### Kiểm định giả thuyết\n\n" + sections[-4][1]))
cells.append(nbf.v4.new_code_cell("""# Kiểm định ba giả thuyết, hiệu chỉnh Holm và đối chiếu độ nhạy.
tests = hypothesis_tests(clean)
display(tests)
sens = sensitivity_analysis(raw, clean)
display(sens)
display(clean[NUMERIC_FEATURES].corr(method='spearman'))
"""))
cells.append(nbf.v4.new_markdown_cell("### Độ nhạy\n\n" + sections[-3][1]))
cells.append(nbf.v4.new_markdown_cell("## 4. Tác động, khuyến nghị và giới hạn\n\n" + sections[-2][1]))
cells.append(nbf.v4.new_code_cell("""# Xuất dữ liệu và bảng để đưa vào báo cáo; không sửa file gốc.
import hashlib, platform
clean.to_csv(OUTPUT / 'laptop_clean.csv', index=False, encoding='utf-8-sig')
schema.to_csv(OUTPUT / 'data_audit.csv', index=False)
tests.to_csv(OUTPUT / 'hypothesis_tests.csv', index=False)
sens.to_csv(OUTPUT / 'sensitivity.csv', index=False)
summary['source_sha256'] = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
summary['versions'] = {'python': platform.python_version(), 'pandas': pd.__version__, 'numpy': np.__version__, 'scipy': scipy.__version__, 'matplotlib': matplotlib.__version__}
(OUTPUT / 'results.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print('Hoàn tất. Kết quả tại:', OUTPUT.as_posix())
"""))
cells.append(nbf.v4.new_markdown_cell("## Tài liệu tham khảo và trước khi nộp\n\n" + sections[-1][1]))
nb.cells = cells
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
               "language_info": {"name": "python", "version": "3.12"}, "colab": {"provenance": []}}
(ROOT / "notebooks").mkdir(exist_ok=True)
notebook_path = ROOT / "notebooks/06_laptop_price.ipynb"
# Chỉnh thông tin báo cáo vẫn giữ các kết quả thực thi của ô mã không đổi.
if notebook_path.exists():
    old = nbf.read(notebook_path, as_version=4)
    previous = {c.source: c for c in old.cells if c.cell_type == 'code'}
    for cell in nb.cells:
        if cell.cell_type == 'code' and cell.source in previous:
            cell.outputs = previous[cell.source].outputs
            cell.execution_count = previous[cell.source].execution_count
nbf.write(nb, notebook_path)
print(f"Đã tạo notebook {len(cells)} ô và báo cáo {len(sections)} mục.")
