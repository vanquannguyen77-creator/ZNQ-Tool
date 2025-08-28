-- ZNQ Heartbeat Script (v4.0)
-- Tác giả: ZNQ
-- Công dụng: Chỉ tạo file heartbeat để tool Python có thể phát hiện trạng thái và chờ đợi.
-- Tương thích hoàn toàn với cơ chế Sequential Launch của ZNQ Tool v4.0.

-- Cấu hình
getgenv().ZNQ_CFG = getgenv().ZNQ_CFG or {
    heartbeat_interval = 2.0, -- Gửi tín hiệu mỗi 2 giây
    notify             = true,   -- Bật/tắt thông báo trong game
}

-- ===== Hàm thông báo (Notify helper) =====
local function notify(title, text, dur)
    if not getgenv().ZNQ_CFG.notify then return end
    pcall(function()
        game:GetService("StarterGui"):SetCore("SendNotification", {
            Title = title or "ZNQ",
            Text  = text or "",
            Duration = dur or 4
        })
    end)
end

-- ===== Các hàm đọc/ghi file của Executor =====
local _isfolder = isfolder or is_folder
local _makefolder = makefolder or make_folder
local _writefile = writefile or write_file

-- ===== Lấy thông tin người chơi và các dịch vụ Roblox =====
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer or Players.PlayerAdded:Wait()
local uid = tostring(LocalPlayer.UserId or 0)

-- ===== Tìm thư mục ZNQ có thể ghi =====
local ZNQ_DIR = nil
local function find_znq_directory()
    -- Các đường dẫn có khả năng chứa thư mục ZNQ
    local potential_paths = {
        "/data/data/" .. game:GetService("CoreGui").RobloxGui.PackageName .. "/files/ZNQ",
        "/storage/emulated/0/Android/data/" .. game:GetService("CoreGui").RobloxGui.PackageName .. "/files/ZNQ",
        "/sdcard/Android/data/" .. game:GetService("CoreGui").RobloxGui.PackageName .. "/files/ZNQ"
    }

    for _, path in ipairs(potential_paths) do
        local success, _ = pcall(function()
            if not _isfolder(path) then
                _makefolder(path)
            end
            -- Thử ghi một file tạm để chắc chắn có quyền
            _writefile(path .. "/.znq_w", "test")
        end)
        if success then
            return path
        end
    end
    return nil -- Trả về nil nếu không tìm thấy thư mục nào có thể ghi
end

ZNQ_DIR = find_znq_directory()

if not ZNQ_DIR then
    notify("ZNQ Heartbeat", "Lỗi: Không tìm thấy hoặc không có quyền ghi vào thư mục ZNQ.", 10)
    return -- Dừng script nếu không tìm thấy thư mục ZNQ
end

notify("ZNQ Heartbeat", "Đã khởi động! Bắt đầu gửi tín hiệu. UID: " .. uid, 5)

-- ===== Chức năng chính: Ghi Heartbeat =====
local heartbeat_path = ZNQ_DIR .. "/" .. uid .. ".json"

local function write_heartbeat()
    -- Tạo một bảng (table) chứa thông tin trạng thái
    local payload = {
        uid = uid,
        timestamp = os.time(),
        placeId = game.PlaceId,
        jobId = game.JobId
    }
    
    -- Chuyển đổi bảng thành chuỗi JSON
    local success, json_data = pcall(function()
        return HttpService:JSONEncode(payload)
    end)
    
    -- Ghi chuỗi JSON vào file
    if success then
        pcall(_writefile, heartbeat_path, json_data)
    end
end

-- ===== Vòng lặp chính =====
-- Tạo một luồng (thread) mới để chạy vòng lặp vô hạn mà không làm treo game
task.spawn(function()
    while task.wait(getgenv().ZNQ_CFG.heartbeat_interval) do
        -- Sử dụng pcall để đảm bảo game không bị crash nếu có lỗi xảy ra
        pcall(write_heartbeat)
    end
end)
