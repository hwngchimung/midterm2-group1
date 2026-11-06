"""Phân tích đề 6 - Laptop Price. Chạy từ thư mục gốc của dự án.

python src/laptop_analysis.py
Không thay đổi dữ liệu gốc. Các đầu ra được tái tạo trong reports/ và data/processed/.
"""
from pathlib import Path
import hashlib
import json
import re
import platform

import numpy as np
import pandas as pd
import scipy
from scipy import stats
import matplotlib
matplotlib.use("Agg")  # Chỉ lưu hình; hoạt động cả trên Colab và máy không có giao diện đồ họa.
import matplotlib.pyplot as plt

SOURCE_URL = "https://www.kaggle.com/datasets/muhammetvarl/laptop-price"
ALPHA = 0.05
SEED = 42
NUMERIC_FEATURES = ["Ram_GB", "Weight_kg", "Inches", "PPI", "Cpu_GHz", "SSD_GB", "HDD_GB", "Price_euros"]


# %% AUDIT
def audit_raw(raw):
    """Kiểm tra missing, chuỗi rỗng, kiểu dữ liệu và trùng lặp trước làm sạch."""
    schema = pd.DataFrame({
        "field": raw.columns,
        "dtype": [str(raw[c].dtype) for c in raw],
        "missing": [int(raw[c].isna().sum()) for c in raw],
        "missing_pct": [float(raw[c].isna().mean() * 100) for c in raw],
        "blank_strings": [int(raw[c].astype(str).str.strip().eq("").sum()) for c in raw],
        "unique_values": [int(raw[c].nunique()) for c in raw],
    })
    key = [c for c in raw if c != "laptop_ID"]
    audit = {
        "raw_rows": len(raw), "raw_columns": len(raw.columns),
        "missing_cells": int(raw.isna().sum().sum()),
        "blank_strings": int(schema.blank_strings.sum()),
        "duplicate_ids": int(raw.laptop_ID.duplicated().sum()),
        "exact_duplicate_rows": int(raw.duplicated().sum()),
        "duplicates_without_id": int(raw.duplicated(subset=key).sum()),
    }
    return schema, audit


# %% CLEAN
def parse_memory(text):
    """Tách từng ổ đĩa; TB = 1000 GB theo quy ước dung lượng thập phân.

    Flash Storage và Hybrid được giữ riêng, không tự xem là SSD/HDD.
    Hỗ trợ ổ kép, hai ổ cùng loại, khoảng trắng kép và dung lượng thập phân.
    """
    result = {"SSD_GB": 0.0, "HDD_GB": 0.0, "Flash_GB": 0.0, "Hybrid_GB": 0.0}
    names = {"SSD": "SSD_GB", "HDD": "HDD_GB", "Flash Storage": "Flash_GB", "Hybrid": "Hybrid_GB"}
    for part in str(text).split("+"):
        match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(GB|TB)\s+(SSD|HDD|Flash Storage|Hybrid)\s*", part)
        if not match:
            raise ValueError(f"Không tách được Memory: {text!r}")
        size, unit, kind = match.groups()
        result[names[kind]] += float(size) * (1000 if unit == "TB" else 1)
    return result


