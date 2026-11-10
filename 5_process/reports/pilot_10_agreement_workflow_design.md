# Pilot 10 – Thiết kế quy trình kiểm tra đồng thuận reviewer

> **TÀI LIỆU THIẾT KẾ – CHƯA THỰC HIỆN.** Hai sheet hiện vẫn ở trạng thái `PENDING`; tài liệu này không chứa kết quả annotation, kết quả đồng thuận hoặc adjudication. Không tự chọn nhãn đúng khi reviewer bất đồng.

## 1. Mục tiêu và nguyên tắc

Thiết kế cách kiểm tra hai lượt annotation độc lập sau khi Reviewer 1 và Reviewer 2 hoàn tất Pilot 10. Căn cứ kiểm tra là `5_process/config/labeling_guideline.md` hiện hành và schema của hai sheet. Không sử dụng AI proposal/nhãn tự động làm ground truth, không sửa quyết định gốc của reviewer, và không diễn giải kết quả của mẫu pilot có chủ đích như đại diện thống kê cho dataset.

Đầu vào so sánh là hai bản đã nộp và khóa độc lập. Giữ nguyên từng file nhận được; tính hash và tạo bản sao chỉ đọc trước khi xử lý. Mọi đối chiếu, danh sách bất đồng và kết quả adjudication phải được ghi ở artifact riêng, không ghi đè hai sheet ban đầu.

## 2. Điều kiện xác nhận reviewer đã hoàn thành

Chỉ xem xét so sánh sau khi:

- Có xác nhận người thật đã nộp và khóa riêng sheet của mình; reviewer_id đã được điền đúng danh tính.
- Mỗi sheet có đúng 10 hàng, 10 `article_id` duy nhất và cùng danh sách ID với sheet còn lại.
- Mỗi hàng có `relevance_manual` thuộc đúng một trong `Relevant`, `Borderline`, `Not relevant`, `Uncertain`.
- `review_reason`, `reviewer_id` và `review_date` được điền; ngày theo `YYYY-MM-DD` và phản ánh ngày hoàn tất thật.
- Với `Relevant`/`Borderline`, `topic_manual` có đúng một mã và tên A–L hợp lệ; với `Not relevant`/`Uncertain`, `topic_manual` để trống.
- Không còn hàng `PENDING` hoặc `IN_PROGRESS`. Trạng thái khi nộp phải phù hợp định nghĩa workflow hiện hành; ghi nhận riêng nếu có trạng thái cần adjudication theo quy trình được cho phép.

Nếu thiếu reviewer_id, ngày, nhãn hoặc lý do; có giá trị sai; hoặc chưa khóa độc lập, dừng đối chiếu các hàng bị ảnh hưởng. Báo lỗi dữ liệu và yêu cầu chính reviewer xác nhận/chỉnh sửa bản của họ. Không tự điền hay sửa giúp.

## 3. Kiểm tra đầu vào trước so sánh

1. Lưu nguyên bản hai file đã nhận ở vùng truy cập hạn chế, ghi tên file, người gửi, thời điểm nhận và SHA-256; tạo bản sao chỉ đọc để phân tích.
2. Xác nhận schema và thứ tự cột đúng guideline: `article_id`, `title`, `content`, `relevance_manual`, `topic_manual`, `review_reason`, `reviewer_id`, `review_date`, `review_status`.
3. Xác nhận đủ 10 hàng, ID không trống/không trùng và hai tập ID bằng nhau. Join theo `article_id`, không dựa vào thứ tự hàng. Nếu hai tập ID không khớp, dừng so sánh đến khi người nộp làm rõ.
4. So sánh `title` và `content` của từng ID giữa hai sheet. Sai khác nguồn là lỗi dữ liệu/quy trình, không phải bất đồng annotation; giữ nguyên hai bản và yêu cầu kiểm tra lại với bản pilot đã phát hành.
5. Kiểm tra nhãn/topic theo quy tắc ở mục 2; kiểm tra `review_reason`, reviewer_id, ngày và trạng thái. Ghi rõ mọi lỗi theo article_id và reviewer, không tự chuẩn hóa giá trị.
6. Chỉ khi hai lượt đã khóa và các điều kiện cần thiết đã qua kiểm tra mới tính đồng thuận. Có thể báo các trường hợp hợp lệ còn lại và mẫu số, nhưng không gộp lỗi dữ liệu thành một nhãn.

