# Đánh giá đề xuất làm rõ chính sách gán nhãn thủ công

> **Phạm vi:** Đánh giá tài liệu đề xuất, không phê duyệt hay cập nhật guideline. Không thay đổi CSV, nhãn AI, nhãn thủ công hoặc trạng thái review.

## 1. Tóm tắt

Đề xuất tại `labeling_policy_clarification_proposal.md` nhìn chung tương thích với bốn nhãn hiện có, taxonomy A–L và các giới hạn của `labeling_guideline.md`. Điểm mạnh nhất là tách `Uncertain` (thiếu bằng chứng để quyết định relevance) khỏi `Borderline` (đã có liên hệ lao động thực chất nhưng gián tiếp/giới hạn), không dùng topic khó làm lý do cho `Uncertain`, và yêu cầu đọc toàn bộ nội dung thay vì dựa vào từ khóa hay địa điểm.

Tuy vậy, các thuật ngữ “đáng kể”, “phụ trợ”, “trọng tâm”, “một phần nhỏ” và “tác động cụ thể” chưa có ngưỡng vận hành. Một số ví dụ dùng ca còn tranh luận làm ví dụ cho nhãn/topic cụ thể; đặc biệt `VNLAB-001450` được gợi ý topic D dù nội dung cũng tập trung đáng kể vào lương, áp lực và điều kiện làm việc, còn `VNLAB-010982` được xếp Borderline/H theo điều kiện chưa được nhóm chốt. Nên dùng chúng làm ca hiệu chuẩn mở, không làm đáp án chuẩn trước khi biểu quyết.

**Kết luận:** Chưa nên dùng đề xuất nguyên trạng làm tiêu chuẩn annotation độc lập. Cần nhóm chốt ngưỡng Borderline, topic chính và cách adjudication; sau đó hiệu chuẩn hai người trên các ca bất đồng trước khi cập nhật guideline chính thức.

## 2. Bảng tổng hợp bốn vấn đề

