# P4 – Đề xuất làm rõ chính sách gán nhãn thủ công

> **PROPOSAL – CHƯA ĐƯỢC PHÊ DUYỆT**
> Tài liệu nghiên cứu và đề xuất để nhóm thảo luận, không thay thế `5_process/config/labeling_guideline.md`. Không có nhãn AI, dự đoán P4.07 hay kết quả audit nào được chuyển thành nhãn con người đã xác nhận. Không chỉnh sửa CSV hoặc dữ liệu review.

## 1. Mục tiêu và phạm vi

Đề xuất quy tắc vận hành nhất quán cho bốn điểm còn gây cách hiểu khác nhau khi chuẩn bị annotation: (1) `Borderline` so với `Uncertain`; (2) tin hình sự có liên hệ với công việc; (3) phạm vi tin về công chức, viên chức và cán bộ nhà nước; (4) quyền lợi lao động/chính sách an sinh so với từ thiện và hỗ trợ cộng đồng.

Đề xuất giữ nguyên bốn nhãn hiện có (`Relevant`, `Borderline`, `Not relevant`, `Uncertain`), taxonomy A–L và schema chín cột. Không tạo nhãn hoặc topic mới. Mỗi bài vẫn cần được người review đọc độc lập; `confidence` trong file đề xuất AI không phải căn cứ thay cho đánh giá của người review.

Các ví dụ có mã bài dưới đây là ví dụ minh họa lấy từ title và nội dung đầy đủ của Batch 01. Nhãn/topic nêu trong ví dụ là **đề xuất để nhóm hiệu chuẩn**, không phải quyết định ground truth. Nếu chưa có ví dụ dữ liệu phù hợp, ví dụ được ghi rõ là giả định và không gắn article ID.

## 2. Điểm chưa rõ trong guideline hiện tại

1. Mục 2 hướng dẫn dùng `Uncertain` nếu không phân biệt được topic chính, trong khi mục 3 nói không dùng `Uncertain` chỉ vì topic khó phân loại. Hai quy tắc này có thể làm cùng một bài có hai nhãn relevance khác nhau.
2. `Borderline` được mô tả là liên hệ đáng kể nhưng gián tiếp, nhưng chưa quy định ngưỡng cho nội dung lao động phụ trợ, sự kiện đơn lẻ phát sinh từ công việc, hoặc hoạt động hỗ trợ có người lao động là nhóm nhận.
3. Với tin tội phạm, guideline đòi hỏi mối liên hệ trực tiếp/đáng kể với nhiệm vụ nhưng chưa phân biệt đủ giữa địa điểm làm việc, nguyên nhân từ công việc, thời điểm đang làm việc và sự kiện sau ca làm.
4. Quy tắc về công chức đã phân biệt tin chính sách cho nhóm với tin nhân sự cá nhân, nhưng chưa nêu rõ cách xử lý cải cách bộ máy có ảnh hưởng việc làm khi chưa rõ việc nghỉ/giảm biên chế là tự nguyện hay bắt buộc.
5. Hỗ trợ người lao động có thể là quyền lợi theo quan hệ lao động, chính sách an sinh, hoạt động đại diện của công đoàn hoặc thiện nguyện; sự hiện diện của công nhân trong bài tự nó chưa đủ để chọn C, F hoặc H.

## 3. Quy tắc đề xuất cho bốn vấn đề

### 3.1. Phân biệt `Borderline` và `Uncertain`

**Nguyên tắc đề xuất**

