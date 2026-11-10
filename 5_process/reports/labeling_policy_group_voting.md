# Tài liệu thảo luận và biểu quyết: Chính sách gán nhãn thủ công P4

> **TÀI LIỆU BIỂU QUYẾT – CHƯA PHẢI GUIDELINE ĐƯỢC PHÊ DUYỆT**
> Dùng để nhóm thống nhất chính sách trước khi review chính thức. Không ghi nhãn, không sửa CSV, không thay thế `5_process/config/labeling_guideline.md`. Mọi khuyến nghị dưới đây chỉ là đề xuất của nhóm dự án.

## 1. Mục tiêu và cách sử dụng

Tài liệu này chuyển bốn điểm còn tranh luận trong `labeling_policy_clarification_proposal.md` và `labeling_policy_review_assessment.md` thành câu hỏi có phương án biểu quyết:

1. Ranh giới `Borderline` / `Uncertain`.
2. Tin hình sự có liên hệ với lao động.
3. Phạm vi công chức, viên chức và cán bộ nhà nước.
4. Quyền lợi lao động, an sinh và hoạt động từ thiện.

Có thêm một mục biểu quyết riêng về cách chọn **một topic A–L** khi nhiều chủ đề cùng xuất hiện, và một quy trình xử lý bất đồng giữa hai reviewer. Các article ID được dẫn là ca thảo luận từ Batch 01; mọi nhãn/topic nêu trong tài liệu đều là nội dung cần biểu quyết, không phải nhãn đã xác nhận.

**Cách bỏ phiếu:** với mỗi câu hỏi, chọn một phương án; nếu chưa đồng thuận, ghi “chưa thống nhất” cùng lý do. Có thể ghi người bỏ phiếu, ngày và ý kiến ngắn trong biên bản họp của nhóm. Chỉ cập nhật guideline sau khi người phụ trách có thẩm quyền phê duyệt kết quả.

## 2. Câu hỏi biểu quyết theo bốn vấn đề

### 2.1. Ranh giới `Borderline` và `Uncertain`

#### Câu hỏi BLU-1 — Khi nào dùng `Uncertain`?

**Vấn đề cần quyết định:** phân biệt việc thiếu bằng chứng quyết định relevance với việc đã biết relevance nhưng chủ đề/topic khó chọn.

| Phương án | Quy tắc đề xuất | Ưu điểm | Rủi ro |
|---|---|---|---|
| A | Chỉ dùng `Uncertain` khi nội dung hiện có thiếu hoặc mâu thuẫn **thông tin thiết yếu để quyết định bài có thuộc phạm vi lao động hay không**. Nếu relevance rõ nhưng topic cạnh tranh, chọn nhãn relevance có căn cứ, chọn topic chính theo quy tắc chung hoặc chuyển phân xử topic. | Giữ `Uncertain` nhất quán như nhãn về độ đủ bằng chứng; không làm lẫn bất đồng topic với bất định relevance. | Có thể ít dùng `Uncertain` hơn; reviewer phải phân biệt thiếu sót quan trọng với lỗi/thiếu không ảnh hưởng kết luận. |
| B | Dùng `Uncertain` cả khi chưa phân biệt được topic chính, dù relevance có thể rõ. | Dễ dùng khi reviewer gặp bài nhiều chủ đề. | Trái với mục 3 của guideline hiện tại; gây nhầm `Uncertain` là độ tự tin/topic và làm lệch thống kê relevance. |
| C | Ưu tiên `Borderline` cho mọi bài có bất kỳ liên hệ nào với lao động; chỉ dùng `Uncertain` khi bài gần như không đọc được. | Quy tắc ngắn, dễ áp dụng nhanh. | Làm Borderline quá rộng; biến nhắc nghề nghiệp/tác động suy đoán thành liên hệ đủ điều kiện. |

**Khuyến nghị của nhóm dự án (đề xuất):** Chọn A. Không tự chuyển `Uncertain` thành `Not relevant`; nếu nội dung thiếu, ghi chính xác thông tin cần xác minh và để topic trống.