## 4. So sánh `relevance_manual`

Đối chiếu nhãn của hai reviewer theo từng `article_id` trên bốn giá trị hợp lệ. Báo:

- số cặp hợp lệ được so sánh;
- số cặp cùng nhãn và số cặp khác nhãn;
- tỷ lệ đồng thuận thô = số cặp cùng nhãn / số cặp hợp lệ;
- bảng đếm các cặp nhãn có hướng (Reviewer 1 → Reviewer 2), gồm cả `Uncertain`.

Không tự quy `Uncertain` thành `Not relevant`, không loại `Uncertain` khỏi chỉ số chính và không gộp nhãn sau khi xem kết quả. Nếu có hàng thiếu/sai, báo riêng số hàng không hợp lệ và tính tỷ lệ chỉ trên mẫu số hợp lệ đã nêu; không trình bày tỷ lệ này như kết quả đủ 10 bài. Nếu còn ít hơn 10 cặp hợp lệ, nêu rõ lý do và không tuyên bố đã đánh giá đủ toàn pilot.

## 5. So sánh `topic_manual`

Áp dụng taxonomy A–L và điều kiện topic của guideline:

- Chỉ so sánh topic khi cả hai reviewer đều gán `Relevant` hoặc `Borderline`, và cả hai topic đều hợp lệ. Tính tỷ lệ khớp topic trên tập này; nêu rõ tử số, mẫu số và danh sách ID được tính.
- Báo thêm tỷ lệ topic khớp trong nhóm mà hai reviewer vừa đồng ý cùng một nhãn relevance `Relevant`/`Borderline`. Đây là phân tích phụ để tách bất đồng topic khỏi khác biệt mức độ liên quan; ghi rõ mẫu số riêng.
- Nếu một reviewer chọn `Relevant`/`Borderline` còn người kia chọn `Not relevant`/`Uncertain`, phân loại là bất đồng relevance; topic không so sánh được vì một phía phải để trống theo guideline.
- Nếu hai reviewer cùng chọn `Not relevant` hoặc `Uncertain`, topic phải để trống ở cả hai; không tính đây là topic agreement hay disagreement.
- Nếu nhãn relevance khác nhau nhưng cả hai vẫn là `Relevant`/`Borderline`, báo bất đồng relevance; topic vẫn có thể được đối chiếu riêng như một trường phụ, không được dùng sự khớp topic để che khuất bất đồng relevance.
- Topic thiếu/sai định dạng hoặc có topic ở hàng `Not relevant`/`Uncertain` là lỗi dữ liệu cần báo riêng; không tự sửa để tính khớp.

## 6. Phân loại và liệt kê bất đồng

Lập bảng riêng từng bài, tối thiểu gồm `article_id`, relevance của Reviewer 1/2, topic của Reviewer 1/2, loại bất đồng, lỗi/thiếu trường (nếu có), và trạng thái xử lý. Không chép nội dung nhãn của người này sang sheet người kia.

Phân loại:

1. **Bất đồng relevance:** hai `relevance_manual` khác nhau.
2. **Bất đồng topic:** cả hai nhãn thuộc `Relevant`/`Borderline` nhưng topic khác nhau hoặc topic chính chưa thống nhất. Có thể đồng thời là bất đồng relevance.
3. **Bất đồng kết hợp:** khác cả relevance lẫn topic, khi topic có thể so sánh theo điều kiện nêu ở mục 5.
4. **Lỗi/thiếu dữ liệu:** nhãn/topic không hợp lệ, lý do trống, reviewer/date/status thiếu hoặc title/content/ID không khớp. Đây không phải bất đồng nhãn và phải báo riêng.
5. **Cùng nhãn, còn câu hỏi chính sách:** hai reviewer chọn giống nhau nhưng lý do cho thấy cách hiểu guideline khác nhau hoặc quy tắc hiện hành mơ hồ. Ghi nhận để người phụ trách xem xét; không coi sự trùng nhãn là bằng chứng chính sách đã được giải quyết.