- `Relevant`: Có đủ bằng chứng và nội dung lao động/việc làm tại Việt Nam là trọng tâm hoặc một nội dung thực chất, trực tiếp của bài.
- `Borderline`: Có đủ bằng chứng để xác nhận một liên hệ lao động thực chất, nhưng liên hệ đó là gián tiếp, phụ trợ, giới hạn hoặc chỉ chiếm một phần nhỏ so với trọng tâm rộng hơn.
- `Not relevant`: Có đủ bằng chứng để kết luận bài nằm ngoài phạm vi; người lao động hoặc thuật ngữ lao động chỉ xuất hiện ngẫu nhiên, ẩn dụ hoặc không tạo liên hệ thực chất.
- `Uncertain`: Sau khi đọc toàn bộ văn bản hiện có, vẫn thiếu hoặc có mâu thuẫn bằng chứng để xác định bài có thuộc phạm vi hay không. Đây là nhãn về **độ đầy đủ của bằng chứng để ra quyết định**, không phải nhãn độ tin cậy thấp, không phải lựa chọn thay cho topic khó.

**Khi nào dùng**

- Dùng `Borderline` khi đã xác định được mối liên hệ lao động cụ thể nhưng mức độ trung tâm/tầm quan trọng còn hạn chế. Ví dụ: tin tường thuật một vụ việc cá nhân phát sinh trực tiếp trong lúc làm nhiệm vụ nhưng không bàn rộng về an toàn nghề nghiệp.
- Dùng `Uncertain` khi thiếu nội dung, thiếu bối cảnh quyết định, nội dung mâu thuẫn, hoặc không thể xác định đối tượng/sự kiện có thực sự liên quan tới lao động hay không.
- Nếu bài chỉ nhắc người lao động nhưng câu chuyện không bàn công việc, quyền lợi, điều kiện, quan hệ việc làm hay tác động đến việc làm, chọn `Not relevant`. Nếu mối liên hệ lao động là thật nhưng phụ trợ và có ý nghĩa, cân nhắc `Borderline`.
- Nếu nội dung không đầy đủ, không suy ra `Not relevant` từ phần thiếu. Chọn `Uncertain`, ghi rõ thông tin thiếu và đưa đi xác minh/đối chiếu nguồn.
- Không tự động chuyển `Uncertain` thành `Not relevant`. Chỉ người review/adjudicator sau khi có đủ bằng chứng mới được quyết định một nhãn cuối cùng.

### 3.2. Tin hình sự và tội phạm liên quan đến lao động

**Nguyên tắc đề xuất:** xác định **mối liên hệ nhân quả hoặc chức năng với lao động**, không chỉ xác định nơi xảy ra sự việc. Ghi rõ trong lý do bài cho thấy người đó đang thực hiện nhiệm vụ, bị nhắm mục tiêu vì công việc, hoặc quyền/điều kiện lao động là một phần thực chất của vụ việc như thế nào.

- **Topic I:** chọn khi trọng tâm là lừa đảo tuyển dụng, mua bán người, cưỡng bức lao động hoặc bóc lột gắn với việc làm. Lừa đảo khách hàng bằng cách giả danh shipper không đồng nghĩa với lừa đảo người lao động.
- **Topic E:** chọn khi trọng tâm liên quan rủi ro, tai nạn, bạo lực hoặc điều kiện an toàn phát sinh trực tiếp từ nhiệm vụ/môi trường làm việc. Một vụ việc đơn lẻ, chỉ được tường thuật theo hướng hình sự và không phân tích an toàn nghề nghiệp, thường tối đa `Borderline` theo đề xuất này.
- **Topic F:** chỉ chọn khi đại diện công đoàn, thương lượng, tranh chấp hoặc bảo vệ quyền lao động là hoạt động thực chất và có liên hệ với quan hệ lao động. Danh tính cán bộ công đoàn hoặc việc tổ chức công đoàn được nhắc tên không đủ.
- **Topic K:** chỉ chọn khi nội dung nói về pháp luật lao động và việc thực thi/vi phạm/tranh tụng quy định đó. Khởi tố theo luật hình sự hoặc một quy định ngành khác không tự động thành K.
- Vụ án xảy ra trong nhà máy, văn phòng hay khu công nghiệp nhưng không có liên hệ với công việc, quyền lao động hoặc người lao động với tư cách người lao động thì không được đưa vào phạm vi chỉ vì địa điểm.
- Tin hình sự chỉ nêu nghề nghiệp của nạn nhân trong tiểu sử, không cho thấy quan hệ với nhiệm vụ, thì không đủ để gán E.
- Không tự kết luận có vi phạm pháp luật lao động chỉ từ cáo buộc hoặc tình tiết chưa được cơ quan có thẩm quyền kết luận.