**Ví dụ Batch 01:** `VNLAB-000673` nêu rõ nội dung về quyền riêng tư hành khách chứ không phải quyền lao động, nên có thể dùng để minh họa `Not relevant` nếu nhóm chấp thuận tiêu chí. `VNLAB-008407` cho thấy đủ dữ kiện về một chuyến giao hàng và sự cố sau đó, nhưng độ liên quan có thể còn tranh luận; đây là bất đồng về ngưỡng relevance/nexus, không phải tự động `Uncertain` vì topic khó. Giả định thiếu đoạn nội dung khiến không rõ người bị nạn có đang làm việc hay không là ví dụ phù hợp hơn cho `Uncertain`; không gán article ID giả định.

#### Câu hỏi BLU-2 — Mối liên hệ nào đủ để gọi là `Borderline`?

**Vấn đề cần quyết định:** xác định “liên hệ đáng kể nhưng gián tiếp/phụ trợ” sao cho không nhầm bài về lao động thực chất với bài chỉ nhắc người lao động.

| Phương án | Quy tắc đề xuất | Ưu điểm | Rủi ro |
|---|---|---|---|
| A | Bắt buộc nêu được một nexus lao động cụ thể từ nội dung (đối tượng, công việc, quyền lợi, quan hệ hoặc tác động việc làm); nội dung lao động có ý nghĩa nhưng không phải trọng tâm chính thì Borderline. | Có căn cứ văn bản; hạn chế suy luận từ từ khóa và chức danh. | “Có ý nghĩa” vẫn cần ví dụ adjudicate; các bài đa chủ đề có thể bất đồng. |
| B | Chỉ xếp Borderline nếu bài có lượng nội dung lao động đáng kể hoặc đo được theo tỷ lệ. | Có vẻ nhất quán và có thể định lượng. | Không có ngưỡng tỷ lệ hợp lý; độ dài một đoạn không phản ánh mức quan trọng; dễ loại bài ngắn nhưng nội dung lao động cốt lõi. |
| C | Xếp Borderline khi bài nhắc cụ thể một nhóm lao động, dù không mô tả quan hệ/tác động đến việc làm. | Bao phủ rộng hơn các tin xã hội liên quan nhóm lao động. | Có thể kéo tin thiện nguyện, đời sống hoặc tội phạm ngẫu nhiên vào dataset chỉ vì nhóm nhận/nạn nhân là lao động. |

**Khuyến nghị của nhóm dự án (đề xuất):** Chọn A và sử dụng các ca hiệu chuẩn được nhóm quyết định làm ví dụ; không đặt ngưỡng phần trăm nội dung.

**Ví dụ Batch 01:** `VNLAB-010982` tập trung vào 300 phần quà Tết cho công nhân, nhưng nội dung không nói đó là quyền lợi theo chế độ; đây là ca để quyết định liên hệ hỗ trợ một lần có đủ đáng kể hay không. `VNLAB-006996` kể việc thiện cá nhân tặng đồ ăn cho shipper/người khó khăn và không bàn công việc hay chế độ; đây là đối chứng không nên đưa vào chỉ vì người nhận là shipper.

### 2.2. Tin hình sự có liên hệ lao động

#### Câu hỏi CR-1 — Nexus công việc nào đưa tin hình sự vào phạm vi?

**Vấn đề cần quyết định:** phân biệt sự cố gắn với nhiệm vụ/quan hệ lao động với vụ án chỉ tình cờ xảy ra ở nơi làm việc hoặc nạn nhân tình cờ có nghề nghiệp đó.

