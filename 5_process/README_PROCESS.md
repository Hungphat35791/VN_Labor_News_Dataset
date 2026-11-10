# Process — cấu trúc và cách chạy

Thư mục này chứa đầu ra Process; dữ liệu Collecting trong `1_du_lieu_chinh/` chỉ đọc và không được ghi đè.

## Cấu trúc

- `src/`: module xử lý.
- `tests/`: unit tests.
- `config/`: hướng dẫn và quy ước gán nhãn.
- `data/processed/`: mẫu gán nhãn chờ người kiểm định.
- `data/interim/`: đầu ra trung gian, metadata đã chuẩn hóa và audit trùng.
- `logs/`: change log, issue log và lỗi metadata.
- `reports/`: báo cáo rà soát, audit metadata và chất lượng nhãn.
- `reference/person5_source_workbooks/`: workbook bàn giao gốc của Người 5, chỉ lưu để tham chiếu; không dùng làm đầu vào xử lý.
- `splits/`: manifest phân chia dữ liệu theo thời gian, chỉ gồm ID và metadata audit.

## Cài đặt và chạy pipeline Process

Cài dependency thống nhất cho các bước Process (nếu môi trường chưa có):

```powershell
python -m pip install -r 5_process/requirements.txt
```

Từ thư mục gốc repository, chạy từng lệnh riêng theo thứ tự. Kiểm thử đơn vị là bước đầu; chỉ chạy pipeline toàn bộ khi tests đạt. Nếu lệnh nào báo lỗi, dừng ở bước đó, xử lý lỗi rồi mới chạy tiếp:

```powershell
python -m unittest discover -s 5_process/tests -p "test_*.py" -v
python -m unittest test_text_cleaning -v
```

```powershell
python 5_process/src/01_profile_data.py
```

```powershell
python 5_process/src/02_validate_schema.py
```

```powershell
python 5_process/src/03_clean_metadata.py
```

```powershell
python 5_process/src/text_cleaning.py
```

```powershell
python 5_process/src/create_splits_and_leakage_audit.py
```

```powershell
python 5_process/src/validate_process_integration.py
```

```powershell
python 5_process/src/create_manual_label_sample.py
python 5_process/src/validate_manual_labels.py
```

`01_profile_data.py` lập hồ sơ đầu vào; `02_validate_schema.py` xác thực schema và ghi issue. Các bước sau đều đọc CSV chuẩn `1_du_lieu_chinh/vn_labor_news_dataset.csv`; không xử lý từ Excel và không ghi đè dữ liệu Collecting.

`validate_process_integration.py` đối chiếu SHA-256, số dòng/ID giữa raw và các đầu ra metadata, text cleaning và split; kiểm tra trường raw được giữ nguyên trong CSV làm sạch và các cột `_clean` khớp hàm làm sạch. Kết quả được lưu tại `reports/integration_validation.json`. Nếu một bước trả mã lỗi khác 0, dừng pipeline và xử lý lỗi trước khi chạy tiếp.

Issue dùng chung của nhóm nằm ở `logs/issue_log.csv`; `reports/process_quality_report.md` và `reports/integration_checklist.md` là trạng thái tích hợp mới nhất. Báo cáo phân biệt rõ phần nghiệm thu kỹ thuật của Người 1 với các review thủ công còn chờ.

## Metadata và audit trùng lặp

Chạy lại từ CSV nguồn chỉ đọc:

```powershell
python 5_process/src/03_clean_metadata.py
```

Module sinh `data/interim/metadata_clean.parquet`/`.csv`, `data/interim/duplicate_review.csv`, các log metadata và `reports/metadata_audit.md`. Bản nguồn từ Người 2 được tích hợp cùng test; các output metadata được tái tạo từ CSV dự án để bảo đảm chúng khớp với code hiện tại.

Các quyết định trong `config/duplicate_decisions.csv` và `config/outlier_review.csv` chỉ chứa kết luận đã được người phụ trách xác nhận; module kiểm tra reviewer, schema, nhãn hợp lệ và khóa review trước khi áp dụng. Các bản nháp AI trong `config/review_drafts/` và `reports/review_drafts/` chỉ là tài liệu tham khảo, không được pipeline tự động nạp, không thay thế xác nhận của người review và không được dùng để loại bài. Công việc audit của Người 2 đã hoàn tất; xem kết quả và giới hạn trong `reports/metadata_audit.md`.

### URL duplicate candidates (P4.02)

Sinh danh sách ứng viên URL trùng, không sửa CSV nguồn:

```powershell
python 5_process/src/detect_url_duplicates.py
```

Mặc định đọc `1_du_lieu_chinh/vn_labor_news_dataset.csv` và ghi
`5_process/data/interim/url_duplicate_candidates.csv` cùng báo cáo
`5_process/reports/url_duplicate_report.json`. Có thể chỉ định `--input`, `--output`
và `--report`. Báo cáo ghi hash đầu vào/ứng viên, số bài đã kiểm tra, phiên bản detector,
số cặp và số URL không hợp lệ. URL gốc được giữ trong các cột `original_url_1`/`original_url_2`; URL so
sánh chuẩn hóa thành HTTPS, host chữ thường, bỏ `www`, fragment và các tham số tracking
đã nhận diện, đồng thời bỏ dấu `/` cuối. Các query parameter khác được giữ nguyên và
giữ thứ tự. URL lỗi bị bỏ qua và số lượng được in ra; mỗi cặp phát hiện đều mang trạng
thái `REVIEW_REQUIRED`. Detector chỉ tạo ứng viên, không xác nhận trùng, xóa, sửa hoặc
gộp bài. Xem quy tắc đầy đủ tại `config/duplicate_taxonomy.md`.

### Exact content duplicate candidates (P4.03)

Sinh ứng viên trùng nội dung chính xác, không sửa CSV nguồn:

```powershell
python 5_process/src/detect_exact_duplicates.py
```

Mặc định đọc `1_du_lieu_chinh/vn_labor_news_dataset.csv`; ghi danh sách theo dòng bài tại
`5_process/data/interim/exact_duplicate_candidates.csv` và thống kê tại
`5_process/reports/exact_duplicate_report.json`. Có thể chỉ định `--input`, `--output`
và `--report`. Detector tính SHA-256 trên chuỗi `content` được đọc nguyên trạng từ CSV,
gom theo hash rồi so sánh chuỗi nội dung đầy đủ để tránh xác nhận nhầm do hash collision.
Không chuẩn hóa khoảng trắng, dấu câu hoặc Unicode; nội dung trống/whitespace-only bị
bỏ khỏi nhóm. Mỗi bài trong nhóm dùng chung `duplicate_group_id` và trạng thái
`REVIEW_REQUIRED`. Không tự động xác nhận, xóa, sửa hoặc gộp bài.
Trong JSON, `candidates_requiring_review` đếm số nhóm cần review;
`candidate_article_rows_requiring_review` đếm số dòng bài trong các nhóm đó.

### Near duplicate candidates (P4.04)

Tìm cặp bài có nội dung gần giống để con người review; không xác nhận duplicate hay
loại bài tự động:

```powershell
python 5_process/src/detect_near_duplicates.py
```

Mặc định đọc CSV chuẩn và ghi
`5_process/data/interim/near_duplicate_candidates.csv` cùng báo cáo
`5_process/reports/near_duplicate_report.json`. Có thể cấu hình cosine threshold trong
khoảng `(0, 1]`, mặc định `0.85`, bằng `--threshold` (ví dụ `--threshold 0.90`).
Detector tái sử dụng TF-IDF unigram/bigram và cosine similarity của audit metadata hiện
có; phép nhân ma trận sparse được xử lý theo khối và chỉ xét các cặp có similarity khác
0. Nội dung rỗng bị bỏ qua; cặp có `content` nguyên bản giống hệt được để cho P4.03.
Các cặp đầu ra có điểm, ngưỡng, method/version và trạng thái `REVIEW_REQUIRED`. Điểm cao
vẫn có thể phản ánh bài độc lập cùng đưa tin một sự kiện; cần review nội dung và ngữ cảnh.

### Duplicate candidate grouping (P4.05)

Gom các candidate từ P4.02–P4.04 thành nhóm để hỗ trợ review thủ công:

```powershell
python 5_process/src/group_duplicate_candidates.py
```

Mặc định đọc `data/interim/url_duplicate_candidates.csv`,
`data/interim/exact_duplicate_candidates.csv` và
`data/interim/near_duplicate_candidates.csv`. Ghi
`data/interim/duplicate_groups.csv` và `reports/duplicate_grouping_report.json`;
có thể thay các đầu vào/đầu ra bằng `--url-candidates`, `--exact-candidates`,
`--near-candidates`, `--output` và `--report`.