### 3.3. Công chức, viên chức và cán bộ nhà nước

**Nguyên tắc đề xuất:** không loại trừ người làm việc trong khu vực công, cũng không coi mọi hoạt động của cơ quan nhà nước là tin lao động. Đánh giá nội dung về việc làm, quan hệ công vụ/việc làm, điều kiện, chế độ hoặc tác động đến một nhóm lao động; phân biệt với quản trị chức vụ và sự kiện chính trị/hành chính.

- Đưa vào khi trọng tâm là chính sách tiền lương, tuyển dụng, chế độ, bảo hiểm, điều kiện làm việc, nghỉ việc/nghỉ hưu hoặc thay đổi biên chế có tác động cụ thể đến người làm việc trong khu vực công.
- Với cải cách bộ máy/tinh giản, đưa vào khi bài cho biết nhóm nào bị tác động, số lượng/quy trình nghỉ việc hoặc quyền lợi liên quan. Phân biệt B (mất việc/cắt giảm ngoài ý muốn) với D (tự nguyện nghỉ, nghỉ hưu hoặc chấm dứt trong quan hệ việc làm) theo bằng chứng. Nếu bài xác nhận tác động đến việc làm nhưng chưa nói rõ tự nguyện hay bắt buộc, có thể xác định relevance trước và chuyển topic/diễn giải sang adjudication; không suy đoán ý chí người lao động.
- Thông tin bổ nhiệm, điều động, phát biểu, hoạt động chính trị hoặc quyết định nhân sự cá nhân không có vấn đề việc làm/quyền lợi rộng hơn thường là `Not relevant`.
- Mức lương hoặc khoản trợ cấp cá nhân chỉ là dữ kiện không đủ để kết luận bài bàn chính sách lao động. Xem xét độ bao phủ, tiêu chí áp dụng, chế độ/quy tắc và trọng tâm nội dung.
- Nếu không xác định được đối tượng là người làm việc trong khu vực công, hoặc không rõ bài nói về chế độ chung hay chỉ sự kiện cá nhân do nội dung thiếu, chọn `Uncertain` thay vì đoán.

Topic có thể phù hợp tùy nội dung: A (tuyển dụng/cung cầu), B (cắt giảm/mất việc ngoài ý muốn), C (lương/quyền lợi), D (nghỉ việc/chấm dứt/nghỉ hưu), E (điều kiện), H (chính sách việc làm/đào tạo/an sinh), K (pháp luật lao động). Đây không phải ánh xạ tự động theo chức danh.

### 3.4. Quyền lợi lao động, an sinh và hoạt động từ thiện

**Nguyên tắc đề xuất:** phân biệt dựa trên cơ sở hưởng, quan hệ chi trả, tính ổn định/điều kiện áp dụng và trọng tâm bài; không chỉ dựa vào việc người nhận là công nhân.

