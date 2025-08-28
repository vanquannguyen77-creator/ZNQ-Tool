-- ZNQ Check (Rokid-compatible) - by ZNQ
-- Mục tiêu:
-- 1) Ghi marker định kỳ: ZNQ/<UserId>.json  (username, userId, placeId, jobId, ts)
-- 2) Lắng nghe lệnh từ tool: ZNQ/cmd.json   ({action="rejoin", same_server=true/false})
-- 3) Hotkeys (tuỳ chọn): F8 (rejoin server cũ), F9 (rejoin server mới)

-- ================== CẤU HÌNH NHANH ==================
getgenv().ZNQ_CFG = getgenv().ZNQ_CFG or {
    marker_dir      = "ZNQ",     -- Thư mục làm việc chung với tool
    update_interval = 2,         -- giây: tần suất cập nhật marker
    enable_hotkeys  = true       -- F8/F9
}

getgenv().disable_ui = getgenv().disable_ui or false -- Nếu executor có overlay UI, cho phép ẩn

-- ============== TIỆN ÍCH & KIỂM TRA API =============
local HttpService = game:GetService("HttpService")
local Players     = game:GetService("Players")
local TPService   = game:GetService("TeleportService")
local UIS         = game:GetService("UserInputService")

local function has(fn) return type(fn) == "function" end

local _isfile    = has(isfile)    and isfile    or function(_) return false end
local _isfolder  = has(isfolder)  and isfolder  or function(_) return false end
local _makefolder= has(makefolder)and makefolderor function(_) end
local _writefile = has(writefile) and writefile or function(_) end
local _readfile  = has(readfile)  and readfile  or function(_) return nil end
local _delfile   = has(delfile)   and delfile   or function(_) end

-- ============== LẤY THÔNG TIN NGƯỜI CHƠI =============
local function safeGetLocalPlayer()
    local plr = Players.LocalPlayer or Players.PlayerAdded:Wait()
    -- Ensure Character & Id sẵn sàng
    if not plr.Character then plr.CharacterAdded:Wait() end
    return plr
end

local function getSnapshot()
    local plr = safeGetLocalPlayer()
    local userId   = tostring(plr.UserId or 0)
    local username = tostring(plr.Name or "Unknown")
    local placeId  = tostring(game.PlaceId or 0)
    local jobId    = tostring(game.JobId or "")
    return {
        username = username,
        userId   = userId,
        placeId  = placeId,
        jobId    = jobId,
        ts       = os.time()
    }
end

-- ============== GHI MARKER ĐỊNH KỲ ===================
local CFG = getgenv().ZNQ_CFG
local MARKER_DIR = tostring(CFG.marker_dir or "ZNQ")
local UPDATE_INTERVAL = tonumber(CFG.update_interval or 2)

local function ensureWorkspace()
    if not _isfolder(MARKER_DIR) then
        _makefolder(MARKER_DIR)
    end
end

local function writeMarker()
    pcall(function()
        ensureWorkspace()
        local snap = getSnapshot()
        local fname = string.format("%s/%s.json", MARKER_DIR, snap.userId)
        _writefile(fname, HttpService:JSONEncode(snap))
    end)
end

-- ============== LẮNG NGHE LỆNH TỪ TOOL ===============
-- Tool sẽ ghi file ZNQ/cmd.json với nội dung như:
-- { "action": "rejoin", "same_server": true }
-- same_server = false  => TeleportToPlaceInstance(placeId, jobId)
-- same_server = true => Teleport(placeId) (server random)

local CMD_FILE = MARKER_DIR.."/cmd.json"
local last_cmd_raw = ""

local function handleCommand(cmd)
    if type(cmd) ~= "table" then return end
    local action = tostring(cmd.action or "")
    if action == "rejoin" then
        local same = cmd.same_server == true
        local snap = getSnapshot()
        if same and snap.jobId and #snap.jobId > 0 then
            TPService:TeleportToPlaceInstance(tonumber(snap.placeId), snap.jobId, Players.LocalPlayer)
        else
            TPService:Teleport(tonumber(snap.placeId), Players.LocalPlayer)
        end
    end
end

local function pollCommand()
    pcall(function()
        if _isfile(CMD_FILE) then
            local raw = _readfile(CMD_FILE)
            if raw and #raw > 0 and raw ~= last_cmd_raw then
                last_cmd_raw = raw
                local ok, obj = pcall(function() return HttpService:JSONDecode(raw) end)
                if ok and obj then
                    handleCommand(obj)
                    -- tuỳ chọn: xoá lệnh sau khi xử lý để tránh lặp
                    -- _delfile(CMD_FILE)
                end
            end
        end
    end)
end

-- =================== HOTKEYS (tuỳ chọn) ===============
if CFG.enable_hotkeys and UIS and UIS:IsKeyDown ~= nil then
    UIS.InputBegan:Connect(function(input, gpe)
        if gpe or not input.KeyCode then return end
        local kc = input.KeyCode
        if kc == Enum.KeyCode.F8 then
            -- Rejoin cùng server (nếu có jobId)
            local s = getSnapshot()
            if s.jobId and #s.jobId > 0 then
                TPService:TeleportToPlaceInstance(tonumber(s.placeId), s.jobId, Players.LocalPlayer)
            else
                TPService:Teleport(tonumber(s.placeId), Players.LocalPlayer)
            end
        elseif kc == Enum.KeyCode.F9 then
            -- Rejoin server mới (random)
            local s = getSnapshot()
            TPService:Teleport(tonumber(s.placeId), Players.LocalPlayer)
        end
    end)
end

-- ================== VÒNG LẶP CHÍNH ===================
task.spawn(function()
    while true do
        writeMarker()
        for _=1, UPDATE_INTERVAL*10 do
            task.wait(0.1)
            pollCommand()
        end
    end
end)

-- ================== UI (tuỳ chọn) =====================
-- Nếu executor của bạn có API draw UI overlay, bạn có thể thêm.
-- Ở đây giữ mặc định tắt UI để nhẹ:
if not getgenv().disable_ui then
    -- Đặt disable_ui=true nếu không muốn log spam
    print("[ZNQ] Check Lua started. Marker: "..MARKER_DIR.."/*.json, Cmd: "..CMD_FILE)
end