Các cặp URL/near là cạnh trong đồ thị; các thành viên của một exact-duplicate group
được nối thành các cặp có bằng chứng exact. Union-find tạo connected components, do đó
các liên kết bắc cầu (A-B, B-C) nằm trong cùng nhóm. ID nhóm được cấp ổn định theo thứ
tự article ID. CSV có một dòng mỗi bài, cùng `duplicate_group_id`, kích thước nhóm,
các loại/method và `candidate_pairs_json` giữ bằng chứng theo từng cặp. Trong JSON,
`total_candidate_pairs` là số cặp article ID không thứ tự duy nhất; nhóm hỗn hợp được
tính trong phân phối từng type của nhóm ở `duplicate_type_distribution`, nên tổng phân
phối này có thể lớn hơn số nhóm.

Thành phần liên thông chỉ phục vụ điều hướng review: cạnh yếu/ chưa kiểm duyệt có thể
kết nối nhiều bài, vì vậy nhóm không khẳng định mọi cặp thành viên đều duplicate. Tất cả
dòng vẫn là `REVIEW_REQUIRED`; không có bài nào bị xác nhận, xóa, sửa hoặc gộp tự động.
`VERSION_DUPLICATE` chỉ được giữ khi nguồn ứng viên nêu rõ `version_evidence`; công cụ
không suy diễn quan hệ phiên bản từ URL, độ tương tự hay ngày xuất bản. Lệnh chặn ghi đè
CSV nguồn và artifact/report P4.02–P4.04.

### Rule-based relevance (P4.07)

Chạy phân loại liên quan theo bộ luật bảo thủ, không đọc `relevance_status`,
`topic_primary`, `topic_secondary` hoặc `relevance_score` hiện có làm nhãn chuẩn:

```powershell
python 5_process/src/classify_relevance_rules.py
```

Mặc định đọc `1_du_lieu_chinh/vn_labor_news_dataset.csv`, ghi
`5_process/data/interim/relevance_results.csv` và
`5_process/reports/relevance_rule_report.json`. Có thể chỉ định `--input`, `--output`
và `--report`. Detector yêu cầu `article_id`, `title`, `content`; ID rỗng/trùng bị từ
chối. Mỗi ID hợp lệ tạo đúng một kết quả.

Văn bản chỉ được chuẩn hóa trong bộ nhớ để so khớp: Unicode được tách dấu, `đ` đổi thành
`d`, chữ thường hóa, dấu câu và khoảng trắng được quy về khoảng trắng. Dữ liệu gốc không
bị sửa. `matched_keywords` và `matched_rules` là JSON arrays có thể truy ngược theo
trường tiêu đề/nội dung và mã luật; `topic_labels` là danh sách mã phân cách bằng `;`.
Các cụm chuyên biệt (ví dụ BHXH/BHTN, hợp đồng lao động, đình công, tai nạn lao động)
có thể tạo `RELEVANT` và một hoặc nhiều nhãn. Từ/cụm yếu như “công nhân”, “lương”,
“bảo hiểm” hoặc “sa thải” đơn lẻ chỉ tạo `REVIEW_REQUIRED`, không tự đủ bằng chứng.
Nội dung rỗng cũng cần review; bài không có dấu hiệu lao động theo bộ luật được gán
`IRRELEVANT`. Trường hợp thể thao có “sa thải” được nhận diện là ngữ cảnh không lao động.

`review_status=AUTO_CLASSIFIED` đánh dấu quyết định tự động `RELEVANT`/`IRRELEVANT`;
`review_status=REVIEW_REQUIRED` đánh dấu ca cần người đọc. Các topic là nhãn ứng viên
theo luật P4.06, không phải kết quả đã được người review xác nhận và không thay thế
P4.08. Xem giới hạn và quy tắc tại `config/relevance_taxonomy.md`. Báo cáo thống kê
được tính từ kết quả thực tế; không có accuracy/precision/recall/F1 vì chưa có tập gold
đại diện và đủ tin cậy. Lệnh chặn ghi đè CSV nguồn và artifact P4.02–P4.06.
Mỗi dòng cũng ghi `taxonomy_version=1.0.0` cùng `classifier_version=1.0.0`.

### Manual audit sample for P4.07

Tạo/cập nhật mẫu kiểm định thủ công 620 bài, dùng A–L và bốn nhãn trong
`config/labeling_guideline.md` làm chuẩn chính thức cho người review:

```powershell
python 5_process/src/create_relevance_review_sample.py
```

