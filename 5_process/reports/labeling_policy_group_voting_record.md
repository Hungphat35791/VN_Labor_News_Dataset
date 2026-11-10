# Biên bản ghi nhận biểu quyết chính sách gán nhãn P4

> **BIỂU MẪU CHƯA CÓ PHIẾU – CHƯA PHẢI KẾT QUẢ BIỂU QUYẾT**
> Chỉ ghi nhận ý kiến thực tế của thành viên sau khi họp. Không suy diễn phiếu từ khuyến nghị trong tài liệu thảo luận. Tài liệu này không thay thế guideline chính thức và không cập nhật nhãn hay dữ liệu review.

## A. Thông tin biểu quyết

| Trường | Nội dung |
|---|---|
| Dự án | VN_Labor_News_Dataset |
| Nội dung | P4 – Group voting cho chính sách gán nhãn thủ công |
| Ngày biểu quyết |  |
| Người điều phối |  |
| Người có quyền quyết định cuối cùng |  |
| Phiên bản guideline đang áp dụng khi biểu quyết | `5_process/config/labeling_guideline.md` hiện hành |
| Thành viên/reviewer tham gia | Chưa điền |

### Danh sách thành viên

| STT | Tên/mã thành viên | Vai trò (reviewer/adjudicator/điều phối/khác) | Có quyền biểu quyết? | Xác nhận tham gia |
|---:|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

### Quy ước trạng thái trong biên bản

`PENDING`, `APPROVED`, `REJECTED`, `NEEDS_DISCUSSION` dưới đây là **trạng thái của quyết định biểu quyết trong biên bản này**, không phải giá trị để ghi vào cột `review_status` của CSV.

- `PENDING`: chưa có quyết định thực tế được ghi nhận.
- `APPROVED`: phương án được nhóm thông qua theo quy tắc biểu quyết mà nhóm đã xác nhận.
- `REJECTED`: phương án/đề xuất đang xét bị bác bỏ theo kết quả biểu quyết thực tế.
- `NEEDS_DISCUSSION`: chưa đạt thống nhất; cần trao đổi/bổ sung căn cứ trước khi quyết định.

Tất cả lựa chọn và lý do của từng thành viên được để trống. Không coi khuyến nghị A trong tài liệu thảo luận là lá phiếu hoặc kết quả.

## B. Phiếu biểu quyết cho từng vấn đề

### B1. `Borderline` và `Uncertain`

#### BLU-1 — Khi nào dùng `Uncertain`?

**Vấn đề cần quyết định:** phân biệt thiếu bằng chứng thiết yếu về relevance với việc đã rõ relevance nhưng khó chọn topic.

| Phương án | Nội dung lựa chọn | Ưu điểm | Rủi ro/tác động đến annotation |
|---|---|---|---|
| A | Chỉ dùng `Uncertain` khi thiếu/mâu thuẫn thông tin cần thiết để quyết định bài có thuộc phạm vi lao động hay không; nếu relevance rõ nhưng topic cạnh tranh thì chọn nhãn relevance có căn cứ và phân xử topic theo quy trình được duyệt. | Tách bất định relevance khỏi bất đồng topic; hạn chế dùng `Uncertain` như nhãn độ tin cậy. | Reviewer cần xác định phần thiếu nào thực sự quyết định phạm vi. |
| B | Dùng `Uncertain` khi không phân biệt được topic chính, dù relevance có thể rõ. | Có thể đơn giản với bài đa chủ đề. | Dễ tạo bất đồng relevance/topic và mâu thuẫn với quy tắc không dùng `Uncertain` chỉ vì topic khó. |
| C | Dùng `Borderline` cho mọi bài có bất kỳ liên hệ nào với lao động; `Uncertain` chỉ khi bài gần như không thể đọc. | Quy tắc nhanh, dễ nhớ. | Làm `Borderline` quá rộng; nguy cơ đưa bài chỉ nhắc nghề nghiệp/người lao động vào corpus. |

**Ví dụ Batch 01 để thảo luận:** `VNLAB-000673` (quyền riêng tư hành khách, không bàn quyền lao động); `VNLAB-008407` (sự cố sau lần giao hàng, nexus còn tranh luận). Đây là ca thảo luận, không phải nhãn chuẩn.

| Thành viên | Lựa chọn (A/B/C/ý kiến khác) | Lý do | Trạng thái quyết định |
|---|---|---|---|
|  |  |  | PENDING |

