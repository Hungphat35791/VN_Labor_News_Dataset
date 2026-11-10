# Checklist nghiệm thu Pilot Annotation 10 bài

> **Trạng thái hiện tại:** Chưa bắt đầu review. Toàn bộ checkbox để trống; chỉ đánh dấu sau khi có bằng chứng thực tế. Checklist này không phải nhãn hoặc kết quả review.

## A. Bộ dữ liệu và bảo toàn nguồn

- [ ] Pilot có đủ đúng 10 bài và 10 `article_id` duy nhất.
- [ ] Reviewer 1 và reviewer 2 nhận đúng cùng danh sách, cùng thứ tự `article_id`.
- [ ] Title/content trong hai sheet khớp nhau và khớp dữ liệu nguồn.
- [ ] Hai file reviewer được phân phối riêng; không lộ sheet hoặc kết quả của reviewer kia.
- [ ] Không reviewer nào xem AI proposals/nhãn tự động trước khi khóa quyết định độc lập.
- [ ] Đã lưu bản sao bất biến và hash của hai sheet đầu vào trước khi phân phối.
- [ ] Canonical dataset, master sample, Batch 01, Batch 02 và official guideline không bị sửa trong pilot.

## B. Hoàn tất độc lập

- [ ] Reviewer 1 hoàn tất và khóa toàn bộ 10 bài trên sheet riêng.
- [ ] Reviewer 2 hoàn tất và khóa toàn bộ 10 bài trên sheet riêng.
- [ ] Hai lượt được giữ độc lập và chỉ mở đối chiếu sau khi cả hai đã khóa.
- [ ] Mỗi bài có đúng một nhãn hợp lệ: `Relevant`, `Borderline`, `Not relevant` hoặc `Uncertain`.
- [ ] Với `Relevant`/`Borderline`, mỗi bài có đúng một topic A–L hợp lệ theo guideline.
- [ ] Với `Not relevant`/`Uncertain`, `topic_manual` để trống.
- [ ] Mỗi bài có `review_reason` cụ thể, dựa trên bằng chứng trong nội dung.
- [ ] `reviewer_id` của từng người phản ánh đúng danh tính reviewer thực tế.
- [ ] `review_date` của từng bài/người phản ánh ngày hoàn thành thực tế theo `YYYY-MM-DD`.
- [ ] `review_status` phản ánh đúng tiến độ theo guideline hiện hành.

## C. Đối chiếu và bất đồng

- [ ] Đã kiểm tra lại schema, số dòng, ID duy nhất và tính đầy đủ của cả hai file đã nhận.
- [ ] Đã tính độ đồng thuận trên các quyết định độc lập trước adjudication.
- [ ] Đã báo cáo riêng mức đồng thuận relevance và mức đồng thuận topic; nêu rõ mẫu số và cách xử lý topic trống.
- [ ] Đã liệt kê các trường hợp bất đồng relevance, topic, hoặc cả hai.
- [ ] Đã ghi nhận những trường hợp còn thiếu bằng chứng hoặc guideline chưa đủ rõ.
- [ ] Adjudication đã được thực hiện cho các trường hợp cần thiết bởi người có thẩm quyền được chỉ định.
- [ ] Quyết định adjudication và lý do được lưu riêng; hai nhãn độc lập ban đầu vẫn được bảo toàn.
- [ ] Các vấn đề guideline cần làm rõ đã được tổng hợp mà không tự coi đề xuất là chính sách đã duyệt.

## D. Hoàn tất và bàn giao

- [ ] Đã sao lưu file nhận từ từng reviewer và ghi nhận tên file, người gửi, thời điểm nhận, phiên bản/hash.
- [ ] Đã xác nhận không tự sửa hoặc ghi đè nhãn/lý do của reviewer.
- [ ] Đã báo cáo kết quả, bất đồng chưa giải quyết và giới hạn của pilot cho người phụ trách.
- [ ] Người phụ trách đã xác nhận bước tiếp theo; không tự mở rộng review ngoài phạm vi được giao.

## Ghi chú về mức độ đồng thuận

Tính và báo cáo độ đồng thuận từ hai bộ quyết định độc lập trước adjudication. Tối thiểu báo cáo số lượng và tỷ lệ đồng ý thô riêng cho relevance và topic; topic chỉ được so sánh theo một quy tắc mẫu số được nêu rõ, chẳng hạn các bài cả hai reviewer đều gán `Relevant`/`Borderline`. Có thể bổ sung Cohen’s kappa nếu phù hợp với dữ liệu, nhưng với pilot nhỏ, có chủ đích gồm 10 bài, cần ghi rõ tính thăm dò và không diễn giải như ước lượng đại diện cho toàn dataset. Không tính quyết định adjudication như sự đồng thuận độc lập.

## Biên bản nghiệm thu

| Trường | Ghi nhận sau khi có kết quả |
|---|---|
| Ngày nghiệm thu |  |
| Người nghiệm thu |  |
| Reviewer 1 (mã thực tế) |  |
| Reviewer 2 (mã thực tế) |  |
| Adjudicator (nếu có) |  |
| Số bài hoàn tất độc lập |  |
| Số bất đồng relevance/topic |  |
| Kết quả adjudication |  |
| Vấn đề guideline còn mở |  |