| Vấn đề | Đề xuất hiện tại | Rủi ro khi áp dụng | Khuyến nghị | Có cần nhóm biểu quyết không? |
|---|---|---|---|---|
| 1. `Borderline` và `Uncertain` | `Borderline` = có liên hệ lao động thực chất nhưng gián tiếp/phụ trợ/giới hạn; `Uncertain` = thiếu hoặc mâu thuẫn bằng chứng về việc có thuộc phạm vi hay không. Không tự chuyển `Uncertain` sang `Not relevant`; nếu relevance rõ mà topic khó thì chọn topic chính và ghi topic cạnh tranh. | “Liên hệ thực chất/đáng kể” và “phụ trợ” chưa được đo; một nội dung chưa đầy đủ có thể vẫn đủ bằng chứng để kết luận relevance, nhưng decision tree hiện dễ khiến người review chọn `Uncertain` chỉ vì có thiếu sót không quan trọng. Mệnh đề “một phần nhỏ” có thể làm Borderline rộng hơn guideline hiện tại. | Chốt rằng `Uncertain` áp dụng khi thiếu/mâu thuẫn thông tin **cần thiết cho quyết định relevance**, không phải bất kỳ trường nội dung nào bị thiếu. Định nghĩa một bộ câu hỏi về nexus, trọng tâm và độ cụ thể; ghi ví dụ đã adjudicate. Nếu relevance rõ nhưng topic cạnh tranh, không đổi sang `Uncertain`; dùng topic chính theo tiêu chí đã thống nhất và chuyển `NEEDS_ADJUDICATION` khi cần. | **Có.** Cần chốt ngưỡng “liên hệ đáng kể” và liệu `Uncertain` có giới hạn đúng như đề xuất hay không. |
| 2. Tin hình sự liên quan lao động | Xét nexus nhân quả/chức năng với nhiệm vụ, không chỉ địa điểm; I cho bóc lột/lừa đảo tuyển dụng, E cho rủi ro an toàn gắn việc, F cho đại diện/tranh chấp thực chất, K chỉ cho luật lao động. Vụ việc đơn lẻ chỉ tường thuật hình sự thường tối đa Borderline. | “Phát sinh trực tiếp từ nhiệm vụ” chưa giải quyết nhất quán các ca đang làm, sau ca nhưng do công việc kích hoạt, hay bị nhắm mục tiêu khi đang làm. “Không bàn biện pháp an toàn” có thể khiến một vụ việc vẫn có nexus bị loại hoặc được giữ Borderline tùy cách hiểu. F có thể bị mở rộng nếu hành động công đoàn thực tế nhưng sự kiện nền là nợ cá nhân. | Dùng bài kiểm tra nexus: (a) người đó đang thực hiện nhiệm vụ hoặc sự kiện phát sinh từ nhiệm vụ/quan hệ lao động; (b) nghề nghiệp không chỉ là tiểu sử; (c) bài có bằng chứng trực tiếp. Quy định riêng cách xử lý tin tường thuật đơn lẻ, không mặc nhiên yêu cầu bài phải đề xuất giải pháp an toàn. Đối với F, xác định nội dung bảo vệ/đại diện có liên quan quyền lao động hay chỉ hỗ trợ cá nhân. | **Có.** Đặc biệt cho `VNLAB-008895`, `VNLAB-008407`, `VNLAB-008880`, `VNLAB-009945`, `VNLAB-012710` và `VNLAB-000693`. |
| 3. Công chức, viên chức, cán bộ nhà nước | Không loại trừ khu vực công; đưa vào nếu bài tập trung chính sách/điều kiện/chế độ hoặc tác động việc làm theo nhóm. Tin nhân sự cá nhân thường Not relevant; phân biệt B (mất việc/cắt giảm ngoài ý muốn) với D (tự nguyện nghỉ/chấm dứt/nghỉ hưu). | “Chính sách theo nhóm” so với cá nhân chưa rõ khi bài nêu một trường hợp nhưng giải thích quy định chung. Khi việc làm bị tác động nhưng ý chí nghỉ việc chưa rõ, proposal nói xác định relevance trước và chuyển topic/diễn giải sang adjudication nhưng chưa nêu bước/trạng thái cụ thể. `VNLAB-001450` là ví dụ phù hợp relevance khu vực công, nhưng topic D không hiển nhiên hơn C/E. | Xác định mức phân tích chính sách/đối tượng áp dụng quan trọng hơn số lượng nhân vật; một bài về một người vẫn có thể thuộc phạm vi nếu giải thích một chế độ chung. Với thay đổi biên chế, chỉ gán B khi có bằng chứng về cắt giảm/mất việc ngoài ý muốn; nếu chưa biết tính tự nguyện mà relevance rõ, ghi ca cần phân xử, không suy đoán B/D. Tách quyết định relevance khỏi chọn topic và chỉ hoàn tất sau adjudication theo workflow hiện có. | **Có.** Cần thống nhất xử lý bài về một cá nhân có dẫn quy định chung, trợ cấp cá nhân và cải cách bộ máy. |
| 4. Quyền lợi, an sinh và từ thiện | C là quyền lợi/đãi ngộ từ quan hệ việc làm/chế độ; H là chính sách việc làm/an sinh và có thể tối đa Borderline/H cho hỗ trợ một lần tập trung vào người lao động; F khi công đoàn thực hiện vai trò đại diện/chăm lo/bảo vệ thực chất; từ thiện chung thường Not relevant nếu người lao động chỉ được nhắc thoáng qua. | H có thể bị mở rộng thành mọi hoạt động tặng quà cho công nhân, dù taxonomy mô tả chính sách/chương trình hỗ trợ. “Tập trung vào nhóm lao động” và “một lần” chưa đủ phân biệt thiện nguyện với chương trình an sinh. Quà do công ty trao không mặc nhiên là quyền lợi theo hợp đồng; có thể là chăm lo tùy nghi. Topic F/C/H có thể cùng hợp lý cho sự kiện công đoàn tặng quà. | Phân loại theo căn cứ hưởng, nguồn/quan hệ chi trả, tiêu chí áp dụng, tính chương trình và trọng tâm nội dung. Không coi quà là C chỉ vì công ty chi trả hoặc gọi là chăm lo; không coi quà một lần là H nếu không có mục tiêu/chương trình hỗ trợ lao động rõ. Dùng F khi vai trò công đoàn và người lao động là nội dung thực chất; khi chưa phân biệt được C/H/F từ văn bản, đánh dấu cần phân xử hoặc Uncertain nếu chính relevance cũng chưa rõ. | **Có.** Cần biểu quyết rõ quà một lần từ bên ngoài, quà thường niên của doanh nghiệp và hỗ trợ từ công đoàn được đưa vào tới mức nào, topic nào là chính. |