- **C – quyền lợi/đãi ngộ lao động:** tiền lương, thưởng, bảo hiểm hoặc phúc lợi được xác định bởi quan hệ việc làm, hợp đồng, chế độ hay chương trình dành cho nhân viên. Việc công ty gọi một khoản là “chăm lo” chưa tự nó chứng minh đó là quyền lợi theo hợp đồng.
- **H – chính sách việc làm/an sinh:** chương trình/chế độ có mục tiêu và tiêu chí tương đối rõ nhằm hỗ trợ việc làm, đào tạo/chuyển đổi nghề hoặc an sinh cho người lao động/nhóm thụ hưởng. Nếu là hoạt động hỗ trợ một lần từ bên ngoài, không có cơ sở chế độ nhưng người lao động là nhóm nhận chính và nội dung bài tập trung vào hỗ trợ đó, đề xuất tối đa `Borderline/H`.
- **F – công đoàn:** dùng khi trọng tâm là vai trò đại diện/chăm lo/bảo vệ quyền lợi của công đoàn trong quan hệ với đoàn viên/người lao động, không chỉ vì công đoàn là đơn vị tổ chức sự kiện.
- **Từ thiện/hỗ trợ cộng đồng:** khoản quyên góp, cứu trợ hoặc quà tặng tự nguyện không phát sinh từ quan hệ lao động. Nếu công nhân chỉ là một trong nhiều người nhận hoặc chỉ xuất hiện thoáng qua, thường `Not relevant`. Nếu người lao động là nhóm nhận được nêu cụ thể và là trọng tâm, có thể `Borderline/H` theo ngưỡng đề xuất ở trên, không gọi đó là lương/quyền lợi C.
- Nếu nguồn chi trả, điều kiện nhận hoặc bản chất khoản hỗ trợ không thể xác định vì thông tin thiếu, chọn `Uncertain` và không đoán C/H.

## 4. Bảng phân biệt bốn nhãn

| Nhãn | Câu hỏi quyết định | Bằng chứng cần có | Topic |
|---|---|---|---|
| `Relevant` | Quan hệ lao động/việc làm có rõ và là trọng tâm hoặc nội dung thực chất không? | Nội dung cụ thể về việc làm, người lao động, quan hệ, điều kiện, quyền lợi hoặc chính sách tại Việt Nam. | Chọn đúng một A–L nếu đủ căn cứ. |
| `Borderline` | Có liên hệ lao động thực chất, nhưng gián tiếp, phụ trợ, giới hạn hoặc không phải trọng tâm chính không? | Nêu được mối liên hệ cụ thể; không chỉ có từ khóa/nghề nghiệp/địa điểm. | Chọn đúng một A–L nếu đủ căn cứ. |
| `Not relevant` | Có đủ thông tin để kết luận nội dung không thuộc phạm vi không? | Chủ đề chính ngoài lao động; liên hệ lao động chỉ tình cờ hoặc không có. | Để trống. |
| `Uncertain` | Thiếu/mâu thuẫn bằng chứng khiến chưa thể kết luận có thuộc phạm vi hay không? | Nêu rõ phần thiếu/mâu thuẫn và cần xác minh gì. | Để trống. Không tự chuyển thành `Not relevant`. |

`Borderline` không có nghĩa là reviewer thiếu tự tin; `Uncertain` không có nghĩa là topic khó chọn. Nếu relevance rõ nhưng có hai topic cạnh tranh, chọn topic phản ánh trọng tâm chính, nêu topic cạnh tranh trong `review_reason`, và xin adjudication khi cần.

## 5. Decision tree đề xuất

```text
Bắt đầu: đọc toàn bộ title và content
  |
  +-- Nội dung có thiếu, hỏng, mâu thuẫn hoặc không đủ để hiểu đối tượng/sự kiện?
  |      +-- Có; thiếu thông tin quyết định phạm vi --> Uncertain, topic trống,
  |      |   ghi rõ phần cần xác minh. Không tự đổi thành Not relevant.
  |      +-- Không --> tiếp tục
  |
  +-- Bài có quan hệ thực chất với việc làm/người lao động/quyền lao động
  |   tại Việt Nam không (không chỉ từ khóa, nghề nghiệp hay địa điểm)?
  |      +-- Không, và có đủ bằng chứng --> Not relevant, topic trống
  |      +-- Có / có khả năng ảnh hưởng cụ thể --> tiếp tục
  |
  +-- Quan hệ lao động có trực tiếp, rõ và là trọng tâm/nội dung thực chất?
  |      +-- Có --> Relevant
  |      +-- Không; nhưng mối liên hệ vẫn cụ thể, đáng kể, phụ trợ/giới hạn
  |          --> Borderline
  |      +-- Không thể biết do thiếu bằng chứng --> Uncertain
  |
  +-- Chỉ với Relevant/Borderline: chọn đúng một topic A–L theo trọng tâm.
         Nếu topic cạnh tranh: chọn topic chính theo bằng chứng, nêu topic
         cạnh tranh trong review_reason; xin adjudication nếu quy tắc chưa thống nhất.
```

