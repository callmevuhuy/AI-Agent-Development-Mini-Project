# BÁO CÁO HIỆN TRẠNG DỰ ÁN AI AGENT DEVELOPMENT

**Dự án:** Global Business Travel Operations Agent  
**Phạm vi báo cáo:** Chức năng đã triển khai, khoảng cách so với định hướng AI Agent và hướng khắc phục.  
**Thời điểm đối chiếu:** 19/11/2026.

## 1. Tổng quan và nhận định chính

Dự án được xây dựng để hỗ trợ ba giai đoạn của chuyến công tác quốc tế: chuẩn bị trước chuyến đi, xử lý sự cố trong chuyến đi và rà soát chi phí sau chuyến đi. Hệ thống sử dụng dữ liệu giả lập, có giao diện web và dòng lệnh, đồng thời cung cấp công cụ tra cứu dữ kiện, tìm chính sách và tạo bản nháp nghiệp vụ.

Tuy nhiên, phiên bản hiện tại **chưa tích hợp mô hình ngôn ngữ lớn (LLM), chưa gọi API suy luận của nhà cung cấp mô hình và chưa chạy mô hình ngôn ngữ cục bộ**. Việc nhận diện yêu cầu, chọn workflow, gọi công cụ và xây dựng phản hồi chủ yếu được thực hiện bằng quy tắc và mã nguồn viết sẵn. Vì vậy, mô tả sát với hiện trạng là **hệ thống hỗ trợ nghiệp vụ theo quy tắc, có các thành phần nền tảng cho kiến trúc agent**.

Theo phản hồi của giảng viên được chủ dự án cung cấp, việc thiếu lớp LLM khiến sản phẩm bị đánh giá là lạc trọng tâm AI Agent Development. Báo cáo này ghi nhận đó là thiếu sót chính: dự án đã đầu tư vào công cụ, kiểm soát và giao diện, nhưng chưa chứng minh được vai trò của mô hình trong quá trình lựa chọn hành động và xử lý kết quả. Những thành phần đã có vẫn có giá trị kỹ thuật, song không thay thế được phần thực nghiệm với LLM mà giảng viên kỳ vọng.

## 2. Những thành phần dự án đã có

### 2.1. Dữ liệu và ba quy trình nghiệp vụ

Dữ liệu hiện có gồm **6 yêu cầu công tác, 4 hồ sơ nhân viên, 5 hành trình, 3 báo cáo chi phí và 13 đoạn chính sách**. Các tình huống bao gồm hồ sơ hợp lệ, thiếu thông tin, chờ phê duyệt, bị từ chối hoặc hủy, chuyến bay chậm và xung đột chính sách. Đây là dữ liệu giả lập phục vụ kiểm chứng, không phải dữ liệu doanh nghiệp thật.

Ba workflow đã được triển khai:

- **Trước chuyến đi:** đọc yêu cầu công tác và trạng thái phê duyệt, tra chính sách, kiểm tra điều kiện và tạo checklist draft. Khi thiếu dữ liệu hoặc chưa được duyệt, hệ thống trả trạng thái tương ứng.
- **Trong chuyến đi:** đọc hành trình, nhận diện sự cố từ dữ liệu, tra hướng dẫn và tạo draft hỗ trợ. Hệ thống không tự đổi vé hoặc đặt dịch vụ.
- **Sau chuyến đi:** đọc báo cáo chi phí, tính toán bằng công cụ xác định, đối chiếu chính sách và tạo draft rà soát. Kết quả không phải quyết định hoàn tiền hoặc phê duyệt chi phí.

Nguồn triển khai: [dữ liệu giả lập](../data/) và [ba workflow](../src/travel_agent/workflows/).

### 2.2. Công cụ, trạng thái và kiểm soát thực thi

Dự án có **19 công cụ** với JSON Schema, registry và allowlist theo workflow. Dispatcher kiểm tra lời gọi trước khi thực thi, bao gồm tên công cụ, cấu trúc tham số, quyền và ngân sách bước. Công cụ trả kết quả có cấu trúc để phân biệt thành công, lỗi và khả năng retry.

`RunState` lưu ngữ cảnh lượt chạy, phase, số bước, kết quả công cụ an toàn, trace và trạng thái kết thúc. Orchestrator hỗ trợ retry tối đa hai lần sau lần thử đầu đối với lỗi được đánh dấu retryable. Hệ thống có thể dừng ở `completed`, `needs_input`, `needs_human`, `awaiting_approval` hoặc các trạng thái lỗi thay vì luôn báo hoàn tất.