## 3. Đánh giá từng đề xuất và đối chiếu guideline

### 3.1. `Borderline` và `Uncertain`

**Nội dung rõ và tương thích**

- Proposal giải quyết đúng mâu thuẫn trong guideline: mục 2 có câu “nếu không thể phân biệt chủ đề chính, chọn `Uncertain`”, trong khi mục 3 nói không dùng nhãn này chỉ vì khó phân loại topic.
- Định nghĩa `Uncertain` dựa trên bằng chứng thiếu/mâu thuẫn phù hợp với mục 3 của guideline. Quy tắc không tự chuyển thành `Not relevant` cũng đúng: thiếu bằng chứng không phải bằng chứng rằng bài ngoài phạm vi.
- Topic để trống cho `Uncertain` và `Not relevant`, còn Relevant/Borderline mới chọn một A–L, giữ đúng schema.

**Còn mơ hồ/rủi ro**

- Guideline mô tả Borderline là liên hệ “đáng kể nhưng gián tiếp, bối cảnh hoặc tác động đến việc làm chưa cụ thể”. Proposal thêm “phụ trợ”, “giới hạn”, “chỉ chiếm một phần nhỏ”. Các từ này có thể hiểu là mở rộng Borderline cho bài có nhắc đến lao động nhưng nội dung lao động không đủ đáng kể.
- Decision tree hỏi “nội dung có thiếu, hỏng, mâu thuẫn” ở bước đầu. Nên nói rõ chỉ chọn Uncertain nếu phần thiếu/mâu thuẫn ảnh hưởng trực tiếp quyết định thuộc phạm vi. Một bài có một đoạn lỗi nhưng các đoạn khác đủ rõ không nên tự động Uncertain.
- “Nếu liên hệ lao động là thật nhưng phụ trợ và có ý nghĩa” chưa nói “có ý nghĩa” đo bằng sự kiện, tỷ trọng nội dung, tác động cụ thể hay đối tượng nhận.
- Proposal đồng thời nói relevance rõ thì chọn topic chính, và topic chưa thống nhất thì xin adjudication. Cần chỉ rõ adjudication là trạng thái workflow (ví dụ `NEEDS_ADJUDICATION`) chứ không dùng `Uncertain` thay thế cho bất đồng topic.

**Khuyến nghị:** Giữ phân biệt hai chiều, nhưng thêm điều kiện “thiếu thông tin thiết yếu để quyết định relevance” cho Uncertain; Borderline phải có nexus lao động cụ thể được nêu trong bài. Đề nghị ghi lại các ca đã phân xử làm chuẩn, thay vì cố đặt một ngưỡng định lượng không có căn cứ.

### 3.2. Tin hình sự và tội phạm

**Nội dung rõ và tương thích**

- Tiêu chí không dùng địa điểm hoặc nghề nghiệp của nạn nhân đơn lẻ tương thích với phần ranh giới hiện có của guideline.
- Các định hướng I/E/F/K nhìn chung đúng taxonomy: mua bán người/lừa tuyển dụng gắn lao động vào I; an toàn nghề nghiệp vào E; hoạt động đại diện/tranh chấp thực chất vào F; chỉ pháp luật lao động vào K.
- Cảnh báo không suy ra vi phạm pháp luật lao động chỉ từ cáo buộc phù hợp nguyên tắc guideline.

**Kiểm tra ví dụ và topic**

