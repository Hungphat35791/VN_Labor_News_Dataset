# Hướng dẫn kiểm định nhãn liên quan và chủ đề

## 1. Mục tiêu và phạm vi

Kiểm tra bằng người đọc liệu bài báo có thuộc phạm vi lao động, việc làm tại Việt Nam hay không, và nhãn chủ đề A–L tự động có phản ánh đúng trọng tâm bài viết không. Nhãn tự động và gợi ý AI chỉ là thông tin tham khảo, không phải ground truth.

Mẫu lịch sử được tạo trực tiếp từ authoritative CSV bằng `5_process/src/create_manual_label_sample.py`: 56 dòng phân tầng theo `topic_primary` và một ví dụ ưu tiên `VNLAB-000002` (57 dòng tổng). Riêng `data/processed/legacy_borderline_manual_labels.csv` ghi lại 56 quyết định của pool ngoài dataset chính; đây là artifact lịch sử riêng và không được nhập vào mẫu mới. `3_du_lieu_phu/borderline_for_review.csv` không khớp các bản ghi của authoritative dataset và không được dùng làm nguồn mẫu (`ISS-008`).

Mẫu kiểm định mới gồm 620 bài tại `5_process/data/interim/relevance_review_sample.csv`, được tạo bằng `create_relevance_review_sample.py`: 200 dự đoán `RELEVANT`, 220 `IRRELEVANT`, 200 `REVIEW_REQUIRED`, seed 42. Đây là mẫu phân tầng theo trạng thái dự đoán P4.07, chỉ phục vụ audit; không thay thế hay ghi đè mẫu lịch sử 57 dòng hoặc sidecar 56 bài. Chuẩn gán nhãn thủ công cho mẫu 620 bài vẫn là các nhãn relevance và taxonomy A–L của tài liệu này, không phải 10 topic P4.06. Mẫu audit không đại diện phân bố lớp tự nhiên và không thể tự xác lập prevalence toàn corpus hoặc metric hiệu năng không thiên lệch nếu thiếu thiết kế lấy mẫu phù hợp cùng nhãn tham chiếu đáng tin cậy.

## 2. Quy trình cho từng bài

1. Đọc tiêu đề và nội dung đủ để hiểu trọng tâm, bối cảnh Việt Nam và đối tượng được nói đến.
2. Tự đánh giá mức liên quan trước khi xem gợi ý AI; không suy luận chỉ từ từ khóa, `topic_primary` hoặc `relevance_score`.
3. Chọn đúng một `relevance_manual` theo mục 3.
4. Với bài Relevant hoặc Borderline, chọn một chủ đề chính A–L theo mục 4. Nếu không thể phân biệt chủ đề chính, chọn `Uncertain` cho relevance và giải thích.
5. Ghi lý do ngắn dựa trên bằng chứng trong bài; không kết luận vi phạm pháp luật chỉ vì bài nêu cáo buộc.
6. Chỉ sau khi tự kiểm tra xong, nếu có gợi ý AI hợp lệ gắn với cùng `article_id`, có thể đối chiếu các cột `ai_suggested_*`. Nếu khác gợi ý, giữ quyết định dựa trên bài và ghi rõ lý do. Các cột gợi ý AI trong mẫu hiện tại đang để trống.
7. Điền mã người kiểm định thật và ngày hoàn tất kiểm tra theo `YYYY-MM-DD`.

Không sửa các trường gốc, không gán sentiment, và không chép đề xuất AI sang trường thủ công nếu chưa tự xác nhận.

## 3. Nhãn mức độ liên quan

`relevance_manual` nhận chính xác một trong các giá trị:

- `Relevant`: Trọng tâm bài trực tiếp nói về việc làm, thị trường lao động, người lao động, quan hệ lao động, điều kiện/quyền lợi lao động hoặc chính sách lao động tại Việt Nam.
- `Borderline`: Có liên hệ đáng kể nhưng gián tiếp, bối cảnh hoặc tác động đến việc làm chưa cụ thể. Ví dụ: dự án/khu công nghiệp chỉ nêu khả năng tạo việc làm nhưng chưa có thông tin tuyển dụng hay lao động thực tế.
- `Not relevant`: Từ khóa lao động xuất hiện nhưng bài không bàn đáng kể về lao động/việc làm trong phạm vi dự án; ví dụ thể thao có từ “sa thải” theo nghĩa huấn luyện viên bị câu lạc bộ cho thôi việc.
- `Uncertain`: Nội dung thiếu, mâu thuẫn hoặc không đủ bằng chứng để quyết định. Không dùng nhãn này chỉ vì bài khó phân loại chủ đề.