#### BLU-2 — Mối liên hệ nào đủ để gọi là `Borderline`?

**Vấn đề cần quyết định:** ngưỡng cho liên hệ lao động thực chất nhưng gián tiếp/phụ trợ.

| Phương án | Nội dung lựa chọn | Ưu điểm | Rủi ro/tác động đến annotation |
|---|---|---|---|
| A | Bài phải có nexus lao động cụ thể; nếu liên hệ có ý nghĩa nhưng phụ trợ/không phải trọng tâm thì `Borderline`. | Bám bằng chứng nội dung, không dùng từ khóa đơn lẻ. | “Có ý nghĩa” cần ví dụ đã adjudicate. |
| B | Chỉ xếp `Borderline` khi tỷ trọng nội dung lao động đạt một ngưỡng định lượng. | Có thể dễ chuẩn hóa nếu có ngưỡng phù hợp. | Độ dài không nhất thiết phản ánh trọng tâm; chưa có ngưỡng được xác nhận. |
| C | Chỉ cần bài nhắc một nhóm lao động cụ thể là đủ để xem xét `Borderline`. | Tăng độ bao phủ tin xã hội liên quan nhóm lao động. | Có thể đưa tin thiện nguyện/tội phạm không có nexus lao động vào corpus. |

**Ví dụ Batch 01 để thảo luận:** `VNLAB-010982` (quà Tết một lần cho 300 công nhân); `VNLAB-006996` (chủ quán tặng đồ ăn cho shipper/người khó khăn như việc thiện cá nhân). Không coi nhãn/topic AI hiện có là kết luận.

| Thành viên | Lựa chọn (A/B/C/ý kiến khác) | Lý do | Trạng thái quyết định |
|---|---|---|---|
|  |  |  | PENDING |

### B2. Tin hình sự có liên hệ lao động

#### CR-1 — Nexus công việc nào đưa tin hình sự vào phạm vi?

| Phương án | Nội dung lựa chọn | Ưu điểm | Rủi ro/tác động đến annotation |
|---|---|---|---|
| A | Cần bằng chứng về liên hệ với nhiệm vụ, quan hệ việc làm hoặc việc người lao động bị nhắm mục tiêu vì công việc; địa điểm/nghề nghiệp đơn lẻ không đủ. | Bao quát rủi ro nghề nghiệp có căn cứ và loại tin chỉ tình cờ ở nơi làm việc. | Cần chốt tình huống xảy ra sau khi nhiệm vụ kết thúc nhưng bắt nguồn từ công việc. |
| B | Chỉ đưa vào khi bài bàn điều kiện/phòng ngừa/trách nhiệm nơi làm việc hoặc hệ quả chính sách lao động. | Phạm vi hẹp, giảm tin hình sự thuần túy. | Có thể loại sự cố trực tiếp trong lúc làm nhiệm vụ chỉ vì bài không phân tích hệ thống an toàn. |
| C | Đưa vào nếu nạn nhân là người lao động hoặc sự việc xảy ra tại nơi làm việc. | Dễ nhận diện và bao phủ rộng. | Dựa vào nghề nghiệp/địa điểm thay vì nexus thực chất. |

**Ví dụ Batch 01 để thảo luận:** `VNLAB-008895` (tài xế bị nhắm mục tiêu khi đang chạy cuốc); `VNLAB-008407` (mâu thuẫn bắt nguồn từ giao hàng nhưng vụ việc xảy ra sau đó); `VNLAB-008880`, `VNLAB-009945`, `VNLAB-012710` (bạo lực trong hoặc gắn với tương tác giao hàng); `VNLAB-007573` (giả danh shipper để lừa khách hàng, không phải lừa người lao động tuyển dụng).

| Thành viên | Lựa chọn (A/B/C/ý kiến khác) | Lý do | Trạng thái quyết định |
|---|---|---|---|
|  |  |  | PENDING |

#### CR-2 — Chọn topic I/E/F/K cho nhóm sự kiện hình sự?