| Phương án | Quy tắc đề xuất | Ưu điểm | Rủi ro |
|---|---|---|---|
| A | Cần bằng chứng về mối liên hệ thực chất: sự việc xảy ra khi đang làm nhiệm vụ, phát sinh từ tương tác/nhiệm vụ/quan hệ việc làm, hoặc người lao động bị nhắm mục tiêu vì công việc. Địa điểm/nghề nghiệp đơn lẻ không đủ. | Bao quát rủi ro nghề nghiệp và ngăn đưa mọi tin an ninh nơi làm việc vào phạm vi. | Khái niệm “thực chất” và sự cố sau ca vẫn cần ví dụ thống nhất. |
| B | Chỉ đưa vào nếu bài bàn rõ điều kiện làm việc, phòng ngừa, trách nhiệm nơi làm việc hoặc hệ quả đối với chính sách lao động. | Ranh giới hẹp, giảm tin hình sự thuần túy. | Có thể loại các vụ việc trực tiếp nhắm vào người đang làm nhiệm vụ chỉ vì bài báo tường thuật sự kiện mà không phân tích hệ thống an toàn. |
| C | Đưa vào nếu nạn nhân là người lao động hoặc sự việc xảy ra tại nơi làm việc. | Dễ nhận diện và tăng độ bao phủ. | Dựa vào nghề nghiệp/địa điểm thay vì nexus; dễ thu nhận án hình sự không liên quan thị trường lao động. |

**Khuyến nghị của nhóm dự án (đề xuất):** Chọn A. Đánh giá relevance riêng với topic: vụ việc đơn lẻ có nexus trực tiếp nhưng bài không bàn rộng về điều kiện/an toàn có thể là Borderline/E nếu nhóm chấp thuận ngưỡng; không bắt buộc phải có đề xuất biện pháp phòng ngừa để xem xét.

**Ví dụ Batch 01:** `VNLAB-008895`: nội dung mô tả tài xế đang thực hiện chuyến xe và bị nhắm mục tiêu để cướp tài sản; ca phù hợp để biểu quyết mức Borderline/E hay cách xử lý hẹp hơn. `VNLAB-008407`: xung đột bắt nguồn từ lần giao hàng/phản ánh với công ty, nhưng người giao hàng quay lại nhà khách sau đó; dùng để chốt sự cố sau nhiệm vụ. `VNLAB-008880` và `VNLAB-009945`: bạo lực phát sinh trong tương tác giao hàng với khách, thích hợp so sánh với trường hợp chỉ tình cờ có nạn nhân làm nghề shipper. `VNLAB-007573`: đối tượng giả danh shipper lừa khách hàng, không phải lừa người lao động tuyển dụng; đối chứng để tránh gán I do từ khóa.

#### Câu hỏi CR-2 — Chọn topic cho các nhóm sự kiện hình sự như thế nào?

**Vấn đề cần quyết định:** giữ ranh giới I/E/F/K và tránh nhầm tội phạm thông thường với vi phạm pháp luật lao động.

| Phương án | Quy tắc đề xuất | Ưu điểm | Rủi ro |
|---|---|---|---|
| A | I cho lừa tuyển dụng/mua bán người/bóc lột gắn lao động; E cho rủi ro an toàn nghề nghiệp; F khi đại diện/tranh chấp quyền lao động là nội dung thực chất; K chỉ cho luật lao động và thực thi. | Bám định nghĩa A–L; tránh ánh xạ từ từ “khởi tố”, “công đoàn”, “lừa đảo”. | Một bài có nhiều khía cạnh có thể cần quy tắc chọn topic chính. |
| B | Gán K cho mọi bài có điều tra, khởi tố hoặc tòa án liên quan người lao động. | Dễ dùng với tin pháp lý. | K bị mở rộng thành toàn bộ hình sự; sai khác định nghĩa “pháp luật lao động và thực thi”. |
| C | Gán E/F/I theo từ khóa (tai nạn/bạo lực, công đoàn, lừa đảo) mà không yêu cầu nexus lao động. | Tốc độ cao, ít phải adjudicate. | Tạo false positive và đi ngược nguyên tắc đánh giá toàn bài. |

**Khuyến nghị của nhóm dự án (đề xuất):** Chọn A. Topic cần căn cứ vào vấn đề lao động được bài bàn, không phải cơ quan xử lý hoặc hình thức tố tụng.