- `VNLAB-008709` là ví dụ Relevant/I vững: nội dung không chỉ nói về vụ án mà nêu lời hứa việc làm/lương cao, thu hộ chiếu, ép làm việc 12–17 giờ/ngày, phạt khi muốn nghỉ. Nexus tuyển dụng và bóc lột là trung tâm.
- `VNLAB-008895` là ví dụ Borderline/E hợp lý nhưng vẫn cần chốt chính sách: nội dung mô tả bị cáo đặt chuyến để cướp tài sản của tài xế và nạn nhân đang thực hiện chuyến xe. Mối liên hệ công việc trực tiếp, nhưng bài là tường thuật xét xử, không phân tích hệ thống an toàn. Gắn E có căn cứ; mức Borderline thay vì Relevant phụ thuộc ngưỡng về sự kiện đơn lẻ.
- `VNLAB-007573` là ví dụ Not relevant phù hợp: nội dung về lừa đảo khách hàng ví điện tử, đối tượng giả danh shipper; không có dấu hiệu shipper/người lao động bị lừa tuyển dụng hay bóc lột. Không gán I chỉ vì có chữ “lừa đảo”.
- Tình huống giả định “bị hành hung gần nhà máy nhưng chưa rõ người đó có đang làm việc hay không” phù hợp Uncertain, vì vị trí không xác nhận nexus lao động.
- `VNLAB-008407` có nexus bắt nguồn từ lần giao hàng/phản ánh nhưng người giao hàng quay lại nhà khách sau đó; đây là ca cần hiệu chuẩn thực sự, không nên dùng như ví dụ minh họa đã ngầm chấp thuận Borderline/E.
- `VNLAB-008880` và `VNLAB-009945` xảy ra trong tương tác giao hàng với khách, nhưng nội dung chủ yếu là bạo lực và xử lý vụ việc. Đề xuất chưa đưa ra quy tắc phân biệt trường hợp đang giao hàng với vụ việc sau khi nhiệm vụ kết thúc.
- `VNLAB-000693` được đề xuất trong danh sách hiệu chuẩn nhưng không có ví dụ/bảng kết luận riêng: công đoàn đề nghị điều tra và bảo vệ cán bộ bị đe dọa do khoản vay của công nhân. Hành động công đoàn là thực tế, nhưng quan hệ với quyền/quan hệ lao động không rõ; F/Borderline không thể coi là đáp án đã thống nhất.

**Khuyến nghị:** Không yêu cầu bài phải đề cập biện pháp phòng ngừa mới được xét E; trọng tâm là nexus được chứng minh trong bài và ngưỡng phạm vi của corpus. Bổ sung ca `VNLAB-000693` vào phần ví dụ mở cho F, không gán kết luận trước khi nhóm thống nhất.

### 3.3. Công chức, viên chức và cán bộ nhà nước

**Nội dung rõ và tương thích**

- Nguyên tắc không tự động đưa vào hoặc loại ra chỉ vì chủ thể là cơ quan/cán bộ nhà nước phù hợp với guideline.
- Phân biệt chính sách áp dụng nhóm với tin bổ nhiệm/điều động hay quyết định cá nhân lặp lại đúng phần ranh giới hiện tại.
- Phân biệt B với D theo tính chất mất việc/cắt giảm hay tự nguyện nghỉ/chấm dứt phù hợp guideline; không suy đoán ý chí là điểm thận trọng đúng.

**Kiểm tra ví dụ và topic**

- `VNLAB-005536`: nội dung là một công chức tự gửi đơn xin thôi việc, được chấp thuận và nhận trợ cấp cá nhân 95 triệu đồng; mô tả quá trình công tác, không phân tích chế độ áp dụng cho nhóm. Ví dụ Not relevant có căn cứ theo guideline hiện hành, dù phạm vi công chức/trợ cấp cá nhân vẫn là điểm nhóm có thể muốn chốt.
- `VNLAB-003841`: nội dung giải thích hệ số và mức lương chức danh Chủ tịch UBND phường/quận, gồm phụ cấp chức vụ, nhưng không phân tích chính sách tiền lương cho nhóm hoặc điều kiện việc làm. Not relevant là cách áp dụng hợp lý theo guideline hiện hành.
- `VNLAB-001450`: nội dung bàn tỷ lệ giáo viên nghỉ/chuyển việc, lương, áp lực, điều kiện làm việc và giải pháp chính sách cho đội ngũ. Relevant phù hợp; tuy nhiên D không phải topic rõ ràng duy nhất. C (lương/quyền lợi) và E (áp lực/giờ làm/điều kiện) cũng có căn cứ, và bài có nhiều nội dung. Cần mô tả đây là ví dụ Relevant nhưng topic cần adjudication/được chọn theo trọng tâm, không nêu D như “lựa chọn phù hợp” không điều kiện.
- Tình huống Borderline giả định nói chỉ có một đoạn nhắc chế độ nhưng không nêu đối tượng, phạm vi hay tác động. Nếu không biết chế độ có áp dụng cho công chức/người lao động hay không, nội dung hiện chưa chứng minh nexus; nhãn phù hợp có thể là Uncertain, không phải Borderline. Dòng giải thích có nhận ra khả năng này, nhưng nhãn trong bảng vẫn dễ bị sao chép thành đáp án.
- Tình huống Uncertain về “tỉnh sắp xếp nhân sự” phù hợp nếu văn bản bị cắt và chưa biết thay đổi việc làm hay chỉ đổi chức vụ.
- `VNLAB-009389` (trong Batch 01 nhưng không được dùng làm ví dụ chính) nêu 473 cán bộ/công chức/viên chức/người lao động nghỉ hưu sớm/nghỉ việc trong đợt tinh gọn bộ máy và dự kiến khoản chi trả. Đây là ví dụ tốt cho relevance theo tác động nhóm, nhưng B/D cần dựa vào bằng chứng về tự nguyện/bắt buộc; nếu không rõ, dùng làm ca thảo luận, không áp topic trước.

