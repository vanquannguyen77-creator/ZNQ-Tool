-- ZNQ Heartbeat Script (v5.0 - Rokid-Style Final)
-- Tác giả: ZNQ
-- Công dụng: Phiên bản cuối cùng, hoạt động theo cơ chế đơn giản nhất,
-- ghi trực tiếp vào thư mục làm việc của executor để đảm bảo tương thích tối đa.

-- Cấu hình
getgenv().ZNQ_CFG = getgenv().ZNQ_CFG or {
    heartbeat_interval = 2.0,
    notify             = true,
}

-- ===== Hàm thông báo (Notify helper) =====
local function notify(title, text, dur)
    pcall(function()
        game:GetService("StarterGui"):SetCore("SendNotification", {
            Title = title or "ZNQ",
            Text = text or "",
            Duration = dur or 8
        })
    end)
end

-- ===== Các hàm đọc/ghi file của Executor =====
-- Chúng ta chỉ cần hàm writefile
local _writefile_func = writefile or write_file

-- ===== Lấy thông tin người chơi =====
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer or Players.PlayerAdded:Wait()
local uid = tostring(LocalPlayer.UserId or 0)

-- ===== Kiểm tra xem hàm writefile có tồn tại không =====
if not _writefile_func then
    notify("ZNQ Lỗi Nghiêm Trọng", "Executor này không hỗ trợ hàm 'writefile'. Tool không thể hoạt động.", 15)
    return
end

notify("ZNQ Heartbeat (v5.0)", "Đã khởi động! Bắt đầu gửi tín hiệu. UID: " .. uid, 8)

-- ===== Chức năng chính: Ghi Heartbeat =====
-- Ghi trực tiếp vào thư mục làm việc hiện tại của executor
local heartbeat_path = uid .. ".json" 

task.spawn(function()
    while task.wait(getgenv().ZNQ_CFG.heartbeat_interval) do
        local payload = {
            uid = uid,
            timestamp = os.time(),
            placeId = game.PlaceId,
            jobId = game.JobId
        }
        -- Sử dụng pcall để đảm bảo an toàn tuyệt đối
        local success, json_data = pcall(HttpService.JSONEncode, HttpService, payload)
        if success then
            pcall(_writefile_func, heartbeat_path, json_data)
        end
    end
end)