Schema CSV đúng thứ tự gồm:
`article_id,title,content,relevance_manual,topic_manual,review_reason,reviewer_id,review_date,review_status`.
Năm trường nhãn/giải thích/người/ngày để trống; `review_status` khởi tạo là `PENDING`.
Reviewer tự điền `relevance_manual` bằng đúng một trong `Relevant`, `Borderline`,
`Not relevant`, `Uncertain`. Với Relevant/Borderline, điền đúng một chủ đề chính A–L
theo mã và tên trong guideline; với Not relevant/Uncertain để `topic_manual` trống.
`review_reason` phải có căn cứ trong bài; `reviewer_id` là người thật, `review_date`
dùng `YYYY-MM-DD`.

`review_status` là trạng thái công việc, không phải nhãn liên quan: `PENDING` = chưa
bắt đầu; `IN_PROGRESS` = đang review; `COMPLETED` = đã điền và kiểm tra đủ trường bắt
buộc; `NEEDS_ADJUDICATION` = cần người có thẩm quyền xử lý bất đồng/ca chưa thống nhất.
Không suy ra nhãn thủ công từ P4.07. File dành cho reviewer không chứa dự đoán hoặc
topic tự động.

Mẫu này tách biệt với mẫu lịch sử 56 bài (56 tầng `topic_primary` cộng một ví dụ ưu tiên
thành 57 dòng) và với sidecar 56 nhãn của pool ngoài dataset chính. Không thay thế hay
ghi đè các dữ liệu lịch sử đó. Mẫu 620 bài phân tầng theo trạng thái dự đoán P4.07 với
seed `42`: 200 `RELEVANT`, 220 `IRRELEVANT`, 200 `REVIEW_REQUIRED`, rồi trộn thứ tự.
Phân tầng nhằm audit các trạng thái, không đại diện phân bố lớp tự nhiên; không thể tự
xác lập prevalence toàn corpus hay metric hiệu năng không thiên lệch nếu thiếu thiết kế
lấy mẫu phù hợp và nhãn tham chiếu đáng tin cậy.

Báo cáo `5_process/reports/relevance_review_sample_report.json` ghi số dòng đầu vào,
số lượng có sẵn/yêu cầu/được chọn theo mỗi trạng thái, seed, số ID duy nhất, hash nguồn
và kết quả, thời điểm, schema review, thiếu hụt (nếu có) và giới hạn lấy mẫu. Nếu một
nhóm không đủ số lượng, script chỉ lấy số bản ghi thực có và ghi `shortfall_by_status`;
không tạo bản ghi giả. Có thể dùng `--source`, `--results`, `--output`, `--report` và
`--seed` để chỉ định đường dẫn/seed. Lệnh chặn va chạm với input/artifact P4.02–P4.07;
nếu sample hiện có chứa annotation hoặc tiến độ review khác `PENDING`, script từ chối
ghi đè để bảo vệ công việc người review.

#### Manual review batches

Tạo Batch 01 (dòng 1–50) theo thứ tự master sample:

```powershell
python 5_process/src/create_relevance_review_batch.py
```

Tạo Batch 02 (dòng 51–100) bằng cùng script:

```powershell
python 5_process/src/create_relevance_review_batch.py --batch-number 2
```

Mỗi batch được ghi thành `data/interim/relevance_review_batch_NN.csv`; báo cáo ID,
SHA-256 master sample và thời điểm tạo được ghi thành
`reports/relevance_review_batch_NN_report.json`. Script giữ nguyên chín cột, không tự
gán nhãn, và tạo các trường annotation trống cùng `review_status=PENDING`. Nếu file batch
hoặc báo cáo đích đã tồn tại, script từ chối ghi đè; cần kiểm tra và xử lý file đó riêng
để không làm mất annotation hay tiến độ review.

## Thống kê, split và bàn giao Modeling

Từ thư mục gốc, sinh lại thống kê, biểu đồ, manifest theo thời gian và audit ứng viên trùng:

```powershell
python 5_process/src/create_splits_and_leakage_audit.py
```

Lệnh đọc CSV nguồn ở chế độ chỉ đọc, kiểm tra schema/ID/ngày, và tạo `reports/process_statistics.md`, biểu đồ trong `reports/charts/`, các manifest trong `splits/`, `reports/split_validation.md` và `reports/handoff_to_modeling.md`. Mặc định train là trước 2025, validation là năm 2025, test từ 2026. Đây là lựa chọn mặc định để bàn giao, không phải xác nhận cuối của nhóm.