| Phương án | Nội dung lựa chọn | Ưu điểm | Rủi ro/tác động đến annotation |
|---|---|---|---|
| A | I cho lừa tuyển dụng/mua bán người/bóc lột gắn lao động; E cho rủi ro an toàn nghề nghiệp; F khi đại diện/tranh chấp quyền lao động thực chất; K chỉ cho pháp luật lao động và thực thi. | Phù hợp định nghĩa A–L và nội dung bài. | Bài có nhiều khía cạnh vẫn cần quy tắc chọn một topic chính. |
| B | Gán K cho mọi bài có khởi tố/xét xử liên quan người lao động. | Dễ nhận diện tin tòa án. | Mở rộng K sang luật hình sự không phải pháp luật lao động. |
| C | Gán I/E/F theo từ khóa (lừa đảo/bạo lực/công đoàn) mà không yêu cầu nexus. | Nhanh. | Nguy cơ gán nhãn theo từ khóa và tạo false positive. |

**Ví dụ Batch 01 để thảo luận:** `VNLAB-008709` (lừa tuyển dụng, mua bán người và bóc lột lao động); `VNLAB-000693` (công đoàn đề nghị điều tra/bảo vệ cán bộ bị đe dọa trong vụ việc bắt nguồn từ khoản vay cá nhân); `VNLAB-000673` (quyền riêng tư hành khách và quy định ngành, không phải K chỉ vì tài xế phải tuân thủ).

| Thành viên | Lựa chọn (A/B/C/ý kiến khác) | Lý do | Trạng thái quyết định |
|---|---|---|---|
|  |  |  | PENDING |

### B3. Công chức, viên chức và cán bộ nhà nước

#### CIV-1 — Phạm vi tin khu vực công

| Phương án | Nội dung lựa chọn | Ưu điểm | Rủi ro/tác động đến annotation |
|---|---|---|---|
| A | Đưa vào khi nội dung thực chất về lương, tuyển dụng, chế độ, bảo hiểm, điều kiện, quan hệ việc làm hoặc thay đổi biên chế có tác động cụ thể; có thể là một cá nhân nếu bài giải thích chính sách/chế độ rộng hơn. | Không mặc định loại khu vực công; dựa trên nội dung và tác động. | Cần phân biệt bài cá nhân có dẫn quy định chung với tin nhân sự thuần túy. |
| B | Chỉ đưa tin về chính sách áp dụng cho một nhóm; loại mọi bài tập trung một cá nhân. | Ranh giới gọn. | Có thể loại nhầm bài giải thích chế độ chung qua trường hợp cụ thể. |
| C | Đưa vào mọi tin có lương, thôi việc, bổ nhiệm hoặc cán bộ nhà nước. | Độ bao phủ rộng. | Trộn tin quản trị hành chính với nội dung lao động. |

**Ví dụ Batch 01 để thảo luận:** `VNLAB-005536` (một công chức xin thôi việc, trợ cấp cá nhân); `VNLAB-003841` (mức lương theo chức danh hành chính); `VNLAB-001450` (tình trạng nghỉ/chuyển việc, lương và điều kiện giáo viên); `VNLAB-009389` (nghỉ hưu/nghỉ việc trong đợt tinh gọn bộ máy). Chúng minh họa ranh giới, không phải nhãn/topic chuẩn.

| Thành viên | Lựa chọn (A/B/C/ý kiến khác) | Lý do | Trạng thái quyết định |
|---|---|---|---|
|  |  |  | PENDING |

#### CIV-2 — Phân biệt B/D khi tinh giản/sắp xếp nhân sự

| Phương án | Nội dung lựa chọn | Ưu điểm | Rủi ro/tác động đến annotation |
|---|---|---|---|
| A | B chỉ khi có bằng chứng mất việc/cắt giảm ngoài ý muốn; D khi có bằng chứng nghỉ tự nguyện/nghỉ hưu/chấm dứt. Nếu relevance rõ nhưng tính chất nghỉ chưa rõ, chuyển phân xử topic, không suy đoán. | Bám ranh giới hiện tại của B/D. | Cần quy trình adjudication được nhóm chấp thuận và người phụ trách. |
| B | Mọi nghỉ việc/nghỉ hưu trong đợt tinh gọn là B. | Đơn giản. | Không chứng minh được người lao động bị mất việc ngoài ý muốn. |
| C | Mọi nghỉ việc/nghỉ hưu là D. | Dễ áp dụng theo từ ngữ. | Bỏ qua tình huống cắt giảm bắt buộc. |

**Ví dụ Batch 01 để thảo luận:** `VNLAB-009389`; chỉ dùng nội dung bài để xác định tự nguyện/bắt buộc, không suy ra từ cụm “tinh gọn”.