**Ví dụ Batch 01:** `VNLAB-008709` có tuyển dụng gian dối, thu hộ chiếu và ép làm việc, phù hợp I. `VNLAB-008895` là ca E cần biểu quyết. `VNLAB-000693` có công đoàn đề nghị điều tra/bảo vệ cán bộ bị đe dọa do khoản vay cá nhân của công nhân; cần thống nhất khi nào hoạt động đó đủ liên hệ quan hệ lao động để chọn F. `VNLAB-000673` nói về quyền riêng tư khách hàng và quy định ngành, không phải K chỉ vì tài xế phải tuân thủ.

### 2.3. Công chức, viên chức và cán bộ nhà nước

#### Câu hỏi CIV-1 — Phạm vi nào áp dụng cho tin khu vực công?

**Vấn đề cần quyết định:** chọn tiêu chí đưa tin về chính sách/việc làm khu vực công vào corpus, đồng thời phân biệt với tin nhân sự hành chính cá nhân.

| Phương án | Quy tắc đề xuất | Ưu điểm | Rủi ro |
|---|---|---|---|
| A | Đưa vào khi nội dung thực chất về tiền lương, tuyển dụng, chế độ, bảo hiểm, điều kiện, quan hệ việc làm hoặc thay đổi biên chế có tác động cụ thể; có thể là chính sách nhóm hoặc một cá nhân nếu bài giải thích quy tắc/chế độ rộng hơn. | Không loại trừ khu vực công; dựa vào nội dung và tác động thay vì chức danh hoặc số người. | Ranh giới “thực chất” cần áp dụng cẩn thận cho bài một nhân vật. |
| B | Chỉ đưa tin về chính sách áp dụng cho một nhóm; loại mọi bài tập trung một cá nhân dù có nói chế độ. | Dễ phân biệt tin chính sách với tin nhân sự. | Quá hẹp; bài giải thích chế độ chung qua một trường hợp cụ thể có thể bị loại nhầm. |
| C | Đưa vào mọi tin có lương, thôi việc, bổ nhiệm hoặc cán bộ nhà nước. | Độ bao phủ rộng và ít ca bỏ sót. | Biến hoạt động quản trị/nhân sự đơn lẻ thành tin lao động dù thiếu nội dung lao động thực chất. |

**Khuyến nghị của nhóm dự án (đề xuất):** Chọn A; quyết định theo chủ đề, chính sách và tác động, không theo việc bài có bao nhiêu nhân vật.

**Ví dụ Batch 01:** `VNLAB-005536` mô tả một Phó giám đốc sở xin thôi việc và trợ cấp cá nhân; `VNLAB-003841` tính lương theo chức danh Chủ tịch UBND phường/quận nhưng không phân tích chính sách nhóm. Hai bài là đối chứng cho tin nhân sự/lương cá nhân. `VNLAB-001450` bàn tình trạng giáo viên nghỉ/chuyển việc, lương và điều kiện công tác của đội ngũ; phù hợp relevance khu vực công, nhưng topic D/C/E cần quyết định riêng. `VNLAB-009389` nêu 473 cán bộ/công chức/viên chức/người lao động nghỉ hưu sớm/nghỉ việc trong đợt tinh gọn bộ máy; là ca về tác động nhóm, cần đọc bằng chứng trước khi chọn B hay D.

#### Câu hỏi CIV-2 — Xếp topic khi tinh giản/sắp xếp nhân sự nhưng không rõ tính tự nguyện?

**Vấn đề cần quyết định:** tránh tự suy luận “nghỉ việc” là mất việc hoặc tự nguyện nghỉ.

| Phương án | Quy tắc đề xuất | Ưu điểm | Rủi ro |
|---|---|---|---|
| A | Chỉ gán B khi bài nêu mất việc/cắt giảm ngoài ý muốn; gán D khi có bằng chứng nghỉ tự nguyện/nghỉ hưu/chấm dứt. Nếu relevance rõ nhưng ý chí chưa rõ, giữ ca ở adjudication để quyết định topic, không suy đoán. | Bám ranh giới B/D hiện hành; ngăn suy diễn. | Cần bước adjudication rõ khi relevance đã xác định nhưng topic chưa chốt. |
| B | Mọi nghỉ việc/nghỉ hưu trong đợt tinh gọn đều là B. | Quy tắc đơn giản, bám bối cảnh tổ chức. | Coi nghỉ tự nguyện/nghỉ hưu là mất việc; thiếu bằng chứng về ý chí. |
| C | Mọi nghỉ việc/nghỉ hưu là D, bất kể có cắt giảm hay bắt buộc. | Dễ áp dụng theo từ “nghỉ việc”. | Bỏ qua mất việc/cắt giảm ngoài ý muốn; trái phân biệt B/D. |