`topic_primary` là weak label tự động, không phải nhãn vàng. `split_manifest.csv` giữ nguyên mốc ngày để audit; script bổ sung `modeling_eligibility_manifest.csv`, gắn các bản ghi thuộc cặp/cụm đã biết giao split thành `review_hold` để chúng không đi vào train/evaluation trước khi được rà soát. Đây là heuristic, không chứng minh không còn leakage. Không huấn luyện mô hình trong bước này. Xem `reports/handoff_to_modeling.md` và `reports/split_validation.md` trước khi dùng manifest.

Người 6 có thể dùng `reports/process_quality_report.md`, `reports/process_statistics.md`, `reports/split_validation.md` và biểu đồ trong `reports/charts/` làm nguồn đã kiểm tra để tự soạn slide. Phần slide được bàn giao riêng, chưa nằm trong gói Process này.

## Làm sạch văn bản

Tạo `5_process/data/processed/articles_text_clean.csv`:

```powershell
python 5_process/src/text_cleaning.py
```

Module thêm `title_clean` và `content_clean`, giữ nguyên các cột gốc và không chỉnh sửa CSV nguồn. Văn bản được chuẩn hóa Unicode NFC; khoảng trắng và ký tự điều khiển được xử lý nhất quán. Zero-width space, BOM nằm trong văn bản và word joiner được đổi thành dấu cách; soft hyphen và các ký tự định dạng vô hình khác được bỏ. ZWJ/ZWNJ được giữ để không phá các cụm chữ hoặc emoji cần ký tự nối. Nếu CSV sai số trường, module báo lỗi và không thay thế đầu ra hiện có.

CSV đầu ra chứa toàn văn bài báo có bản quyền; không commit hoặc đẩy file này lên repository công khai. Tái tạo file khi cần từ CSV nguồn nội bộ.

## Trạng thái dữ liệu nhãn

`config/labeling_guideline.md` là chuẩn thủ công A–L. `create_manual_label_sample.py` có thể tái tạo mẫu lịch sử 57 dòng trực tiếp từ authoritative CSV: 56 dòng phân tầng theo `topic_primary` bằng thứ tự SHA-256 của `article_id` và một ví dụ ưu tiên `VNLAB-000002`. File `borderline_for_review.csv` không khớp authoritative dataset và không được dùng làm nguồn mẫu (`ISS-008`). Mẫu audit 620 dòng ở phần trên là một mẫu riêng, lấy theo trạng thái P4.07; không thay thế mẫu lịch sử hoặc sidecar nhãn 56 bài.

File `data/processed/legacy_borderline_manual_labels.csv` lưu 56 quyết định thủ công đã hoàn tất cho pool riêng `3_du_lieu_phu/borderline_for_review.csv`; sidecar chỉ có ID và các trường nhãn/review, không chứa nội dung bài. Tất cả 16 trường nguồn của 56 dòng khớp pool này sau chuẩn hóa kiểu xuống dòng. Người review được xác nhận là Hà Mạnh Trí, ngày review 2026-10-27. Pool 304 dòng không thuộc authoritative CSV hiện hành, vì vậy các nhãn này không được ghép vào mẫu 57 dòng hoặc dùng để đánh giá dataset chính. Xem chi tiết tại `reports/label_quality.md`.

Mẫu chính thức `data/processed/manual_label_sample.csv` hiện đã hoàn tất 57/57 dòng theo reviewer `RV004` ngày `2026-10-27`; kết quả đã qua validator strict. Báo cáo phân bố và giới hạn xem tại `reports/label_quality.md`.

`reports/review_drafts/manual_label_ai_suggestions.csv` là bản nháp AI tham khảo, không phải nguồn nhãn chính thức; không nhập tự động vào các cột `*_manual`.

Các CSV review chứa toàn văn bài báo nên được giữ cục bộ, không commit hoặc đưa lên repository công khai. `.gitignore` đã loại `manual_label_sample*.csv` khỏi Git.

Kiểm tra nguồn gốc, trường gốc, danh mục nhãn và trạng thái review:

```powershell
python 5_process/src/create_manual_label_sample.py
python 5_process/src/validate_manual_labels.py
```

Validator đối chiếu từng trường nguồn với authoritative CSV, kiểm tra quota phân tầng và báo số dòng còn chờ. Sau khi người kiểm định điền đủ mẫu, yêu cầu kiểm tra hoàn tất:

```powershell
python 5_process/src/validate_manual_labels.py --require-complete
```

Các file mẫu nhãn có chứa nội dung bài báo. Không đưa chúng hoặc dữ liệu toàn văn lên repository công khai.