Đánh giá theo nội dung và trọng tâm của bài, không theo việc bài có chứa một từ neo hay từ khóa A–L.

## 4. Chủ đề chính A–L

`topic_manual` ghi **một mã và tên chủ đề đúng như danh mục dưới đây** cho bài Relevant hoặc Borderline:

| Mã | Tên chủ đề | Chọn khi trọng tâm bài là |
|---|---|---|
| A | Thị trường lao động Việt Nam | Cung/cầu lao động, tuyển dụng, thiếu nhân lực, tạo việc làm hoặc dịch chuyển lao động |
| B | Thất nghiệp, mất việc, cắt giảm nhân sự | Thất nghiệp, mất việc, giảm giờ làm hoặc cắt giảm lao động |
| C | Tiền lương, bảo hiểm, quyền lợi | Lương, thưởng, BHXH/BHTN/BHYT hoặc quyền lợi và trợ cấp |
| D | Hợp đồng lao động, nghỉ việc, sa thải | Hợp đồng, chấm dứt việc làm, nghỉ việc, kỷ luật hoặc nghỉ hưu trong quan hệ lao động |
| E | Điều kiện làm việc, an toàn lao động | Giờ làm, tăng ca, an toàn, tai nạn, môi trường làm việc, nhà ở/suất ăn gắn với lao động |
| F | Công đoàn, đình công, tranh chấp lao động | Công đoàn, đại diện người lao động, thương lượng, đình công hoặc tranh chấp |
| G | Nhóm lao động dễ bị ảnh hưởng | Một nhóm lao động cụ thể và đặc thù/khó khăn của nhóm đó là trọng tâm |
| H | Chính sách việc làm, đào tạo nghề, an sinh xã hội | Chính sách việc làm, đào tạo/chuyển đổi nghề, hỗ trợ và an sinh cho người lao động |
| I | Lừa đảo tuyển dụng, bóc lột lao động | Lừa đảo tuyển dụng, cưỡng bức/bóc lột lao động hoặc mua bán người gắn với lao động |
| J | Kinh tế và yếu tố tác động đến việc làm | Kinh tế, ngành, doanh nghiệp hoặc công nghệ tác động đáng kể đến việc làm/lao động |
| K | Pháp luật lao động và thực thi | Quy định, thanh tra, xử phạt, thực thi hoặc tranh tụng về pháp luật lao động |
| L | Tâm lý người lao động, chất lượng việc làm | Sức khỏe tinh thần, trải nghiệm, hài lòng, kiệt sức hoặc chất lượng việc làm |

### Ranh giới áp dụng giữa các nhóm chủ đề

- Phân biệt B và D theo bản chất sự kiện: thất nghiệp, mất việc ngoài ý muốn, giảm giờ làm hoặc cắt giảm lao động thuộc B; tự nguyện nghỉ việc, chuyển việc, chấm dứt hợp đồng hoặc nghỉ hưu trong quan hệ việc làm thuộc D. Không gán B chỉ vì bài dùng cụm từ “nghỉ việc”.
- Tin về cán bộ, công chức không tự động thuộc phạm vi lao động chỉ vì có nhắc lương hoặc thôi việc. Tin thuần về bổ nhiệm, điều động, thôi chức, đơn xin nghỉ của một cá nhân hoặc mức lương gắn riêng với một chức danh hành chính thường là `Not relevant` nếu trọng tâm chỉ là quản trị nhân sự/hành chính. Xem xét C hoặc D khi bài tập trung thực chất vào chính sách lương, quyền lợi hoặc điều kiện việc làm áp dụng cho một nhóm người lao động/công chức, hoặc một vấn đề quan hệ việc làm rộng hơn; dựa vào trọng tâm bài, không chỉ một con số lương hay khoản trợ cấp cá nhân.
- Với tin hình sự có nạn nhân là người lao động, nghề nghiệp của nạn nhân tự nó không đủ để gán E. Cân nhắc E khi sự việc xảy ra trong lúc thực hiện công việc hoặc có mối liên hệ trực tiếp, đáng kể với tương tác/nhiệm vụ công việc; nếu bài chỉ nêu nghề như thông tin tiểu sử thì không xem là chủ đề an toàn lao động. Một vụ việc đơn lẻ chỉ phản ánh rủi ro liên quan công việc mà không bàn điều kiện hay biện pháp an toàn thường tối đa là `Borderline`.
- Chỉ chọn F khi hoạt động đại diện của công đoàn, thương lượng, đình công hoặc tranh chấp lao động là nội dung thực chất của bài. Việc nhân vật là cán bộ công đoàn hoặc bài có trích dẫn tổ chức công đoàn không tự nó tạo thành chủ đề F.
- Chỉ chọn K cho quy định và thực thi pháp luật lao động. Quy định về quyền riêng tư/dữ liệu của khách hàng hoặc quy định ngành khác không thành K chỉ vì tài xế/người lao động là đối tượng phải tuân thủ.
- Phân biệt C với hỗ trợ cộng đồng: quà tặng một lần từ bên ngoài quan hệ lao động không phải tiền lương hay quyền lợi lao động của người sử dụng lao động. Nếu việc hỗ trợ người lao động là trọng tâm nhưng không phải chế độ lao động/an sinh có tính chính sách, có thể cân nhắc H với mức `Borderline`; nếu người lao động chỉ được nhắc thoáng qua thì không gán nhãn liên quan vì từ khóa.