**Khuyến nghị của nhóm dự án (đề xuất):** Chọn A. Nếu không rõ tự nguyện hay bắt buộc, không đoán B/D; dùng workflow adjudication hiện hữu để làm rõ topic.

**Ví dụ Batch 01:** `VNLAB-009389` nêu số người nghỉ hưu sớm/nghỉ việc trong đợt sắp xếp, nhưng cần dựa vào nội dung về từng diện và tính tự nguyện/bắt buộc; không chọn B chỉ vì có “tinh gọn bộ máy”.

### 2.4. Quyền lợi lao động, an sinh và từ thiện

#### Câu hỏi BEN-1 — Khi nào hỗ trợ là quyền lợi C, chính sách H, hoạt động F hay ngoài phạm vi?

**Vấn đề cần quyết định:** phân biệt chế độ/benefit, hỗ trợ có mục tiêu và thiện nguyện tùy nghi.

| Phương án | Quy tắc đề xuất | Ưu điểm | Rủi ro |
|---|---|---|---|
| A | C khi quyền lợi phát sinh từ quan hệ việc làm, hợp đồng, chế độ hoặc chương trình nhân viên; H khi có chương trình/chính sách việc làm/an sinh với nhóm đích/mục tiêu rõ; F khi vai trò đại diện/chăm lo quyền lợi của công đoàn là nội dung thực chất; từ thiện một lần ngoài các quan hệ đó chỉ đưa vào nếu có liên hệ lao động đáng kể đã được nhóm chấp thuận. | Phân biệt theo căn cứ hưởng và nội dung, không theo từ “quà” hay “công nhân”. | Một số hoạt động chăm lo tập trung có thể không khớp rạch ròi; cần ví dụ adjudicate. |
| B | Mọi quà/hỗ trợ cho người lao động được gán H; nếu do công ty trao thì C. | Dễ nhớ, bao phủ rộng. | Đồng nhất từ thiện với an sinh và hoạt động chăm lo tùy nghi với quyền lợi C. |
| C | Chỉ chế độ có căn cứ pháp lý/hợp đồng mới vào phạm vi; mọi hỗ trợ tự nguyện đều Not relevant. | Ranh giới hẹp, nhất quán với entitlement. | Có thể loại các chương trình hỗ trợ người lao động thực chất, dù là nội dung chính và thuộc H/F. |

**Khuyến nghị của nhóm dự án (đề xuất):** Chọn A. Không mặc định quà của doanh nghiệp là C; không mặc định một khoản tặng cho công nhân là H. Xét mục tiêu, nhóm thụ hưởng, căn cứ/điều kiện, vai trò công đoàn và trọng tâm bài.

**Ví dụ Batch 01:** `VNLAB-001411` mô tả chi hỗ trợ từ Quỹ Bảo hiểm thất nghiệp theo nghị quyết cho hàng trăm nghìn người lao động, có căn cứ chế độ và phù hợp để thảo luận C. `VNLAB-010982` là quà Tết một lần do Công an tỉnh tặng 300 công nhân; Borderline/H còn cần biểu quyết. `VNLAB-004239` nêu quà Trung thu thường niên của doanh nghiệp cho hơn 17.000 công nhân, nhưng nội dung không khẳng định đó là entitlement; không tự động gán C. `VNLAB-000076` là phiên chợ công nhân do Liên đoàn Lao động và Saigon Co.op phối hợp nhằm hỗ trợ người lao động khó khăn trong thời gian 15 ngày, phù hợp để thảo luận H hay F theo trọng tâm chương trình. `VNLAB-001095` nêu công đoàn tổ chức sinh hoạt gia đình và trao 43 phần quà cho đoàn viên khó khăn; phân biệt F với hỗ trợ H/C. `VNLAB-006996` là hành động tặng suất ăn miễn phí của chủ quán cho shipper/người khó khăn, đối chứng với thiện nguyện cá nhân ngoài quyền lợi lao động.