**Không tự động chuyển `Uncertain` thành `Not relevant`.** Thiếu dữ liệu là lý do giữ trạng thái cần xác minh; không phải bằng chứng về việc nằm ngoài phạm vi.

## 6. Bộ ví dụ minh họa từ dữ liệu thực tế

Các kết luận dưới đây là **ví dụ hiệu chuẩn đề xuất**, căn cứ vào nội dung bài, không phải nhãn đã được phê duyệt. Mã topic chỉ nêu khi có căn cứ. “Giả định” nghĩa là tình huống minh họa, không phải bài trong dữ liệu và không có article ID.

### 6.1. Ví dụ cho ranh giới relevance

| Nhãn minh họa | Bài/bằng chứng trong nội dung | Topic gợi ý và lý do |
|---|---|---|
| Relevant | `VNLAB-001450`: bài nêu tỷ lệ giáo viên nghỉ/chuyển việc, nguyên nhân về lương, áp lực và điều kiện làm việc; Bộ GD-ĐT bàn giải pháp để giáo viên yên tâm công tác. | D là lựa chọn phù hợp nếu trọng tâm là nghỉ/chuyển việc; C/E là nhóm cạnh tranh cần ghi nhận nếu reviewer xác định trọng tâm khác. |
| Borderline | `VNLAB-010982`: Công an Đồng Nai trao 300 phần quà cho công nhân; bài tập trung vào chương trình quà Tết một lần, không nói đây là quyền lợi theo hợp đồng/chế độ. | H chỉ là đề xuất nếu nhóm thống nhất hỗ trợ tập trung cho người lao động có thể là liên hệ gián tiếp; không tự động xếp C. |
| Not relevant | `VNLAB-000673`: nội dung yêu cầu tài xế bảo vệ dữ liệu và quyền riêng tư của hành khách, không bàn quyền/điều kiện lao động của tài xế. | Để trống; việc tài xế phải tuân thủ quy định không làm chủ đề thành K. |
| Uncertain | **Giả định:** CSV chỉ có tiêu đề “Công nhân gặp sự cố tại cơ sở”, còn content bị cắt trước khi cho biết người đó đang làm việc hay chỉ có mặt tại địa điểm. | Để trống; thiếu bằng chứng để biết sự kiện có liên quan việc làm hay không. |

### 6.2. Ví dụ cho tin hình sự

| Nhãn minh họa | Bài/bằng chứng trong nội dung | Topic gợi ý và lý do |
|---|---|---|
| Relevant | `VNLAB-008709`: người lao động bị dụ ra nước ngoài bằng lời hứa việc văn phòng/lương cao; bài nêu bị thu hộ chiếu, ép làm việc 12–17 giờ/ngày và phạt nếu muốn nghỉ. | I: tuyển dụng gian dối, mua bán người và bóc lột gắn trực tiếp với lao động là trọng tâm. |
| Borderline | `VNLAB-008895`: bị cáo đặt chuyến xe đến nơi vắng nhằm cướp tài sản; nạn nhân là tài xế công nghệ đang chạy chuyến đã thỏa thuận. | E có thể phù hợp ở mức Borderline nếu nhóm đồng ý vụ án đơn lẻ trong khi làm nhiệm vụ có liên hệ an toàn nghề nghiệp dù bài không bàn biện pháp an toàn. |
| Not relevant | `VNLAB-007573`: đối tượng giả danh shipper để lừa khách hàng thanh toán và lấy thông tin ví/ngân hàng; shipper là danh tính giả được dùng trong thủ đoạn, không phải đối tượng hay vấn đề lao động. | Để trống; không chọn I chỉ vì có chữ “lừa đảo” và “shipper”. |
| Uncertain | **Giả định:** bài nói một người bị hành hung gần nhà máy nhưng không cho biết người đó là nhân viên, đang làm nhiệm vụ hay sự việc bắt nguồn từ công việc. | Để trống; địa điểm một mình không xác lập nexus lao động. |