| Thành viên | Lựa chọn (A/B/C/ý kiến khác) | Lý do | Trạng thái quyết định |
|---|---|---|---|
|  |  |  | PENDING |

### B4. Quyền lợi lao động, an sinh và từ thiện

#### BEN-1 — Phân biệt C/H/F và hoạt động ngoài phạm vi

| Phương án | Nội dung lựa chọn | Ưu điểm | Rủi ro/tác động đến annotation |
|---|---|---|---|
| A | C cho quyền lợi gắn quan hệ việc làm/chế độ; H cho chương trình/chính sách việc làm/an sinh có mục tiêu; F khi vai trò đại diện/chăm lo quyền lợi của công đoàn là nội dung thực chất; từ thiện chỉ vào khi có nexus lao động đáng kể được nhóm thống nhất. | Phân biệt theo căn cứ hưởng, đối tượng, mục tiêu và trọng tâm. | Ca chăm lo/quà tặng có thể cần adjudication để chọn C/H/F. |
| B | Mọi hỗ trợ người lao động là H; do doanh nghiệp trao thì C. | Dễ dùng. | Nhầm từ thiện với an sinh và chăm lo tùy nghi với quyền lợi C. |
| C | Chỉ chế độ có căn cứ pháp lý/hợp đồng thuộc phạm vi; mọi hỗ trợ tự nguyện là Not relevant. | Ranh giới hẹp. | Có thể loại chương trình hỗ trợ lao động thực chất thuộc H/F. |

**Ví dụ Batch 01 để thảo luận:** `VNLAB-001411` (Quỹ Bảo hiểm thất nghiệp theo nghị quyết); `VNLAB-010982` (quà Tết một lần từ Công an tỉnh); `VNLAB-004239` (quà thường niên của doanh nghiệp, không nêu rõ entitlement); `VNLAB-000076` (phiên chợ công nhân do Liên đoàn Lao động và Saigon Co.op phối hợp); `VNLAB-001095` (hoạt động công đoàn và quà cho đoàn viên khó khăn); `VNLAB-006996` (quà cá nhân của chủ quán cho shipper/người khó khăn).

| Thành viên | Lựa chọn (A/B/C/ý kiến khác) | Lý do | Trạng thái quyết định |
|---|---|---|---|
|  |  |  | PENDING |

#### BEN-2 — Hỗ trợ cộng đồng một lần tập trung vào người lao động

| Phương án | Nội dung lựa chọn | Ưu điểm | Rủi ro/tác động đến annotation |
|---|---|---|---|
| A | Có thể Borderline/H nếu người lao động là nhóm đích rõ, hỗ trợ là trọng tâm và bài nêu mục tiêu liên quan đời sống/an sinh lao động; không gọi là C nếu không có cơ sở chế độ. | Bao phủ hỗ trợ lao động có mục tiêu nhưng tách khỏi entitlement. | “Mục tiêu liên quan an sinh” cần được diễn giải bằng ví dụ. |
| B | Chỉ đưa vào khi có chương trình/chính sách với tiêu chí và tính lặp lại; quà tự nguyện một lần là Not relevant. | Ranh giới H rõ, hạn chế false positive. | Có thể loại hỗ trợ một lần nhưng được tổ chức nhắm riêng tới lao động. |
| C | Nếu công nhân là nhóm nhận và là trọng tâm thì luôn Borderline/H, bất kể nguồn/mục đích. | Độ bao phủ tối đa. | Nhóm nhận trở thành tiêu chí duy nhất; dễ bao gồm mọi tin từ thiện. |

**Ví dụ Batch 01 để thảo luận:** `VNLAB-010982`; đối chứng `VNLAB-006996`. Không coi bất kỳ đề xuất AI nào là quyết định.

| Thành viên | Lựa chọn (A/B/C/ý kiến khác) | Lý do | Trạng thái quyết định |
|---|---|---|---|
|  |  |  | PENDING |

## C. Biểu quyết về taxonomy A–L

Taxonomy hiện hành gồm 12 chủ đề. Biểu quyết này chỉ ghi nhận ý kiến; không tự thêm, xóa, đổi tên hoặc sửa định nghĩa chủ đề.