def clean_data(raw, deduplicate=True):
    """Chuẩn hóa đơn vị, tách cấu hình; giữ nguyên các trường gốc để đối chiếu."""
    df = raw.copy(deep=True)
    for c in df.columns:
        if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c]):
            df[c] = df[c].str.strip()
    if deduplicate:
        # Một quan sát là bản ghi cấu hình-giá, không phải giao dịch hay số máy bán.
        df = df.drop_duplicates(subset=[c for c in raw if c != "laptop_ID"]).copy()
    df = df.reset_index(drop=True)
    df["Ram_GB"] = pd.to_numeric(df.Ram.str.extract(r"^(\d+)GB$", expand=False), errors="raise")
    df["Weight_kg"] = pd.to_numeric(df.Weight.str.extract(r"^(\d+(?:\.\d+)?)kg$", expand=False), errors="raise")
    resolution = df.ScreenResolution.str.extract(r"(\d+)x(\d+)")
    df["ScreenWidth_px"] = pd.to_numeric(resolution[0], errors="raise")
    df["ScreenHeight_px"] = pd.to_numeric(resolution[1], errors="raise")
    df["PPI"] = np.hypot(df.ScreenWidth_px, df.ScreenHeight_px) / df.Inches
    df["Touchscreen"] = df.ScreenResolution.str.contains("Touchscreen", case=False, regex=False)
    df["IPS"] = df.ScreenResolution.str.contains("IPS", case=False, regex=False)
    df["Cpu_GHz"] = pd.to_numeric(df.Cpu.str.extract(r"(\d+(?:\.\d+)?)GHz", expand=False), errors="raise")
    df["Cpu_brand"] = df.Cpu.str.split().str[0]
    df["Gpu_brand"] = df.Gpu.str.split().str[0]
    memory = pd.DataFrame(df.Memory.map(parse_memory).tolist(), index=df.index)
    df = pd.concat([df, memory], axis=1)
    df["Has_SSD"] = df.SSD_GB.gt(0)
    # IQR chỉ gắn cờ để kiểm tra, không tự xóa phân khúc laptop cao cấp.
    q1, q3 = df.Price_euros.quantile([0.25, 0.75])
    lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    df["Price_IQR_flag"] = (df.Price_euros < lower) | (df.Price_euros > upper)
    required_positive = ["Price_euros", "Ram_GB", "Weight_kg", "Inches", "PPI", "Cpu_GHz"]
    if df[required_positive].isna().any().any() or not df[required_positive].gt(0).all().all():
        raise ValueError("Có giá trị thiếu hoặc không dương sau khi tách dữ liệu.")
    return df