#### Câu hỏi BEN-2 — Hỗ trợ cộng đồng một lần tập trung vào người lao động có thuộc phạm vi không?

**Vấn đề cần quyết định:** xử lý khoản quyên góp/quà tặng tự nguyện không phải chế độ nhưng bài tập trung vào người lao động.

| Phương án | Quy tắc đề xuất | Ưu điểm | Rủi ro |
|---|---|---|---|
| A | Có thể Borderline/H khi người lao động là nhóm đích rõ ràng, hỗ trợ là trọng tâm và bài nêu mục tiêu hỗ trợ liên quan đời sống/an sinh lao động; không gọi là quyền lợi C nếu không có cơ sở chế độ. | Không loại bỏ hoạt động hỗ trợ lao động thực chất; phân biệt với quà tặng ngẫu nhiên. | Từ “mục tiêu liên quan an sinh” vẫn có thể diễn giải rộng; cần quyết định ngưỡng cho quà Tết. |
| B | Chỉ đưa vào nếu có chính sách/chương trình với tiêu chí và tính lặp lại; quà từ thiện một lần luôn Not relevant. | Ranh giới H rõ, hạn chế false positive. | Loại trường hợp một lần có mục tiêu rõ, được bài đưa làm trọng tâm hỗ trợ người lao động. |
| C | Nếu công nhân là nhóm nhận và là trọng tâm thì luôn Borderline/H, bất kể mục đích, nguồn hay quan hệ chi trả. | Bao phủ tối đa. | Người nhận trở thành tiêu chí duy nhất; dễ nhập toàn bộ tin từ thiện vào corpus. |

**Khuyến nghị của nhóm dự án (đề xuất):** Chọn A, kèm yêu cầu bằng chứng trong bài về nhóm đích và mục tiêu hỗ trợ lao động; coi `VNLAB-010982` là ca thử nghiệm để nhóm quyết định quy tắc, không phải đáp án mặc định.

## 3. Biểu quyết riêng: chọn một topic A–L khi nhiều chủ đề cùng xuất hiện

### Câu hỏi TOP-1 — Tiêu chí ưu tiên cho topic chính

**Vấn đề cần quyết định:** khi bài có đủ căn cứ cho nhiều topic, chọn một topic theo tiêu chí nào để tất cả reviewer nhất quán?

| Phương án | Quy tắc đề xuất | Ưu điểm | Rủi ro |
|---|---|---|---|
| A | Chọn topic phản ánh vấn đề lao động trung tâm mà bài giải thích/đưa tin; xét toàn bài (không chỉ title), quan hệ nhân quả, mục tiêu chính sách và bằng chứng. Dùng title/lede như tín hiệu, không làm quy tắc quyết định. Ghi topic cạnh tranh trong `review_reason`. | Bám nội dung và phù hợp nguyên tắc chọn nhóm phản ánh trọng tâm chính; hạn chế quyết định theo từ khóa. | “Vấn đề trung tâm” vẫn cần adjudication với bài đa chủ đề. |
| B | Chọn topic xuất hiện nhiều nhất theo số từ/đoạn. | Dễ định lượng và tái lập. | Độ dài không đồng nghĩa trọng tâm; bài dài có thể nhắc nhiều nội dung nền. |
| C | Luôn ưu tiên topic cụ thể hơn (ví dụ C/D/E) hơn topic rộng (A/H/J). | Tạo thứ tự ưu tiên đơn giản. | Không có thứ bậc chính thức giữa A–L; ép một ưu tiên có thể sai trọng tâm bài. |
| D | Cho phép nhiều topic trong `topic_manual`. | Giữ được nhiều chiều nội dung. | Vi phạm yêu cầu hiện tại: một primary topic A–L; làm thay đổi schema/định nghĩa gán nhãn. |