**Khuyến nghị:** Dùng `VNLAB-005536` và `VNLAB-003841` làm cặp phân biệt thông tin nhân sự/lương cá nhân với chính sách nhóm; dùng `VNLAB-009389` làm ca chưa chốt topic. Với `VNLAB-001450`, giữ relevance làm ví dụ, nhưng bỏ cách trình bày D như topic mặc định; quyết định topic theo tiêu chí trọng tâm thống nhất.

### 3.4. Quyền lợi lao động, an sinh và từ thiện

**Nội dung rõ và tương thích**

- Phân biệt C với quyền lợi gắn quan hệ việc làm/chế độ và phân biệt từ thiện bên ngoài phù hợp hướng dẫn hiện có.
- Quy tắc người nhận là công nhân không đủ để suy ra quyền lợi lao động là điểm đúng.
- Hướng dẫn không đoán C/H khi nguồn chi trả/bản chất hỗ trợ bị thiếu tương thích cách dùng Uncertain.
- Topic F được gắn với hoạt động đại diện/chăm lo/bảo vệ thực chất, phù hợp với guideline; tuy nhiên bản thân việc một công đoàn tổ chức sự kiện và trao quà chưa nhất thiết là hoạt động đại diện quyền lao động.

**Kiểm tra ví dụ và topic**

- `VNLAB-001411` phù hợp Relevant/C: nội dung nêu việc chi trả từ Quỹ Bảo hiểm thất nghiệp theo nghị quyết, đối tượng là người lao động và số lượng/khoản chi cụ thể.
- `VNLAB-006996` phù hợp Not relevant: trọng tâm là một chủ quán tặng suất ăn miễn phí cho shipper/người khó khăn như hoạt động thiện nguyện cá nhân; không nêu quyền lợi, chế độ hay chính sách việc làm.
- `VNLAB-010982` có mô tả cụ thể chương trình “Xuân công nhân”, 300 phần quà do Công an tỉnh trao; bài cũng nói về đóng góp của công nhân và an toàn/quyền lợi. Borderline có thể bảo vệ được nếu nhóm cho rằng một hoạt động tập trung riêng cho công nhân là liên hệ phụ trợ đáng kể. H chưa chắc: quà một lần không phải tự thân là chính sách an sinh theo định nghĩa H; guideline hiện tại cho phép cân nhắc H/Borderline nếu hỗ trợ người lao động là trọng tâm, nên ví dụ này là ca biểu quyết chứ chưa phải chuẩn.
- `VNLAB-004239` nêu doanh nghiệp trao quà Trung thu thường niên cho hơn 17.000 công nhân, nói hoạt động chăm lo/bảo vệ quyền lợi và cố gắng bảo đảm việc làm. Đây là nexus lao động rõ hơn từ thiện cá nhân, nhưng nội dung không khẳng định quà là entitlement theo hợp đồng hay chế độ. Proposal thận trọng khi chưa chọn C/H; nên giữ như một ca so sánh thay vì xem thường niên là đủ điều kiện C.
- Tình huống Uncertain về nguồn chi trả và điều kiện nhận bị thiếu phù hợp, miễn là thông tin đó thực sự quyết định việc đây là quyền lợi/an sinh lao động hay từ thiện ngoài phạm vi.
- Chưa có ví dụ cụ thể trong bảng minh họa Topic F. `VNLAB-001095` có công đoàn tổ chức buổi sinh hoạt gia đình và trao 43 phần quà cho đoàn viên khó khăn; nội dung liên quan người lao động nhưng chủ đề F (đại diện/bảo vệ quyền) so với H/C (hỗ trợ/quyền lợi) cần được thảo luận, không nên tự động gán F.