**Ca cần hiệu chuẩn thêm:** `VNLAB-008407` mô tả mâu thuẫn bắt nguồn từ giao hàng/phản ánh với công ty, nhưng vụ hành hung xảy ra sau đó khi shipper quay lại nhà khách. `VNLAB-008880` và `VNLAB-009945` mô tả bạo lực trong tình huống giao hàng/trao đổi với khách. Nhóm cần thống nhất nếu liên hệ nhân quả trực tiếp nhưng sự việc là tin hình sự đơn lẻ thì xếp Borderline/E hay loại khi nội dung không đề cập điều kiện an toàn. Không dùng riêng nơi xảy ra hoặc nghề nghiệp làm tiêu chí.

### 6.3. Ví dụ cho công chức, viên chức và cán bộ nhà nước

| Nhãn minh họa | Bài/bằng chứng trong nội dung | Topic gợi ý và lý do |
|---|---|---|
| Relevant | `VNLAB-001450`: bài bàn tình trạng giáo viên nghỉ/chuyển việc, nguyên nhân về thu nhập và điều kiện công tác, cùng giải pháp chính sách cho đội ngũ. | D nếu trọng tâm là rời bỏ/chuyển việc; đây là nội dung việc làm của một nhóm, không phải tin bổ nhiệm cá nhân. |
| Borderline | **Giả định:** bài chủ yếu tường thuật một sự kiện cơ quan nhà nước, chỉ có một đoạn ngắn nhắc đề xuất chế độ làm việc cho công chức nhưng không nêu đối tượng, phạm vi hay tác động cụ thể. | Nếu mối liên hệ được xác nhận nhưng phụ trợ, có thể Borderline/C hoặc E theo trọng tâm; nếu không đủ nội dung để xác nhận thì Uncertain, không ép vào Borderline. |
| Not relevant | `VNLAB-005536`: bài nêu một Phó giám đốc sở xin không bổ nhiệm lại/xin thôi việc và khoản trợ cấp riêng hơn 95 triệu đồng; phần còn lại tóm tắt quá trình công tác, không phân tích chế độ áp dụng cho nhóm. | Để trống theo ranh giới đề xuất; đây là trường hợp cần nhóm thống nhất phạm vi công chức và trợ cấp cá nhân. |
| Uncertain | **Giả định:** nội dung bị cắt sau thông tin “tỉnh sắp xếp nhân sự”, không rõ tác động đến việc làm, chính sách áp dụng hay chỉ thay đổi chức vụ. | Để trống; xác minh nội dung trước khi gán nhãn. |

`VNLAB-003841` là đối chứng hữu ích: bài tính lương theo hệ số của Chủ tịch UBND phường/quận, nêu rõ mức cơ sở và phụ cấp chức vụ, nhưng không mô tả chính sách lương cho nhóm hoặc điều kiện lao động rộng hơn. Cần phân biệt bài giải thích một mức lương chức danh với bài phân tích chế độ/đãi ngộ cho nhóm công chức.

### 6.4. Ví dụ cho quyền lợi, an sinh và từ thiện

