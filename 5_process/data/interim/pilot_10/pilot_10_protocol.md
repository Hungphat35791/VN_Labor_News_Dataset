# Quy trình Pilot Annotation 10 bài – Hai reviewer độc lập

## Mục tiêu

Thử nghiệm việc áp dụng `5_process/config/labeling_guideline.md` hiện hành trên một mẫu có chủ đích gồm 10 bài, để kiểm tra cách hiểu nhãn và topic, ghi nhận bất đồng và xác định các câu hỏi cần adjudication. Đây không phải mẫu đại diện thống kê và không dùng để suy rộng tỷ lệ cho toàn bộ dataset.

Các đề xuất trong `labeling_policy_clarification_proposal.md`, `labeling_policy_review_assessment.md` và các báo cáo audit chỉ giúp nhận diện ca khó; chúng **chưa được phê duyệt**, không sửa đổi guideline và không phải nhãn chuẩn.

## Chuẩn bị và tách biệt reviewer

- Mỗi reviewer chỉ nhận bản riêng của mình: `reviewer_1_sheet.csv` hoặc `reviewer_2_sheet.csv`. Không gửi chung thư mục chứa cả hai sheet cho reviewer và không cấp quyền xem file của người còn lại.
- Người điều phối giữ `pilot_10_articles.csv` và `pilot_10_selection_report.json`; không chia sẻ lý do chọn mẫu hoặc danh sách tình huống cần kiểm tra cho reviewer trước khi họ khóa quyết định độc lập, để tránh gợi ý hướng phân loại.
- Hai reviewer làm cùng 10 bài nhưng làm riêng, không trao đổi nhãn/lý do và không xem sheet còn lại cho đến khi cả hai đã nộp, khóa kết quả.
- Các CSV hiện được đặt cùng một thư mục vì mục đích lưu trữ; việc tách file tự nó **không** tạo rào cản truy cập. Người điều phối phải phân phối qua bản sao/quyền truy cập tách biệt phù hợp. Chưa có reviewer hoặc người adjudicator nào được chỉ định trong bộ tài liệu này.

## Hướng dẫn annotation độc lập

1. Đọc toàn bộ `title` và `content` trong sheet được giao.
2. Dùng duy nhất guideline chính thức hiện hành làm căn cứ; không xem hoặc sử dụng AI proposal, nhãn tự động, audit suggestion hay quyết định của reviewer còn lại.
3. Với mỗi bài, chọn đúng một giá trị `relevance_manual`: `Relevant`, `Borderline`, `Not relevant` hoặc `Uncertain`.
4. Chỉ khi chọn `Relevant` hoặc `Borderline`, điền đúng một topic A–L (mã kèm tên chính xác theo guideline). Với `Not relevant` hoặc `Uncertain`, để `topic_manual` trống.
5. Điền `review_reason` riêng cho từng bài: nêu bằng chứng cụ thể trong nội dung và lý do nhãn/topic phù hợp. Không để trống lý do cho một quyết định đã hoàn tất.
6. Ghi `reviewer_id` và `review_date` thật của người thực hiện sau khi review; ngày theo `YYYY-MM-DD`. Không tự điền danh tính reviewer chưa được cung cấp. Trạng thái ban đầu của mọi dòng là `PENDING`; chỉ cập nhật theo tiến độ thực tế và các định nghĩa trong guideline.
7. Nếu guideline chưa giải quyết rõ một trường hợp, nêu chính xác điểm chưa rõ trong `review_reason` và giữ nguyên đánh giá độc lập của mình; không tự suy diễn quy tắc mới, không ép đồng thuận, và không dùng `Uncertain` chỉ để né khó chọn topic.
8. Chỉ reviewer thật mới điền nhãn. Không chép hoặc chuyển đổi bất kỳ nhãn AI nào thành nhãn thủ công.

## Bất đồng và adjudication

- Chỉ sau khi cả hai lượt độc lập đã được nộp/khóa, người điều phối mới đối chiếu kết quả và phân nhóm bất đồng: relevance, topic, cả hai, hoặc bằng chứng/quy trình.
- Giữ nguyên hai quyết định ban đầu để phân tích độ đồng thuận. Không ép reviewer đạt đồng thuận và không sửa một sheet để làm cho hai kết quả giống nhau.
- Chuyển ca bất đồng hoặc ca có quy tắc chưa rõ cho adjudicator do nhóm chỉ định. Adjudicator đọc bài đầy đủ, guideline chính thức và lý do của cả hai reviewer; không dùng AI proposal làm ground truth.
- Nếu chưa thể quyết định theo guideline hiện hành, ghi rõ unresolved và xin quyết định của người phụ trách. Không tự phê duyệt đề xuất chính sách, không cập nhật guideline và không tạo kết quả đồng thuận giả.
- Chỉ dùng trạng thái `NEEDS_ADJUDICATION` theo workflow hiện hành sau khi hai quyết định độc lập đã được lưu và một ca thực sự cần adjudication. Không thay trạng thái `PENDING` ban đầu trong bộ pilot trước khi review bắt đầu.

## Điều kiện kết thúc pilot

Pilot có thể được báo cáo hoàn tất khi:

- Hai reviewer đã nộp đủ 10 quyết định độc lập, mỗi người trên đúng tập article ID.
- Hai bản độc lập được giữ nguyên; khác biệt relevance/topic và các ca chuyển adjudication được ghi nhận.
- Các ca đã được giải quyết có căn cứ theo guideline hiện hành; ca chưa giải quyết được vẫn được đánh dấu rõ là chưa có kết luận, không tính là nhãn đã xác nhận.
- Người phụ trách dự án xem xét kết quả pilot và quyết định bước tiếp theo. Việc kết thúc pilot không tự động phê duyệt đề xuất chính sách hoặc cho phép rà soát Batch 01/02 hay toàn bộ mẫu 620 bài.

## Điểm guideline cần lưu ý

Guideline hiện hành có câu ở quy trình từng bài hướng dẫn dùng `Uncertain` nếu không phân biệt được topic chính, trong khi phần định nghĩa nhãn nói không dùng `Uncertain` chỉ vì khó phân loại chủ đề. Không tự hòa giải mâu thuẫn này bằng proposal chưa được duyệt. Reviewer cần trích dẫn điểm vướng trong `review_reason`, giữ nguyên quyết định độc lập theo cách hiểu của mình và để người phụ trách/adjudicator xử lý sau khi hai lượt đã khóa.