| Mã | Chủ đề hiện hành |
|---|---|
| A | Thị trường lao động Việt Nam |
| B | Thất nghiệp, mất việc, cắt giảm nhân sự |
| C | Tiền lương, bảo hiểm, quyền lợi |
| D | Hợp đồng lao động, nghỉ việc, sa thải |
| E | Điều kiện làm việc, an toàn lao động |
| F | Công đoàn, đình công, tranh chấp lao động |
| G | Nhóm lao động dễ bị ảnh hưởng |
| H | Chính sách việc làm, đào tạo nghề, an sinh xã hội |
| I | Lừa đảo tuyển dụng, bóc lột lao động |
| J | Kinh tế và yếu tố tác động đến việc làm |
| K | Pháp luật lao động và thực thi |
| L | Tâm lý người lao động, chất lượng việc làm |

**Câu hỏi:** Nhóm có đồng ý giữ nguyên 12 topic A–L và tên/định nghĩa hiện có không?

| Phương án | Ý nghĩa | Ưu điểm | Rủi ro/tác động |
|---|---|---|---|
| A | Giữ nguyên đủ 12 topic, tên và định nghĩa hiện hành. | Bảo toàn chuẩn đã thiết lập và tính nhất quán lịch sử. | Có thể cần thêm ví dụ ranh giới mà không đổi taxonomy. |
| B | Đề nghị xem xét sửa đổi taxonomy, nhưng không thực hiện trong biên bản này; phải ghi rõ đề xuất và mở quyết định/phê duyệt riêng trước mọi thay đổi. | Cho phép nêu vấn đề cấu trúc nếu có căn cứ. | Nếu không kiểm soát, có thể gây hiểu nhầm là thay đổi đã được chấp thuận; không được áp dụng khi chưa có quyết định riêng. |
| C | Chưa quyết định; tiếp tục dùng taxonomy hiện hành trong lúc chờ biểu quyết. | Tránh thay đổi vội. | Không giải quyết được vấn đề cấu trúc nếu nhóm đã thấy cần sửa. |

| Thành viên | Lựa chọn (A/B/C/ý kiến khác) | Nếu B, mô tả đề xuất (không áp dụng) | Lý do | Trạng thái quyết định |
|---|---|---|---|---|
|  |  |  |  | PENDING |

## D. Biểu quyết quy trình hai reviewer và pilot

### D1. Đánh giá độc lập và bảo mật nhãn

| Nội dung cần nhóm quyết định | Lựa chọn của thành viên (Đồng ý/Không đồng ý/Cần thảo luận) | Lý do/điều kiện |
|---|---|---|
| Hai reviewer đánh giá độc lập cùng tập bài trước khi so sánh. |  |  |
| Trong lượt độc lập, reviewer không xem AI proposals hoặc dự đoán P4.07. |  |  |
| Reviewer không xem nhãn/lý do của người còn lại cho đến khi cả hai lượt được khóa. |  |  |
| Hai bản làm việc và quyền truy cập được tách biệt; chỉ mở đối chiếu sau khi nộp/khóa cả hai lượt. |  |  |
| Thành viên xác nhận cần bổ sung điều kiện bảo mật nào khác? |  |  |

### D2. Bất đồng và adjudication

| Nội dung cần nhóm quyết định | Lựa chọn của thành viên (Đồng ý/Không đồng ý/Cần thảo luận) | Lý do/điều kiện |
|---|---|---|
| Phân loại bất đồng thành relevance, topic, combined và vấn đề bằng chứng/quy trình. |  |  |
| Reviewer có thể thảo luận sau khi đã ghi nhận quyết định độc lập; nếu chưa thống nhất thì chuyển adjudicator. |  |  |
| Adjudicator đọc bài đầy đủ, guideline đang có hiệu lực và lý do của hai reviewer; không dùng AI proposal làm ground truth. |  |  |
| Người được chỉ định làm adjudicator |  |  |
| Cách lưu quyết định cuối, bằng chứng, quy tắc và lý do |  |  |

### D3. Điều kiện kết thúc pilot 10 bài

**Điều kiện dưới đây chỉ là đề xuất để nhóm quyết định, chưa phải yêu cầu được thông qua.**