Phân quyền được áp dụng cho Employee, Reviewer, Approver và Admin trong môi trường demo. Employee bị giới hạn theo chủ hồ sơ; Approver bị giới hạn theo yêu cầu pending được phân công và phạm vi đọc. Đây là kiểm tra quyền trên danh tính giả lập, chưa phải cơ chế đăng nhập xác thực người dùng thật.

Nguồn: [registry](../src/travel_agent/registry.py), [dispatcher](../src/travel_agent/dispatcher.py), [state](../src/travel_agent/state.py) và [orchestrator](../src/travel_agent/orchestrator.py).

### 2.3. Truy xuất chính sách, memory và bản nháp

Hệ thống tìm chính sách bằng BM25 ngoại tuyến, có lọc quyền truy cập, metadata nguồn, phiên bản và citation. Các nhánh xử lý bao gồm không tìm thấy evidence, xung đột phiên bản và loại bỏ đoạn chứa mẫu chỉ thị injection. Kiểm tra claim hiện dựa trên từ khóa, câu chứa evidence và phủ định.

Memory được tách thành ngữ cảnh phiên và tùy chọn người dùng. Session có TTL mặc định 30 phút; việc lưu preference yêu cầu sự đồng ý tường minh. Draft có mã ổn định theo workflow và nguồn nhằm hạn chế tạo trùng khi chạy lại. Giao diện web cho phép theo dõi hội thoại, chuyến đi, draft, handoff, audit và trace.

Nguồn: [RAG](../src/travel_agent/rag/), [memory](../src/travel_agent/memory/store.py), [draft workspace](../src/travel_agent/mock_systems/draft_workspace.py) và [web demo](../src/travel_agent/web_demo.py).

## 3. Khoảng cách trọng tâm: chưa có LLM trong vòng thực thi agent

### 3.1. Quyết định hiện tại được thực hiện bằng code

Trong [planner.py](../src/travel_agent/planner.py), hàm `plan()` gọi bộ nhận diện ý định theo quy tắc rồi trả workflow và ID. [nlu.py](../src/travel_agent/nlu.py) xử lý mẫu câu, từ khóa và định dạng; [conversation.py](../src/travel_agent/conversation.py) chọn nhánh hội thoại, gọi workflow và định dạng kết quả. Chuỗi công cụ của ba workflow được lập trình sẵn.

Do đó, việc hệ thống trả lời được các câu demo chưa chứng minh mô hình hiểu yêu cầu hoặc tự lựa chọn hành động. Phần quan sát được là khả năng xử lý những nhánh đã được lập trình. Khi người dùng diễn đạt khác, quy tắc có thể vẫn nhận diện được nếu đã bao phủ mẫu tương ứng; dự án chưa có bằng chứng đủ rộng về khả năng xử lý yêu cầu ngoài tập mẫu.

Vấn đề không nằm ở việc sử dụng quy tắc cho mọi thành phần. Tính toán chi phí, kiểm tra quyền và validation cần được thực hiện bằng code đáng tin cậy. Khoảng trống là dự án chưa phân chia được một cách thực nghiệm **phần mô hình đề xuất và diễn giải** với **phần application kiểm tra và thực thi**.

### 3.2. Có tool/schema chưa chứng minh LLM function calling

Registry, schema và dispatcher là nền tảng cần thiết để kiểm soát công cụ. Tuy nhiên, trong bản hiện tại, code quyết định tên công cụ và arguments rồi gọi dispatcher. Chưa có phản hồi từ LLM chứa tool call để application tiếp nhận và kiểm tra.

Dự án cũng chưa thể hiện vòng lặp: mô hình nhận yêu cầu → đề xuất công cụ → application thực thi → trả observation cho mô hình → mô hình quyết định gọi tiếp, hỏi lại hoặc kết thúc. Vì vậy, báo cáo không thể xem các lời gọi hàm Python hiện có là bằng chứng đã triển khai function calling của LLM.

Tương tự, tuy dự án có truy xuất, evidence và citation, phần sinh/diễn giải câu trả lời vẫn theo code và mẫu. Có thể ghi nhận đây là **cơ chế truy xuất và kiểm tra căn cứ phục vụ kiến trúc RAG**, nhưng chưa có bằng chứng về một pipeline RAG dùng LLM để sinh câu trả lời từ ngữ cảnh truy xuất.

### 3.3. Cần phân biệt thiếu LLM với thiếu API nghiệp vụ thật