Nếu nhiều nhóm cùng xuất hiện, chọn nhóm phản ánh trọng tâm chính; nêu nhóm cạnh tranh trong `review_reason`. Không tạo mã mới. Với `Not relevant` hoặc `Uncertain`, để `topic_manual` trống và giải thích trong `review_reason`; không dùng một giá trị ngoài danh mục A–L.

## 5. Trường cần điền và quy tắc hoàn tất

- `relevance_manual`: một nhãn ở mục 3.
- `topic_manual`: một chủ đề A–L nếu relevance là Relevant/Borderline; để trống nếu Not relevant/Uncertain.
- `review_reason`: lý do cụ thể, có căn cứ từ tiêu đề/nội dung; ghi bất đồng với nhãn tự động hoặc gợi ý AI nếu có.
- `reviewer_id`: mã người thật đã đọc và quyết định; không dùng tên/mã AI.
- `review_date`: ngày người đó hoàn tất review, định dạng `YYYY-MM-DD`.

Một dòng chỉ được tính là đã review khi các trường bắt buộc trên hợp lệ. Không điền trước reviewer/date hoặc coi giá trị gợi ý AI là nhãn thủ công.

Với mẫu 620 bài, CSV dùng đúng chín cột theo thứ tự: `article_id`, `title`, `content`,
`relevance_manual`, `topic_manual`, `review_reason`, `reviewer_id`, `review_date`,
`review_status`. Trước review, năm trường `relevance_manual`, `topic_manual`,
`review_reason`, `reviewer_id`, `review_date` để trống. `topic_manual` ghi một mã A–L
kèm tên tương ứng; để trống cho `Not relevant` và `Uncertain`. Không tự động chuyển đổi
nhãn 10-topic P4.06 sang A–L.

`review_status` là trường vận hành độc lập với `relevance_manual`; giá trị khởi tạo là
`PENDING`. Các giá trị workflow được dùng trong mẫu:

- `PENDING`: chưa bắt đầu review.
- `IN_PROGRESS`: đang review.
- `COMPLETED`: đã hoàn tất và kiểm tra các trường bắt buộc.
- `NEEDS_ADJUDICATION`: cần phân xử bất đồng hoặc ca chưa thống nhất.

## 6. Kiểm soát chất lượng và giới hạn

- Dùng mẫu phân tầng theo chủ đề tự động để bao phủ các nhóm, bổ sung trường hợp nhiễu đã biết và lưu lại cách lấy mẫu/số lượng từng tầng. Đây là nhãn yếu dùng để chọn tầng, không phải ground truth.
- Với mẫu audit 620 bài, lưu nguyên trạng seed 42 và phân tầng 200/220/200 theo P4.07 để tái lập; các dự đoán chỉ dùng để lấy mẫu, không xuất hiện trong file reviewer và không được dùng thay nhãn thủ công.
- Mẫu 620 bài không đại diện phân bố lớp tự nhiên. Không dùng nó một mình để suy ra prevalence toàn corpus hoặc metric hiệu năng không thiên lệch nếu không có sampling design phù hợp và nhãn tham chiếu đáng tin cậy.
- Với review chéo, hai người cần gán độc lập trên cùng một tập con trước khi thảo luận; lưu bất đồng và chỉ tính độ đồng thuận trên nhãn độc lập.
- Mẫu 56 bài phân tầng cộng một trường hợp ưu tiên không phải mẫu ngẫu nhiên đại diện; không suy rộng tỷ lệ sai hoặc tính precision/recall toàn tập từ mẫu này.
- Không suy ra kết luận pháp lý hoặc sentiment từ nhãn liên quan/chủ đề.
