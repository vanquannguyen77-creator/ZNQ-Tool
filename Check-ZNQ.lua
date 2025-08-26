-- ZNQ Check Script (lean)
-- Phù hợp autoexec đa-executor, không phụ thuộc http_request
-- Tùy chỉnh qua getgenv():
--   getgenv().disable_ui = true/false
--   getgenv().ZNQ_CFG = { marker_dir = "ZNQ", update_interval = 2 }

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TeleportService = game:GetService("TeleportService")
local HttpService = game:GetService("HttpService")

local LP = Players.LocalPlayer
if not LP then
    repeat task.wait() until Players.LocalPlayer
    LP = Players.LocalPlayer
end

local G = getgenv and getgenv() or _G
local CFG = (G.ZNQ_CFG and type(G.ZNQ_CFG) == "table") and G.ZNQ_CFG or {}
local DISABLE_UI = (G.disable_ui == true)

local MARKER_DIR = tostring(CFG.marker_dir or "ZNQ")
local UPDATE_INTERVAL = tonumber(CFG.update_interval or 2)
if UPDATE_INTERVAL < 1 then UPDATE_INTERVAL = 1 end

-- Trạng thái chung để Python có thể đọc nếu cần (qua remote debug)
G.ZNQ_STATE = {
    username = LP and LP.Name or "Unknown",
    userId   = LP and LP.UserId or 0,
    placeId  = game.PlaceId,
    jobId    = game.JobId,
    startTs  = os.time()
}

-- ========= UI gọn =========
local function mount_gui()
    local ok, gui = pcall(function()
        local sg = Instance.new("ScreenGui")
        sg.Name = "ZNQ_UI"
        sg.ResetOnSpawn = false

        -- ưu tiên gethui nếu có
        local parent = (gethui and gethui()) or game:FindFirstChildOfClass("CoreGui")
        if not parent then
            parent = LP:FindFirstChildOfClass("PlayerGui") or LP:WaitForChild("PlayerGui")
        end
        if syn and syn.protect_gui then pcall(syn.protect_gui, sg) end
        sg.Parent = parent

        -- nếu đã có cũ thì dọn
        local old = parent:FindFirstChild("ZNQ_UI")
        if old and old ~= sg then pcall(function() old:Destroy() end) end

        local label = Instance.new("TextLabel")
        label.Name = "ZNQ_Label"
        label.Parent = sg
        label.Size = UDim2.new(0, 360, 0, 48)
        label.Position = UDim2.new(0, 10, 0, 10)
        label.BackgroundTransparency = 0.25
        label.BackgroundColor3 = Color3.new(0.1, 0.1, 0.1)
        label.TextColor3 = Color3.new(1,1,1)
        label.TextStrokeTransparency = 0.3
        label.Font = Enum.Font.GothamBold
        label.TextScaled = true
        label.Text = "ZNQ • " .. tostring(LP.Name) .. " (" .. tostring(LP.UserId) .. ")"

        local frames, lastTick = 0, tick()
        RunService.RenderStepped:Connect(function(dt)
            frames += 1
            local now = tick()
            if now - lastTick >= 1 then
                local fps = math.floor(frames / (now - lastTick) + 0.5)
                frames, lastTick = 0, now
                label.Text = ("ZNQ • %s (%d)  |  FPS: %d")
                    :format(LP.Name, LP.UserId, fps)
            end
        end)

        return sg
    end)
    return ok and gui
end

if not DISABLE_UI then
    pcall(mount_gui)
end

-- ========= Marker writer =========
local has_io = (typeof(writefile) == "function") and (typeof(makefolder) == "function")
if has_io then
    pcall(function()
        if not isfolder(MARKER_DIR) then makefolder(MARKER_DIR) end
    end)

    task.spawn(function()
        while task.wait(UPDATE_INTERVAL) do
            local payload = {
                username = LP.Name,
                userId   = LP.UserId,
                placeId  = game.PlaceId,
                jobId    = game.JobId,
                ts       = os.time()
            }
            local ok, json = pcall(HttpService.JSONEncode, HttpService, payload)
            if ok then
                pcall(writefile, string.format("%s/%d.json", MARKER_DIR, LP.UserId), json)
            end
        end
    end)
end

-- ========= Hotkeys rejoin =========
pcall(function()
    local UIS = game:GetService("UserInputService")
    UIS.InputBegan:Connect(function(input, gpe)
        if gpe then return end
        if input.KeyCode == Enum.KeyCode.F8 then
            -- Rejoin game (mới)
            pcall(TeleportService.Teleport, TeleportService, game.PlaceId, LP)
        elseif input.KeyCode == Enum.KeyCode.F9 then
            -- Về đúng server hiện tại
            pcall(TeleportService.TeleportToPlaceInstance, TeleportService, game.PlaceId, game.JobId, LP)
        end
    end)
end)

-- (Optional) expose 1 hàm tiện ích:
G.ZNQ_Rejoin = function(same_server)
    if same_server then
        pcall(TeleportService.TeleportToPlaceInstance, TeleportService, game.PlaceId, game.JobId, LP)
    else
        pcall(TeleportService.Teleport, TeleportService, game.PlaceId, LP)
    end
end