Không sử dụng API bên thứ ba tự nó không đủ để kết luận một hệ thống không có AI: LLM có thể được chạy cục bộ. Đối với dự án này, điểm thiếu cụ thể là **cả API suy luận lẫn mô hình ngôn ngữ cục bộ đều chưa được tích hợp**. [requirements.txt](../requirements.txt) và [pyproject.toml](../pyproject.toml) hiện khai báo các phụ thuộc phục vụ validation, kiểm thử và đóng gói; mã nguồn chưa có lớp gọi mô hình.

Ngược lại, việc không kết nối API đặt vé, thanh toán, email hoặc hồ sơ nhân sự thật phù hợp với phạm vi giả lập của [đề bài](../Requirement%20Docs/Global_Business_Travel_Operations_Agent_Mini_Project.pdf). Các dịch vụ nghiệp vụ này không phải phần cần bổ sung để giải quyết nhận xét lạc đề. Cần ưu tiên tích hợp mô hình vào việc xử lý yêu cầu và đề xuất công cụ, trong khi vẫn giữ mock systems và giới hạn draft-only.

### 3.4. Hệ quả 

Trong bối cảnh phản hồi của giảng viên, phần chưa đáp ứng nằm ở trọng tâm phát triển agent dựa trên mô hình: dự án chưa cho thấy LLM lựa chọn tool, tạo arguments, sử dụng observation và điều chỉnh bước tiếp theo. Tên gọi “AI Agent” và sự đầy đủ của giao diện không bù đắp được bằng chứng còn thiếu này.

Do đó, cần thừa nhận khoảng cách thay vì chỉ đổi cách diễn đạt để bảo vệ hiện trạng. Có thể kế thừa phần công cụ, phân quyền, state và kiểm thử đã xây dựng; nhưng chỉ sau khi có tích hợp và thực nghiệm mới được kết luận về hành vi của agent dùng LLM. Việc kết nối mô hình để viết lại câu trả lời cuối cùng cũng chưa đủ chứng minh khả năng lựa chọn và điều phối công cụ.

## 4. Kết quả kiểm chứng hiện có và giới hạn

Các báo cáo evaluator đã lưu ghi nhận **baseline 31/31 ca đạt** và **after 62/62 ca đạt**. Báo cáo hồi quy ghi nhận không có ca cũ chuyển từ đạt sang không đạt; 31 ca được bổ sung là ca mới. Vì thế, tăng từ 31 lên 62 ca không có nghĩa độ chính xác tăng gấp đôi hoặc có 31 lỗi đã được sửa. Nguồn: [baseline](../eval/reports/baseline.md), [after](../eval/reports/after.md) và [regression](../eval/reports/regression.md).

Trong lượt kiểm tra trước khi dọn môi trường, pytest ghi nhận 179 test đạt và một test HTTP bị sandbox chặn kết nối localhost. Test HTTP đó đạt khi được chạy riêng ngoài sandbox. Đây là kết quả kiểm tra chức năng trước đó; báo cáo này không thực hiện một lần chạy lại test hoặc evaluator mới.

Các kết quả trên có giá trị xác nhận những nhánh đã kiểm tra, nhưng còn ba giới hạn đáng chú ý:

- **Tập câu hỏi đã biết:** 31 ca web lấy từ các prompt demo; chưa có tập độc lập đủ để kết luận khả năng tổng quát hóa.
- **Tiêu chí tool/arguments còn hẹp:** việc tool kỳ vọng xuất hiện và ID có mặt trong trace chưa xác minh toàn bộ chuỗi công cụ, thứ tự phụ thuộc hoặc mọi tham số quan trọng.
- **Grounding chỉ có claim đại diện:** metric `grounding_citation_accuracy` hiện lấy giá trị 0/1 từ một ca mẫu; không phải độ chính xác ngữ nghĩa trên toàn bộ câu trả lời.

Đặc biệt, các số đo này được tạo từ hệ thống theo quy tắc. Chúng **chưa đánh giá khả năng suy luận, lựa chọn tool, sinh arguments hoặc lỗi bịa thông tin của LLM**, vì dự án chưa sử dụng LLM. Nguồn cách tính: [evaluator](../eval/run_eval.py) và [web card checks](../src/travel_agent/demo_evaluation.py).

## 5. Những phần còn thiếu và hướng khắc phục

### 5.1. Bổ sung lớp mô hình và vòng lặp công cụ — ưu tiên đầu tiên