**Khuyến nghị của nhóm dự án (đề xuất):** Chọn A. Giữ đúng một topic và schema hiện tại; không tự tạo thứ bậc topic. Khi bất đồng không giải quyết được bằng tiêu chí đã thống nhất, chuyển adjudicator quyết định.

**Ví dụ Batch 01 để bỏ phiếu hiệu chuẩn:**

- `VNLAB-001450`: nghỉ/chuyển việc (D), lương (C), áp lực và điều kiện công tác (E) cùng hiện diện; quyết định relevance có thể rõ nhưng topic chính cần căn cứ trọng tâm đã thống nhất.
- `VNLAB-004574`: đề xuất đồng thời tăng lương tối thiểu và giảm giờ làm; C cạnh tranh với E. Chọn theo vấn đề bài nhấn mạnh, không theo một từ khóa.
- `VNLAB-001095`: hoạt động công đoàn và phần quà/hỗ trợ đoàn viên; F cạnh tranh với C/H. Việc công đoàn tổ chức không tự nó quyết định F.
- `VNLAB-009591`: đề xuất chuyển đổi phương tiện cho shipper/tài xế, dừng ký hợp đồng mới với nhóm xe xăng và có hỗ trợ tín dụng; H có thể cạnh tranh với A/J tùy trọng tâm chính sách và tác động việc làm.
- `VNLAB-009389`: nghỉ hưu/nghỉ việc trong đợt tinh gọn bộ máy; cần phân biệt B/D theo bằng chứng, không theo từ “tinh gọn” đơn lẻ.

**Phiếu TOP-1:** chọn A / B / C / D / Chưa thống nhất. Ý kiến/lý do: ____________________.

## 4. Quy trình hai reviewer độc lập và giải quyết bất đồng

### 4.1. Bảo đảm độc lập và không lộ AI/nhãn của người kia

1. Chỉ định reviewer 1 và reviewer 2; cả hai nhận cùng một tập article ID và cùng phiên bản guideline đã được nhóm chấp thuận.
2. Tạo hai bản làm việc riêng, mỗi bản chỉ có trường nguồn (article_id, title, content) và các trường annotation trống. Không đưa file AI proposals, `relevance_results.csv`, dự đoán P4.07, topic dự đoán hoặc nhãn của reviewer kia vào bản làm việc.
3. Giới hạn quyền truy cập: mỗi reviewer chỉ được xem bản của mình; giữ proposals và kết quả của reviewer kia ở vị trí không chia sẻ cho đến khi cả hai lượt được nộp/khóa. Không thảo luận nhãn bài cụ thể trước thời điểm khóa.
4. Mỗi reviewer đọc toàn bộ title/content, tự gán một relevance, một topic nếu được phép, review_reason có bằng chứng, reviewer_id thật và ngày review; không xem gợi ý AI để quyết định.
5. Khóa/ghi nhận phiên bản hai bản làm việc trước khi so sánh. Chỉ sau khi cả hai lượt độc lập đã hoàn tất mới mở đối chiếu; AI proposals không tham gia thay thế một trong hai lượt.

### 4.2. Phân loại và xử lý bất đồng

1. **Đánh giá độc lập:** hai reviewer hoàn thành riêng, không nhìn quyết định của nhau hoặc AI proposals.
2. **So sánh nhãn:** sau khi khóa hai lượt, lập bảng đối chiếu theo article_id.
3. **Phân loại bất đồng:**
   - relevance disagreement: nhãn relevance khác nhau;
   - topic disagreement: relevance giống nhau nhưng topic khác;
   - combined disagreement: relevance và topic khác nhau;
   - evidence/process issue: thiếu nội dung, thiếu căn cứ, vi phạm quy tắc hoặc cần xác minh.
