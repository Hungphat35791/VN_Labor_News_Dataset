# Hướng dẫn phân phối và thu nhận file Pilot 10 bài

## Mục tiêu và phạm vi

Tài liệu này hướng dẫn người điều phối giao hai bản sheet độc lập cho Pilot 10 bài, thu nhận kết quả và bảo toàn dấu vết ban đầu. Pilot dùng guideline chính thức hiện hành tại `5_process/config/labeling_guideline.md`; các đề xuất chính sách trước đó chưa được phê duyệt và không phải nhãn chuẩn.

Hai reviewer đánh giá cùng 10 bài độc lập. Tài liệu này không chỉ định reviewer, không gửi file, không gán nhãn và không cho phép sửa official guideline, canonical dataset, master sample, Batch 01 hoặc Batch 02.

## Phân phối riêng biệt

1. Người điều phối xác nhận hai file nguồn có cùng 10 `article_id`, cùng thứ tự, title/content trùng khớp, trường annotation trống và `review_status=PENDING`.
2. Tạo hai bản phân phối riêng, mỗi bản chỉ chứa sheet của người nhận tương ứng. Reviewer 1 chỉ nhận `reviewer_1_sheet.csv`; reviewer 2 chỉ nhận `reviewer_2_sheet.csv`.
3. Không gửi chung cả hai sheet cho reviewer. Dùng kênh và quyền truy cập tách biệt; không cấp quyền xem bản của người còn lại. Hai file cùng nằm trong thư mục nguồn không được xem là biện pháp phân quyền.
4. Không kèm `pilot_10_articles.csv`, selection report, AI proposals, audit, ghi chú chọn mẫu hoặc tài liệu tiết lộ ca được kỳ vọng là “khó”. Chỉ cung cấp guideline chính thức và sheet của reviewer đó.
5. Không tự điền `reviewer_id`. Xác nhận danh tính người nhận thực tế trước khi tạo bản phân phối; nếu chưa biết thì để reviewer tự ghi mã thật khi hoàn tất.

## Thực hiện và bảo mật kết quả

- Mỗi reviewer chỉ chỉnh sửa bản làm việc riêng của mình và làm theo `pilot_10_protocol.md`.
- Không trao đổi nhãn, lý do hoặc quyết định khi cả hai lượt chưa hoàn tất và được khóa.
- Không gửi, chép hoặc hiển thị nhãn của reviewer này cho reviewer kia trước thời điểm khóa hai lượt độc lập.
- Reviewer ghi `review_reason` cho từng bài, `reviewer_id` thật và ngày hoàn tất thật theo `YYYY-MM-DD`; không ghi trước hoặc suy đoán các giá trị này.
- Không tự sửa nhãn, lý do hay topic do reviewer điền. Nếu phát hiện lỗi kỹ thuật hoặc ô bị bỏ trống, yêu cầu chính reviewer xác nhận/chỉnh sửa trên bản của họ và lưu lại phiên bản nhận được; không âm thầm “sửa cho đúng”.

## Sao lưu và nhận lại

1. Trước khi phát hành, sao lưu bản nguồn bất biến của từng sheet và ghi nhận tên file, người nhận, thời điểm, phiên bản và SHA-256 trong nhật ký điều phối do nhóm quản lý. Không thay thế bản nguồn bằng bản làm việc.
2. Nhận lại từng file qua kênh riêng từ chính reviewer; ghi nhận người gửi, thời điểm nhận, tên file và SHA-256. Không mở chia sẻ chéo.
3. Lưu nguyên trạng từng file nhận được vào vùng chỉ người điều phối có quyền truy cập; tạo thêm bản sao làm việc để kiểm tra cấu trúc. Không ghi đè file nhận gốc.
4. Chỉ mở đối chiếu hai kết quả sau khi xác nhận cả hai lượt đã hoàn tất/khóa. Giữ nguyên hai bản độc lập để tính độ đồng thuận và phân tích bất đồng.
5. Nếu cần adjudication, xử lý theo protocol và guideline hiện hành; không gộp kết quả hoặc tạo nhãn đồng thuận thay cho quyết định của adjudicator.

## Ghi nhận danh tính và ngày

Reviewer phải ghi đúng mã định danh thực tế của mình trong `reviewer_id` và ngày hoàn thành từng review trong `review_date` theo `YYYY-MM-DD`. Người điều phối không tự đặt danh tính, ngày hoàn thành hoặc trạng thái review. Nếu file trả về thiếu thông tin, giữ nguyên file nhận được và liên hệ reviewer để xác nhận.

## Bàn giao

Sau khi thu nhận, người điều phối kiểm tra đủ 10 bài, schema, nhãn/topic theo guideline, lý do, reviewer_id, review_date và trạng thái. Ghi nhận bất đồng relevance/topic riêng trước adjudication; không sửa các quyết định độc lập. Chỉ báo cáo những gì đã được reviewer/adjudicator thực hiện, không suy diễn thành chính sách mới đã được phê duyệt.