Phần phát triển tiếp theo cần kết nối một LLM qua API suy luận hoặc triển khai cục bộ. Mô hình nhận yêu cầu, mô tả tool được phép và context phù hợp để đề xuất tên công cụ cùng arguments. Application tiếp tục kiểm tra bằng dispatcher, thực thi công cụ và trả observation cho mô hình. Vòng lặp kết thúc khi đủ kết quả, thiếu thông tin, cần người xử lý hoặc hết budget.

Danh tính, role và approval scope phải do application cấp; mô hình không tự khai quyền. Tính toán, kiểm tra chứng từ, quyết định quyền và thao tác ghi vẫn do code kiểm soát. Phản hồi của mô hình cần dựa trên facts/evidence đã nhận; không được tự kết luận đã duyệt, đã gửi hoặc đã hoàn tiền khi hệ thống chưa thực hiện.

Đây là **hướng khắc phục chưa triển khai**. Bằng chứng hoàn thành cần có ít nhất một trace thực tế cho thấy đề xuất tool của mô hình, kết quả dispatcher/tool và bước xử lý tiếp theo; một cuộc gọi mô hình chỉ sinh lời chào hoặc viết lại văn bản không đáp ứng mục tiêu đó.

### 5.2. Đánh giá lại bằng tập độc lập

Sau khi có LLM, cần giữ hệ thống quy tắc hiện tại làm baseline và so sánh trên cùng tập ca độc lập. Tập này nên có câu diễn đạt mới, câu tiếng Việt, yêu cầu thiếu hoặc mơ hồ, tool lỗi, policy conflict và injection. Đánh giá cần kiểm tra đúng tool, đúng arguments, đúng outcome, evidence hỗ trợ claim và không có side effect bị cấm.

Đối với bản dùng LLM, cần ghi phiên bản mô hình, cấu hình, thời điểm chạy và số lần lặp; đo thêm độ trễ, số lần gọi, token và chi phí nếu môi trường cung cấp. Không đưa giá trị ước đoán thành kết quả thực nghiệm.

### 5.3. Hoàn thiện các giới hạn kỹ thuật còn lại

- **Ngôn ngữ và grounding:** BM25 và claim checker còn dựa nhiều vào từ khóa/tiếng Anh; cần kiểm thử diễn đạt lại, tiếng Việt có dấu, điều kiện, phủ định và nhiều claim có citation.
- **Budget và timeout:** giới hạn bước chủ yếu theo `RunState`; lookup phụ và yêu cầu nhiều phần có state riêng. Chưa có budget tổng cho cả tin nhắn và timeout cưỡng chế khi handler bị treo.
- **Lưu trữ hội thoại:** CSV hiện giữ `user_message` và `bot_response`, có che một số mẫu nhạy cảm. Cần đối chiếu yêu cầu không lưu full raw conversation mặc định và chuyển sang tối thiểu hóa log; không thể coi bộ lọc mẫu là đã loại mọi thông tin nhạy cảm.
- **Tính tái lập và tài liệu:** cần đồng bộ mô tả metric, mốc số test và đường dẫn demo/schema, lưu log cho bản nộp và xác minh cài mới. Đăng nhập thật, database và kiểm thử tải là hướng mở rộng nếu thay đổi phạm vi sử dụng.

Nguồn: [retriever](../src/travel_agent/rag/retriever.py), [claim checker](../src/travel_agent/rag/claim_evidence_check.py), [conversation](../src/travel_agent/conversation.py), [logging](../src/travel_agent/logging_utils.py) và [README](../README.md).

## 6. Kết luận

Dự án đã xây dựng được một hệ thống nghiệp vụ giả lập có ba workflow, công cụ có hợp đồng, phân quyền, state, memory, truy xuất chính sách, draft và kiểm thử. Đây là phần nền có thể tiếp tục sử dụng khi phát triển agent.

Thiếu sót lớn nhất là chưa đưa LLM vào quá trình xử lý yêu cầu và quyết định lời gọi công cụ. Theo định hướng mà giảng viên phản hồi, phiên bản hiện tại chưa thể hiện đầy đủ trọng tâm AI Agent Development; các kết quả kiểm thử đang chứng minh độ đúng của hệ thống theo quy tắc, chưa chứng minh năng lực agent dùng mô hình.

Ưu tiên tiếp theo là tích hợp LLM vào vòng đề xuất công cụ–nhận observation–quyết định bước tiếp, giữ các kiểm soát hiện có và đánh giá lại trên tập độc lập. Trước khi hoàn thành phần đó, dự án cần được trình bày đúng như một nguyên mẫu điều phối nghiệp vụ theo quy tắc có nền tảng kiến trúc agent, đồng thời công bố rõ những năng lực còn chưa có.
