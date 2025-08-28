-- ZNQ Rejoin Check Script v3.0
-- Tương thích với ZNQ Tool Python (phiên bản có auto-rejoin).
-- Nhiệm vụ: Tạo một "file tín hiệu" để tool Python biết rằng game và executor đã khởi động thành công.

-- Tool Python sẽ tự động thay thế "{}" bằng đường dẫn file chính xác khi nó cài đặt script này.
local signal_file_path = "{}"

-- Hàm để ghi file một cách an toàn, tránh gây lỗi
local function write_file(path, content)
    pcall(function()
        local file, err = io.open(path, "w")
        if file then
            file:write(content or "ok")
            file:close()
        end
    end)
end

-- Tạo file tín hiệu ngay khi script chạy
write_file(signal_file_path)

-- Thông báo trong console của executor để bạn biết script đang hoạt động
print("[ZNQ Tool] Script Rejoin Check đã được kích hoạt. File tín hiệu đã được tạo.")

-- (Tùy chọn) Hiển thị một thông báo nhỏ trên màn hình để xác nhận
-- Lưu ý: Phần này có thể không hoạt động trên tất cả các executor.
local success, coreGui = pcall(game.GetService, game, "CoreGui")
if success and coreGui then
    -- Tạo một giao diện người dùng (GUI) mới
    local gui = Instance.new("ScreenGui", coreGui)
    gui.Name = "ZNQ_Notification_GUI"
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

    -- Tạo một nhãn văn bản (TextLabel) để hiển thị thông báo
    local label = Instance.new("TextLabel", gui)
    label.Size = UDim2.new(0, 350, 0, 40)
    label.Position = UDim2.new(0.5, -175, 0, 20) -- Căn giữa trên cùng màn hình
    label.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
    label.BackgroundTransparency = 0.2
    label.TextColor3 = Color3.fromRGB(10, 255, 120) -- Màu xanh lá cây sáng
    label.Font = Enum.Font.SourceSansSemibold
    label.TextSize = 18
    label.Text = "[ZNQ Tool] Rejoin Script Active"
    
    -- Bo tròn các góc của nhãn
    local corner = Instance.new("UICorner", label)
    corner.CornerRadius = UDim.new(0, 6)
    
    -- Tự động xóa thông báo sau 10 giây
    task.delay(10, function()
        gui:Destroy()
    end)
end