# %% STATISTICS
def holm_adjust(pvalues):
    """Điều chỉnh Holm cho ba kiểm định chính, kiểm soát sai số theo họ kiểm định."""
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    adjusted = np.empty(len(p))
    adjusted[order] = np.minimum(1.0, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    return adjusted


def hypothesis_tests(df):
    """Các giả thuyết khám phá; p-value không chứng minh quan hệ nhân quả."""
    # H1: H0 rho=0; H1 rho>0. Spearman phù hợp quan hệ đơn điệu và biến RAM rời rạc.
    ram_test = stats.spearmanr(df.Ram_GB, df.Price_euros, alternative="greater")
    # H2: H0 hai phân phối giống nhau; H1 giá nhóm SSD có xu hướng cao hơn.
    x = df.loc[df.Has_SSD, "Price_euros"]
    y = df.loc[~df.Has_SSD, "Price_euros"]
    ssd_test = stats.mannwhitneyu(x, y, alternative="greater", method="asymptotic")
    # H3: Kiểm định tổng thể sáu phân phối theo TypeName; không kết luận từng cặp.
    groups = [g.Price_euros.to_numpy() for _, g in df.groupby("TypeName", sort=True)]
    if min(map(len, groups)) < 5:
        raise ValueError("Nhóm TypeName quá nhỏ cho xấp xỉ Kruskal-Wallis.")
    type_test = stats.kruskal(*groups)
    rows = [
        {"hypothesis": "H1 RAM-price", "test": "Spearman greater", "statistic": float(ram_test.statistic), "p_raw": float(ram_test.pvalue), "effect": float(ram_test.statistic), "effect_name": "Spearman rho"},
        {"hypothesis": "H2 SSD-price", "test": "Mann-Whitney greater", "statistic": float(ssd_test.statistic), "p_raw": float(ssd_test.pvalue), "effect": float(ssd_test.statistic / (len(x) * len(y))), "effect_name": "P(SSD>non-SSD)+0.5*P(tie)"},
        {"hypothesis": "H3 type-price", "test": "Kruskal-Wallis", "statistic": float(type_test.statistic), "p_raw": float(type_test.pvalue), "effect": float(max(0, (type_test.statistic - len(groups) + 1) / (len(df) - len(groups)))), "effect_name": "epsilon squared H"},
    ]
    table = pd.DataFrame(rows)
    table["p_holm"] = holm_adjust(table.p_raw)
    table["reject_H0_at_0.05"] = table.p_holm < ALPHA
    return table


def group_summary(df, field):
    """Luôn ghi cỡ mẫu để tránh suy rộng từ nhóm chỉ có vài bản ghi."""
    return df.groupby(field, observed=True).Price_euros.agg(n="size", mean="mean", median="median", minimum="min", maximum="max").reset_index()


def analyze(df):
    """Tạo thống kê và khoảng bootstrap mô tả chênh lệch trung vị SSD."""
    q1, q3 = df.Price_euros.quantile([0.25, 0.75])
    ssd = df.loc[df.Has_SSD, "Price_euros"].to_numpy()
    other = df.loc[~df.Has_SSD, "Price_euros"].to_numpy()
    rng = np.random.default_rng(SEED)
    # Bootstrap 2000 lần; khoảng phân vị 95%, giả định các bản ghi độc lập.
    differences = np.array([
        np.median(rng.choice(ssd, len(ssd), replace=True)) - np.median(rng.choice(other, len(other), replace=True))
        for _ in range(2000)
    ])
    return {
        "clean_rows": len(df), "companies": int(df.Company.nunique()),
        "price_mean": float(df.Price_euros.mean()), "price_median": float(df.Price_euros.median()),
        "price_min": float(df.Price_euros.min()), "price_max": float(df.Price_euros.max()),
        "price_q1": float(q1), "price_q3": float(q3), "price_skew": float(df.Price_euros.skew()),
        "iqr_lower": float(q1 - 1.5 * (q3 - q1)), "iqr_upper": float(q3 + 1.5 * (q3 - q1)),
        "iqr_flagged": int(df.Price_IQR_flag.sum()),
        "ssd_n": len(ssd), "non_ssd_n": len(other),
        "ssd_median": float(np.median(ssd)), "non_ssd_median": float(np.median(other)),
        "ssd_median_diff": float(np.median(ssd) - np.median(other)),
        "ssd_median_diff_ci95": [float(v) for v in np.quantile(differences, [0.025, 0.975])],
        "ram_rho": float(stats.spearmanr(df.Ram_GB, df.Price_euros).statistic),
        "ppi_rho": float(stats.spearmanr(df.PPI, df.Price_euros).statistic),
        "weight_rho": float(stats.spearmanr(df.Weight_kg, df.Price_euros).statistic),
    }


def sensitivity_analysis(raw, clean):
    """So sánh kết quả có trùng, bỏ trùng, và bỏ cờ IQR (chỉ đối chiếu)."""
    scenarios = {"raw_with_duplicates": clean_data(raw, False), "deduplicated_main": clean,
                 "without_IQR_flags_sensitivity_only": clean.loc[~clean.Price_IQR_flag].copy()}
    rows = []
    for name, data in scenarios.items():
        h = hypothesis_tests(data)
        x, y = data.loc[data.Has_SSD, "Price_euros"], data.loc[~data.Has_SSD, "Price_euros"]
        rows.append({"scenario": name, "n": len(data), "median_eur": data.Price_euros.median(),
                     "ram_rho": h.loc[0, "effect"], "ssd_median_gap_eur": x.median() - y.median(),
                     "H1_p_holm": h.loc[0, "p_holm"], "H2_p_holm": h.loc[1, "p_holm"], "H3_p_holm": h.loc[2, "p_holm"]})
    return pd.DataFrame(rows)


# %% CHARTS
def make_figures(df, output):
    """Mỗi hình trả lời một câu hỏi, có đơn vị và cỡ mẫu trong nhãn."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 110, "savefig.dpi": 180})
    blue, orange = "#2563a6", "#d67523"

    def save(fig, name):
        fig.savefig(output / name, bbox_inches="tight", facecolor="white")
        plt.close(fig)

    # Hình 1: Phân phối giá và cờ ngoại lệ IQR.
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), constrained_layout=True)
    axes[0].hist(df.Price_euros, bins=35, color=blue, edgecolor="white")
    axes[0].axvline(df.Price_euros.mean(), color=orange, label=f"Mean = {df.Price_euros.mean():,.0f}")
    axes[0].axvline(df.Price_euros.median(), color="#333333", linestyle="--", label=f"Median = {df.Price_euros.median():,.0f}")
    axes[0].set(xlabel="Giá (EUR)", ylabel="Số bản ghi", title=f"Phân phối giá (n={len(df):,})")
    axes[0].legend(fontsize=8)
    axes[1].boxplot(df.Price_euros, vert=False, widths=0.35, patch_artist=True,
                    boxprops={"facecolor": "#bfdbfe"}, medianprops={"color": "#111827"})
    axes[1].set(xlabel="Giá (EUR)", yticks=[], title="Giá trị xa theo quy tắc 1,5 IQR")
    save(fig, "01_price_distribution.png")

    # Hình 2: RAM và giá; giữ các nhóm nhỏ nhưng hiển thị rõ n.
    ram_levels = sorted(df.Ram_GB.unique())
    fig, ax = plt.subplots(figsize=(9.4, 4.3), constrained_layout=True)
    ax.boxplot([df.loc[df.Ram_GB.eq(v), "Price_euros"] for v in ram_levels], patch_artist=True,
               boxprops={"facecolor": "#bfdbfe"}, medianprops={"color": "#111827"})
    ax.set_xticks(range(1, len(ram_levels) + 1), [f"{v} GB\n(n={int(df.Ram_GB.eq(v).sum())})" for v in ram_levels])
    ax.set(xlabel="Dung lượng RAM", ylabel="Giá (EUR)", title="Giá phân bố thế nào theo RAM?")
    save(fig, "02_ram_price.png")

    # Hình 3: Có SSD bao gồm SSD đơn và SSD kết hợp ổ khác.
    fig, ax = plt.subplots(figsize=(7.5, 4), constrained_layout=True)
    groups = [df.loc[~df.Has_SSD, "Price_euros"], df.loc[df.Has_SSD, "Price_euros"]]
    ax.boxplot(groups, patch_artist=True, boxprops={"facecolor": "#fed7aa"}, medianprops={"color": "#111827"})
    ax.set_xticks([1, 2], [f"Không có SSD\n(n={len(groups[0])})", f"Có SSD\n(n={len(groups[1])})"])
    ax.set(ylabel="Giá (EUR)", title="Giá theo sự hiện diện của SSD")
    save(fig, "03_ssd_price.png")

    # Hình 4: Các loại laptop; thứ tự theo trung vị chỉ để mô tả.
    types = group_summary(df, "TypeName").sort_values("median")
    fig, ax = plt.subplots(figsize=(9.4, 4.4), constrained_layout=True)
    ax.boxplot([df.loc[df.TypeName.eq(v), "Price_euros"] for v in types.TypeName], vert=False,
               patch_artist=True, boxprops={"facecolor": "#bfdbfe"}, medianprops={"color": "#111827"})
    ax.set_yticks(range(1, len(types) + 1), [f"{r.TypeName} (n={r.n})" for r in types.itertuples()])
    ax.set(xlabel="Giá (EUR)", title="Phân bố giá theo loại laptop")
    save(fig, "04_type_price.png")

    # Hình 5: Chỉ so sánh trực quan hãng có ít nhất 20 bản ghi.
    brands = group_summary(df, "Company").query("n >= 20").sort_values("median")
    fig, ax = plt.subplots(figsize=(9.2, 4.3), constrained_layout=True)
    ax.barh(brands.Company, brands["median"], color=blue)
    for i, r in enumerate(brands.itertuples()):
        ax.text(r.median + 15, i, f"{r.median:,.0f} (n={r.n})", va="center", fontsize=9)
    ax.set_xlim(0, brands["median"].max() * 1.32)
    ax.set(xlabel="Trung vị giá (EUR)", title="Trung vị theo hãng có n ≥ 20")
    save(fig, "05_company_price.png")

    # Hình 6: Scatter PPI-giá; màu RAM giúp thấy cấu hình đi kèm nhau.
    fig, ax = plt.subplots(figsize=(9, 4.2), constrained_layout=True)
    points = ax.scatter(df.PPI, df.Price_euros, c=df.Ram_GB, s=15, alpha=0.5, cmap="viridis", vmin=2, vmax=32)
    fig.colorbar(points, ax=ax, label="RAM (GB, màu giới hạn ở 32)")
    ax.set(xlabel="Mật độ điểm ảnh (PPI)", ylabel="Giá (EUR)", title="Màn hình sắc nét hơn đi cùng mức giá nào?")
    save(fig, "06_ppi_price.png")

    # Hình 7: Tương quan Spearman; loại ID vì đó chỉ là mã định danh.
    corr = df[NUMERIC_FEATURES].corr(method="spearman")
    labels = ["RAM", "Cân nặng", "Inches", "PPI", "CPU GHz", "SSD GB", "HDD GB", "Giá EUR"]
    fig, ax = plt.subplots(figsize=(8, 6.1), constrained_layout=True)
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(labels)), labels, rotation=40, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            v = corr.iloc[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", color="white" if abs(v) > 0.55 else "#111827", fontsize=9)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Spearman rho")
    ax.set_title("Liên hệ đơn điệu giữa các thuộc tính")
    save(fig, "07_spearman_heatmap.png")


# %% OUTPUT
def run_project(root):
    """Tái tạo dữ liệu sạch, bảng, hình và kết quả thống kê có thể kiểm tra."""
    root = Path(root)
    source = root / "data/raw/laptop_price.csv"
    raw = pd.read_csv(source, encoding="latin-1")
    schema, audit = audit_raw(raw)
    df = clean_data(raw)
    summary = {**audit, **analyze(df), "source_url": SOURCE_URL,
               "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "versions": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__,
                            "scipy": scipy.__version__, "matplotlib": matplotlib.__version__}}
    tables = root / "reports/tables"
    tables.mkdir(parents=True, exist_ok=True)
    (root / "data/processed").mkdir(parents=True, exist_ok=True)
    df.to_csv(root / "data/processed/laptop_clean.csv", index=False, encoding="utf-8-sig")
    schema.to_csv(tables / "01_data_audit.csv", index=False)
    hypothesis_tests(df).to_csv(tables / "02_hypothesis_tests.csv", index=False)
    for field in ["Ram_GB", "Company", "TypeName", "Has_SSD"]:
        group_summary(df, field).to_csv(tables / f"group_{field}.csv", index=False)
    sensitivity_analysis(raw, df).to_csv(tables / "03_sensitivity.csv", index=False)
    key = [c for c in raw if c != "laptop_ID"]
    raw.loc[raw.duplicated(subset=key, keep=False)].to_csv(tables / "04_duplicate_evidence.csv", index=False)
    df.loc[df.Price_IQR_flag].to_csv(tables / "05_IQR_flagged_retained.csv", index=False)
    df[NUMERIC_FEATURES].corr(method="spearman").to_csv(tables / "06_spearman_correlations.csv")
    (root / "reports/results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    make_figures(df, root / "reports/figures")
    return raw, df, summary


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    _, _, result = run_project(project_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