| Nhãn minh họa | Bài/bằng chứng trong nội dung | Topic gợi ý và lý do |
|---|---|---|
| Relevant | `VNLAB-001411`: nội dung nêu hơn 339.000 người lao động nhận hơn 963 tỉ đồng từ Quỹ Bảo hiểm thất nghiệp và việc giải quyết hồ sơ. | C: chế độ bảo hiểm/quyền lợi được quy định, gắn với bảo vệ người lao động. |
| Borderline | `VNLAB-010982`: quà Tết một lần do Công an tỉnh trao cho 300 công nhân; người nhận là nhóm lao động được nêu rõ nhưng không có căn cứ cho thấy đây là chế độ/entitlement. | H chỉ khi nhóm thống nhất hỗ trợ tập trung cho người lao động là liên hệ phụ trợ đáng kể; nếu chỉ là sự kiện xã hội chung thì Not relevant. |
| Not relevant | `VNLAB-006996`: trọng tâm là chủ quán tự tặng suất ăn miễn phí cho shipper/người khó khăn như việc thiện cá nhân; không nêu chính sách, quyền lợi hay quan hệ chi trả lao động. | Để trống; người nhận làm nghề shipper không biến hoạt động từ thiện thành C hoặc H. |
| Uncertain | **Giả định:** bài viết nói “người lao động được hỗ trợ” nhưng không nêu ai chi trả, điều kiện nhận, đây là chế độ hay quyên góp, và phần nội dung về bản chất khoản hỗ trợ bị thiếu. | Để trống cho đến khi xác minh; không đoán C/H. |

Đối chứng: `VNLAB-004239` nêu công ty trao quà Trung thu thường niên cho hơn 17.000 công nhân, đồng thời nói về chăm lo/bảo vệ quyền lợi và bảo đảm việc làm. Đây là căn cứ mạnh hơn hoạt động từ thiện cá nhân để xét liên hệ lao động, nhưng topic C (quyền lợi) hay H (hỗ trợ/an sinh) vẫn cần dựa vào việc khoản quà có phải chế độ/benefit hay chỉ là hoạt động chăm lo.

## 7. Quy trình review đề xuất

Quy trình giữ nguyên schema chín cột và batch 50 bài; không thêm trường.

1. Đọc toàn bộ `title` và `content`; không dùng riêng tiêu đề, từ khóa hoặc dự đoán P4.07.
2. Tóm tắt một câu về chủ đề chính của bài và đối tượng/sự kiện trung tâm.
3. Xác định mối liên hệ cụ thể với lao động/việc làm/quyền lợi tại Việt Nam. Với tin hình sự, ghi mối liên hệ công việc (nhiệm vụ, quan hệ nhân quả, đối tượng bị nhắm tới hoặc điều kiện lao động), không chỉ địa điểm.
4. Áp dụng tiêu chí đưa vào/loại ra và decision tree ở mục 5.
5. Chọn đúng một trong bốn nhãn. Dùng `Uncertain` chỉ khi thiếu/mâu thuẫn bằng chứng khiến chưa quyết định được phạm vi; giữ danh sách cần xác minh/adjudication thay vì tự chuyển nhãn.
6. Chỉ khi nhãn là `Relevant` hoặc `Borderline`, chọn một topic A–L phản ánh nội dung lao động chính. Nếu có topic cạnh tranh, chọn theo trọng tâm bài và nêu lựa chọn còn lại trong `review_reason`; bất đồng chưa được quy tắc giải quyết thì chuyển adjudication.
7. Ghi `review_reason` ngắn, nêu bằng chứng cụ thể trong bài và vì sao bằng chứng đáp ứng/không đáp ứng tiêu chí. Không suy diễn kết luận pháp lý từ cáo buộc.
8. Ghi `reviewer_id` của người thật và `review_date` theo `YYYY-MM-DD` sau khi người đó hoàn tất review. Không ghi các trường manual bằng đề xuất AI; không đổi `review_status` thành hoàn tất trước khi review được xác nhận.
9. Với hiệu chuẩn, hai reviewer gán độc lập cùng một tập nhỏ, so sánh bất đồng trước khi xem gợi ý AI, thống nhất quy tắc qua adjudication rồi mới mở rộng sang batch. Ghi nhận quy tắc được thông qua, không sửa âm thầm lịch sử.

## 8. Những điểm cần nhóm thống nhất hoặc biểu quyết