## 7. Quy trình adjudication do con người thực hiện

1. Khóa và bảo toàn hai quyết định ban đầu; hoàn tất thống kê đồng thuận trước adjudication.
2. Người điều phối lập danh sách ca bất đồng và lỗi dữ liệu, phân biệt relevance, topic, kết hợp và vấn đề guideline.
3. Chuyển ca phù hợp cho adjudicator/người có thẩm quyền do nhóm chỉ định. Adjudicator đọc đầy đủ bài, guideline đang có hiệu lực và lý do độc lập của hai reviewer; không xem AI proposal như đáp án.
4. Adjudicator ghi quyết định, bằng chứng, quy tắc guideline được áp dụng và lý do trong bản ghi adjudication riêng. Nếu guideline không đủ rõ, giữ ca unresolved và xin quyết định chính sách; không ép đồng thuận hay tự bổ sung quy tắc.
5. Không sửa hoặc xóa hai nhãn gốc. Mọi bản hợp nhất/phân tích sau adjudication phải giữ được liên kết đến cả hai quyết định độc lập và quyết định adjudicator.
6. Chỉ cập nhật `review_status` theo workflow chính thức và thẩm quyền đã xác định; không dùng trạng thái mới hoặc thay đổi trạng thái ngược với guideline.

## 8. Cách báo cáo tỷ lệ đồng thuận

Với mẫu pilot có chủ đích chỉ gồm 10 bài, báo cáo mô tả và thận trọng:

- **Relevance:** số cặp hợp lệ, số cặp đồng ý, số cặp bất đồng, tỷ lệ đồng ý thô và bảng chéo bốn nhãn.
- **Topic:** số cặp đủ điều kiện (cả hai Relevant/Borderline và topic hợp lệ), số topic trùng, tỷ lệ đồng ý; báo riêng tập cùng nhãn relevance nếu sử dụng phân tích phụ.
- **Bất đồng:** liệt kê ID và nhóm bất đồng; nêu rõ hàng nào không tính được cùng lý do.
- **Chất lượng dữ liệu:** số hàng thiếu lý do, thiếu reviewer/date, sai nhãn/topic, sai trạng thái hoặc khác nội dung nguồn.
- **Sau adjudication:** báo riêng quyết định adjudicator; không tính chúng như đồng thuận độc lập và không thay thế tỷ lệ trước adjudication.
- Ghi mẫu số, cách loại hàng không hợp lệ và mọi giả định ngay cạnh mỗi tỷ lệ. Không suy rộng ra 620 bài/toàn corpus.

Không tính Cohen’s Kappa hoặc chỉ số điều chỉnh theo cơ hội ở giai đoạn này. Chỉ xem xét sau khi người phụ trách thống nhất trước cách xử lý `Uncertain`, dữ liệu thiếu/không hợp lệ, topic không áp dụng, tập mẫu số và điều kiện tối thiểu của dữ liệu; pilot 10 bài có chủ đích cũng hạn chế mạnh diễn giải thống kê.

## 9. Trạng thái hiện tại và giới hạn

Tại thời điểm thiết kế này, cả hai reviewer sheet được quan sát có 10 ID duy nhất theo cùng thứ tự, các trường annotation còn trống và `review_status=PENDING`. Vì chưa có nhãn reviewer, chưa thể xác nhận hoàn thành, tính tỷ lệ đồng thuận, lập danh sách bất đồng hay chạy adjudication. Tài liệu này chỉ mô tả quy trình cho tương lai và không tạo kết quả thực tế.

Guideline hiện hành có điểm chưa nhất quán về `Uncertain` khi khó phân biệt topic chính so với quy định không dùng nhãn này chỉ vì topic khó. Không giải quyết mâu thuẫn bằng cách diễn giải thiết kế này thành chính sách mới; nếu tình huống xảy ra, ghi nhận và chuyển người có thẩm quyền theo quy trình con người.
