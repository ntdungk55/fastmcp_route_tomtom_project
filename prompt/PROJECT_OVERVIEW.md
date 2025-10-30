# Đây là file gì?

Đây là file bắt đầu của dự án . File này được đặt trong thư mục /prompt/ mới mục tiêu giới thiệu tổng quan về dự án.

## 1 Chính sách sử dụng/Quyền hạn

- Developer : Toàn quyền sửa file này ở tất cả các mục
- LLM : Khi auto gennerate code , LLM sẽ được sửa mục "## 3 Các tính năng và tình trạng" Tuyệt đối không sửa các mục khác .

## 2 Mục tiêu

- Là một MCP server trung gian giúp MCP client kết nối đến các dịch vụ mà không hỗ trợ MCP server
- Người dùng có thể yêu cầu server tạo thêm tính năng bằng cách request.Các bước làm như sau :
    + Step 1 : Từ phía mcp client, người dùng request tính năng mong muốn mà mcp server hiện tại chưa có.
    + Step 2 : MCP Server sẽ phê duyệt tính năng đó có tính khả thi hay không rồi yêu cầu LLM ở server tạo tính năng đó.
    + Step 3 : Khi đó Server sẽ tự động tìm kiếm nguồn thông tin , tạo các file prompt theo template dựa trên nghiệp vụ người dùng mô
    tả kèm thông tin mà LLM có thể thu hoạch được từ nhiều nguồn.
    + Step 4 : LLM trên Server sẽ dựa theo prompt folder tạo code theo yêu cầu rồi sau đó chạy test thử .
    + Step 5 : Gửi file report về tính năng người dùng mong muốn xem đã đáp ứng nhu cầu của họ chưa.

## 3 Các tính năng và tình trạng

Hướng dẫn điền thông tin : 
- Tính năng : danh sách các tính năng , khi update thêm tính năng sẽ thêm vào đây như ví dụ sau
    Ví dụ : 
        * Các tính năng : 
            + Lưu các điểm đến
            + Chỉ dẫn đường đi
            + Thông tin về tình trạng giao thông
- Tình trạng : Các giá trị thể hiện tình trạng bao gồm : Chưa phát triển, Đang phát triển, Đã outdate , Lỗi , Hoàn thành

- Cụm tool cung cấp cho người dùng tìm kiếm đường giữa 2 điểm, kiểm tra tình trạng giao thông:
    * Tính năng : 
        + Lưu các điểm đến
        + Chỉ dẫn đường đi
        + Thông tin về tình trạng giao thông
    * Tình trạng : Hoàn thành

- Tạo tính năng theo yêu cầu của người dùng:
    * Tính năng : 
    * Tình trạng : Chưa phát triển

## 4 Hướng dẫn tạo tính năng từ yêu cầu người dùng

- Step 1 : Khi nhận yêu cầu của người dùng LLM sẽ phân tích yêu cầu người dùng bằng cách dựa vào thông tin người dùng 
    cung cấp rồi tìm kiếm thông tin liên quan . Sau khi đủ thông tin xây dựng một sơ đồ theo chuẩn được mô tả ở file prompt\specs\diagram_instruction.md. 
- Step 2 : Sau khi có diagram và các file mô tả quay lại file này ở prompt\PROJECT_OVERVIEW.md cập nhật tính năng ở mục
    "## Các tính năng và tình trạng" theo mẫu đã được hướng dẫn .
- Step 3 : Dựa vào diagram và mô tả cùng với hướng dẫn ở file prompt\LLM_GUIDE_FOR_AUTOMATIC_CODE_GENERATION.md , Tạo code dựa trên code đã có .
- Step 4 : Tạo các file test tự động các trường hợp có thể xảy ra . Nếu có vấn đề thì quay lại bước 3 .
- Step 5 : Thông báo đến người dùng kiểm tra lại rồi nhận feedback của người dùng lưu vào file review dành riêng cho tính năng này.

## Quy định cách thể hiện nội dung cho tất cả các tài liệu được tự động tạo từ LLM

- Ngôn ngữ sử dụng mặc định : Tiếng Việt
- Định dạng file text là .md