1. **`Uncertain`:** có đồng ý giới hạn nhãn này cho thiếu/mâu thuẫn bằng chứng về relevance, và không dùng khi chỉ khó chọn topic?
2. **Ngưỡng `Borderline`:** liên hệ phụ trợ nào được xem là “đáng kể”; bài cần có tác động cụ thể hay chỉ cần nhóm lao động là trọng tâm của một sự kiện?
3. **Tin hình sự:** vụ việc đang diễn ra trong nhiệm vụ hoặc phát sinh trực tiếp từ tương tác công việc nhưng bài chỉ tường thuật sự kiện có được xếp Borderline/E không? Sự cố ngoài ca làm nhưng do công việc kích hoạt xử lý ra sao?
4. **Công chức:** có đưa tin lương/trợ cấp cá nhân vào phạm vi nếu bài không phân tích chế độ nhóm không? Mức nào của cải cách bộ máy được xem là tác động việc làm đủ rõ?
5. **Hỗ trợ cộng đồng:** hoạt động một lần nhắm riêng đến công nhân có thể là Borderline/H không, hay chỉ đưa vào khi là chính sách/chế độ có tiêu chí rõ? Cách phân biệt quà từ người sử dụng lao động với từ thiện bên ngoài?
6. **Topic chính:** khi bài đồng thời nói đến lương/giờ làm (C/E), nghỉ việc/chính sách (D/C/H), hoặc công đoàn/quyền lợi (F/C/H), dùng trọng tâm biên tập hay phần có bằng chứng nhiều nhất làm tiêu chí?
7. **Adjudication:** ai là người ra quyết định cuối cùng, và làm thế nào lưu bất đồng mà không biến đề xuất AI thành nhãn con người?

## 9. Đánh giá mức độ sẵn sàng để bắt đầu Batch 01

**Chưa khuyến nghị bắt đầu gán nhãn chính thức độc lập cho toàn Batch 01 trước khi nhóm thống nhất các điểm ở mục 8.** Pre-manual validation cho thấy cấu trúc Batch 01/02 hợp lệ, các trường manual còn trống và đề xuất AI được tách riêng; nhưng Batch 01 có nhiều ca ranh giới đúng ở bốn lĩnh vực trên. Guideline hiện tại cũng có mâu thuẫn trực tiếp về việc dùng `Uncertain` khi topic khó phân biệt.

Có thể bắt đầu **vòng hiệu chuẩn chưa ghi vào CSV** với các ca minh họa: `VNLAB-008895`, `VNLAB-008407`, `VNLAB-008880`, `VNLAB-005536`, `VNLAB-003841`, `VNLAB-010982`, `VNLAB-000693`, `VNLAB-006996` và `VNLAB-004239`. Hai người review độc lập nội dung, thảo luận, rồi người phụ trách biểu quyết quy tắc trước khi ghi nhãn chính thức. Các bài AI gợi ý chỉ là đầu vào cần được kiểm tra độc lập.

## 10. Kết luận và khuyến nghị

Thông qua một chính sách theo hai trục riêng: **(a) đủ bằng chứng để kết luận relevance hay chưa** và **(b) mối liên hệ lao động mạnh hay gián tiếp đến mức nào**. Theo đề xuất, `Uncertain` xử lý thiếu/mâu thuẫn bằng chứng; `Borderline` xử lý liên hệ thực chất nhưng gián tiếp/phụ trợ. Không dùng địa điểm, nghề nghiệp, tên cơ quan, từ “công đoàn”, “trợ cấp” hay “shipper” làm căn cứ đơn lẻ.

Khuyến nghị nhóm biểu quyết các điểm ở mục 8, áp dụng thử trên một tập hiệu chuẩn chung, lưu quyết định và ví dụ đã adjudicate thành phụ lục chính thức nếu được duyệt. Chỉ sau khi có xác nhận của nhóm mới cập nhật guideline chính thức. Tài liệu này **chỉ là đề xuất**, không thay đổi guideline, nhãn, topic, proposal AI hay trạng thái review hiện có.