**Khuyến nghị:** Giữ điều kiện “hỗ trợ người lao động là trọng tâm” nhưng nhóm cần định nghĩa dấu hiệu trọng tâm, mục tiêu và quan hệ chi trả. Bổ sung ví dụ mở cho C (quỹ bảo hiểm), H (hỗ trợ có chương trình/đối tượng rõ), F (hoạt động đại diện quyền lợi) và Not relevant (từ thiện cá nhân), đồng thời giữ `VNLAB-010982`, `VNLAB-004239` và `VNLAB-001095` làm ca so sánh cần adjudication.

## 4. Các điểm cần sửa trước khi đưa đề xuất ra biểu quyết

1. **Phân loại điều kiện thiếu:** thay “nội dung có thiếu” bằng “thiếu/mâu thuẫn bằng chứng cần thiết để quyết định relevance”; nêu rằng lỗi/thiếu không ảnh hưởng kết luận không buộc dùng Uncertain.
2. **Ngưỡng Borderline:** yêu cầu một nexus cụ thể trong nội dung; phân biệt “chủ đề lao động phụ nhưng thực chất” với “chỉ nhắc người lao động”. Nêu ít nhất một ví dụ chuẩn đã được nhóm adjudicate cho mỗi dạng.
3. **Topic cho ví dụ giáo viên:** không giới thiệu D như topic hiển nhiên ở `VNLAB-001450`; bài đề cập đồng thời nghỉ/chuyển việc, lương và điều kiện. Nếu giữ làm ví dụ, ghi rõ relevance là điểm minh họa, còn topic là ca cần chọn theo trọng tâm.
4. **Ví dụ Borderline giả định về công chức:** không đặt Borderline nếu nội dung chưa chứng minh đối tượng/phạm vi chế độ. Tách hai tình huống: liên hệ phụ trợ đã xác nhận (có thể Borderline) và nexus còn thiếu (Uncertain).
5. **Hỗ trợ một lần:** cụ thể hóa điều kiện nào làm quà/hỗ trợ từ bên ngoài đủ liên quan để cân nhắc H/Borderline; nếu chưa có chính sách/an sinh, tránh diễn đạt H như topic đương nhiên.
6. **Bổ sung F:** thêm ca hoạt động công đoàn thực tế nhưng nexus lao động chưa chắc như `VNLAB-000693` hoặc `VNLAB-001095`, ghi rõ đây là ví dụ tranh luận chứ không phải đáp án.
7. **Adjudication:** chỉ rõ khi nào chuyển `review_status` sang `NEEDS_ADJUDICATION`, ai quyết định cuối cùng, và cách ghi quyết định/độ bất đồng mà không nhập gợi ý AI vào các trường manual.

## 5. Khuyến nghị và mức sẵn sàng

- **Mức sẵn sàng:** Có thể dùng tài liệu làm cơ sở thảo luận/hiệu chuẩn, chưa đủ để làm chuẩn bắt buộc cho gán nhãn độc lập.
- **Bước tiếp theo đề xuất:** Nhóm biểu quyết các câu hỏi tại mục 8 của proposal sau khi làm rõ các điểm ở mục 4 của báo cáo này. Sau đó, hai reviewer gán độc lập một tập nhỏ gồm các ca `VNLAB-008895`, `VNLAB-008407`, `VNLAB-000693`, `VNLAB-005536`, `VNLAB-003841`, `VNLAB-009389`, `VNLAB-010982`, `VNLAB-004239`, `VNLAB-001095` và `VNLAB-006996`; so sánh bất đồng, adjudicate rồi mới sửa guideline nếu được phê duyệt.
- Đây là khuyến nghị phân tích, không phải sự chấp thuận chính sách. Không có nhãn nào được xác nhận trong báo cáo này.

## 6. Giới hạn

Đánh giá ví dụ dựa trên nội dung trong Batch 01 được cung cấp và các ghi nhận audit/validation hiện có; các quyết định cuối cùng thuộc reviewer/adjudicator con người. Báo cáo không kiểm chứng tính đúng sai pháp lý của bài báo, không suy rộng từ batch audit ra toàn corpus, và không thay đổi guideline hoặc tiến độ review.