4. **Thảo luận reviewer:** reviewer có thể nêu bằng chứng từ nội dung và guideline sau khi đã ghi nhận bất đồng độc lập. Nếu thống nhất, lưu lý do đồng thuận; nếu không, không tự lấy đa số hoặc gợi ý AI làm ground truth.
5. **Chuyển adjudicator:** adjudicator đọc bài đầy đủ, guideline đang có hiệu lực và hai lý do độc lập; nếu có thể, adjudicator không xem AI proposal trước khi đưa quyết định ban đầu. Adjudicator quyết định relevance/topic cuối cùng hoặc yêu cầu xác minh thêm.
6. **Ghi quyết định cuối:** lưu quyết định, bằng chứng, quy tắc áp dụng, lý do bác/giữ từng phương án và người/ngày adjudication trong biên bản phân xử/nhật ký kiểm soát riêng. Không mở rộng schema CSV chín cột trong bước biểu quyết này. Khi được phê duyệt quy trình, chỉ người có thẩm quyền mới cập nhật các trường manual; giữ reviewer_id/date trung thực và theo quy ước do nhóm chốt.
7. **Cập nhật chính sách:** nếu bất đồng phản ánh quy tắc thiếu, ghi nhận ca làm ví dụ hiệu chuẩn; chỉ sửa guideline sau khi nhóm phê duyệt, không thay đổi hồi tố nhãn đã ghi mà không lưu lịch sử.

### 4.3. `review_status` hiện có — không đề xuất trạng thái mới

Đã kiểm tra `5_process/config/labeling_guideline.md`, `5_process/README_PROCESS.md` và script tạo batch. Các trạng thái workflow đã được quy định là:

| Giá trị hiện có | Ý nghĩa hiện hành |
|---|---|
| `PENDING` | Chưa bắt đầu review. |
| `IN_PROGRESS` | Đang review. |
| `COMPLETED` | Đã điền và kiểm tra đủ trường bắt buộc. |
| `NEEDS_ADJUDICATION` | Cần người có thẩm quyền xử lý bất đồng/ca chưa thống nhất. |

Batch 01 và Batch 02 hiện quan sát đều là `PENDING`. Tài liệu này **không thêm** giá trị `review_status` mới. Có thể dùng `NEEDS_ADJUDICATION` cho ca cần phân xử vì trạng thái đó đã tồn tại trong quy trình; không chuyển thành `COMPLETED` cho đến khi quyết định cuối được ghi và kiểm tra.

## 5. Bảng kết quả biểu quyết

Điền tại cuộc họp sau khi từng thành viên đã xem tài liệu:

| Mã | Phương án được chọn | Số phiếu/đồng thuận | Người chịu trách nhiệm áp dụng | Ghi chú/ca hiệu chuẩn |
|---|---|---|---|---|
| BLU-1 |  |  |  |  |
| BLU-2 |  |  |  |  |
| CR-1 |  |  |  |  |
| CR-2 |  |  |  |  |
| CIV-1 |  |  |  |  |
| CIV-2 |  |  |  |  |
| BEN-1 |  |  |  |  |
| BEN-2 |  |  |  |  |
| TOP-1 |  |  |  |  |
| Quy trình hai reviewer/adjudication |  |  |  |  |

## 6. Điều kiện trước khi cập nhật guideline

- Có kết quả biểu quyết và người có thẩm quyền phê duyệt rõ.
- Quy tắc được diễn đạt nhất quán với bốn nhãn và topic A–L; topic_manual vẫn chỉ có một topic cho Relevant/Borderline và để trống cho Not relevant/Uncertain.
- Các ví dụ tranh luận được ghi rõ là ví dụ đã adjudicate hay ca còn mở; không biến AI proposals thành nhãn đã xác nhận.
- Quy trình hai reviewer bảo vệ tính độc lập, lưu được bất đồng và quyết định adjudicator.
- Không thêm `review_status` mới; nếu có đề xuất thay đổi workflow trong tương lai, cần một quyết định riêng.
- Chỉ sau khi đủ điều kiện trên mới cập nhật guideline chính thức theo phê duyệt của nhóm.

## 7. Nguồn tham chiếu

- `5_process/reports/labeling_policy_clarification_proposal.md`
- `5_process/reports/labeling_policy_review_assessment.md`
- `5_process/config/labeling_guideline.md`
- `5_process/README_PROCESS.md`
- `5_process/data/interim/relevance_review_batch_01.csv` (chỉ làm nguồn ví dụ; không sửa)