| Điều kiện kết thúc pilot | Đồng ý/Không đồng ý/Cần thảo luận | Người chịu trách nhiệm xác nhận | Ghi chú |
|---|---|---|---|
| Hai reviewer hoàn tất độc lập 10 bài theo quy tắc được phê duyệt và không xem AI proposals/nhãn của nhau trước khi khóa. |  |  |  |
| Mọi bất đồng relevance/topic trong pilot được giải quyết hoặc được ghi nhận rõ là còn mở; không để quyết định chưa rõ bị coi là nhãn đã xác nhận. |  |  |  |
| Kiểm tra schema, topic hợp lệ, lý do có căn cứ và trường reviewer/date/status theo quy ước. |  |  |  |
| Nhóm xem lại các bất đồng và quyết định có cần làm rõ guideline trước khi mở rộng review. |  |  |  |
| Người có thẩm quyền phê duyệt kết thúc pilot |  |  |  |

## E. Trạng thái `review_status` và giới hạn sử dụng

Các giá trị workflow được ghi trong `labeling_guideline.md` và `README_PROCESS.md` cho manual review:

| Giá trị đã có | Ý nghĩa được tài liệu hiện hành nêu |
|---|---|
| `PENDING` | Chưa bắt đầu review. |
| `IN_PROGRESS` | Đang review. |
| `COMPLETED` | Đã điền và kiểm tra đủ trường bắt buộc. |
| `NEEDS_ADJUDICATION` | Cần người có thẩm quyền xử lý bất đồng/ca chưa thống nhất. |

`PENDING / APPROVED / REJECTED / NEEDS_DISCUSSION` trong phần A là trạng thái **biểu quyết**, không phải `review_status`. Một số artifact tự động/legacy có các giá trị như `AUTO_CLASSIFIED` hoặc `REVIEW_REQUIRED`; đó là ngữ cảnh khác, không thay thế workflow của manual review CSV.

Mặc dù `NEEDS_ADJUDICATION` đã được liệt kê trong tài liệu hiện hành, **biên bản này không yêu cầu và không cho phép tự ý áp dụng trạng thái đó vào Batch 01/02**. Chỉ xem xét sử dụng cho tác vụ tương lai sau khi nhóm đã xác nhận quy trình adjudication, người có thẩm quyền và cách lưu quyết định. Hiện tại không thay đổi bất kỳ `review_status` nào.

### Ghi nhận giá trị đang có trong Batch

| File | Giá trị quan sát trước biểu quyết |
|---|---|
| Batch 01 | `PENDING` |
| Batch 02 | `PENDING` |

Các giá trị trên chỉ ghi trạng thái quan sát, không phải kết quả biểu quyết.

## F. Tổng kết quyết định

Điền sau khi có cuộc họp/phiếu thực tế; hiện để trống.

| Phân loại | Nội dung thực tế đã được ghi nhận | Người/ngày xác nhận |
|---|---|---|
| Đã được nhóm phê duyệt | Chưa có quyết định được ghi nhận. |  |
| Chưa được phê duyệt | Toàn bộ quy tắc mới/chỉnh sửa guideline đang chờ biểu quyết và phê duyệt. |  |
| Còn tranh luận | BLU-1, BLU-2, CR-1, CR-2, CIV-1, CIV-2, BEN-1, BEN-2, TOP-1 và quy trình hai reviewer/pilot chưa có phiếu. |  |
| Cần bổ sung ví dụ hoặc tiêu chí | Các ca hỗ trợ một lần, sự cố sau nhiệm vụ, công đoàn trong vụ việc cá nhân, topic cạnh tranh và tinh giản nhưng chưa rõ tự nguyện/bắt buộc cần hiệu chuẩn theo kết quả họp. |  |

## G. Nhật ký thay đổi sau biểu quyết

Không ghi sửa đổi nào cho đến khi có kết quả thật và người có thẩm quyền xác nhận.

| Ngày | Mã vấn đề | Quyết định đã được xác nhận | Người phê duyệt | Hành động được phép tiếp theo |
|---|---|---|---|---|
|  |  |  |  |  |

## H. Nguồn tham chiếu

- `5_process/reports/labeling_policy_group_voting.md`
- `5_process/reports/labeling_policy_clarification_proposal.md`
- `5_process/reports/labeling_policy_review_assessment.md`
- `5_process/config/labeling_guideline.md`
- `5_process/README_PROCESS.md`
- `5_process/src/create_relevance_review_batch.py`
- `5_process/data/interim/relevance_review_batch_01.csv` và `relevance_review_batch_02.csv` (chỉ kiểm tra trạng thái; không sửa)
