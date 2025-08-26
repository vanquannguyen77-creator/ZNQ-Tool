-- ZNQ Check Script – with command watcher
-- Vẫn dùng getgenv().disable_ui = true/false như trước
-- Thêm cơ chế đọc lệnh từ ZNQ/cmd.json trong workspace để Teleport (bỏ deep-link)

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TeleportService = game:GetService("TeleportService")
local HttpService = game:GetService("HttpService")
local UIS = game:GetService("UserInputService")

local LP = Players.LocalPlayer; while not LP do task.wait() LP = Players.LocalPlayer end
local G = getgenv and getgenv() or _G
local CFG = (G.ZNQ_CFG and type(G.ZNQ_CFG)=="table") and G.ZNQ_CFG or {}
local DISABLE_UI = (G.disable_ui == true)
local MARKER_DIR = tostring(CFG.marker_dir or "ZNQ")
local UPDATE_INTERVAL = tonumber(CFG.update_interval or 2); if UPDATE_INTERVAL < 1 then UPDATE_INTERVAL = 1 end

-- ===== UI gọn (như trước) =====
local function mount_gui()
    local ok, gui = pcall(function()
        local sg = Instance.new("ScreenGui")
        sg.Name = "ZNQ_UI"; sg.ResetOnSpawn = false
        local parent = (gethui and gethui()) or game:FindFirstChildOfClass("CoreGui")
        if not parent then parent = LP:FindFirstChildOfClass("PlayerGui") or LP:WaitForChild("PlayerGui") end
        if syn and syn.protect_gui then pcall(syn.protect_gui, sg) end
        local old = parent:FindFirstChild("ZNQ_UI"); if old and old~=sg then pcall(function() old:Destroy() end) end
        sg.Parent = parent

        local label = Instance.new("TextLabel")
        label.Name="ZNQ_Label"; label.Parent=sg
        label.Size=UDim2.new(0,360,0,48); label.Position=UDim2.new(0,10,0,10)
        label.BackgroundTransparency=0.25; label.BackgroundColor3=Color3.new(0.1,0.1,0.1)
        label.TextColor3=Color3.new(1,1,1); label.TextStrokeTransparency=0.3
        label.Font=Enum.Font.GothamBold; label.TextScaled=true
        label.Text=("ZNQ • %s (%d)"):format(LP.Name, LP.UserId)

        local frames, last = 0, tick()
        RunService.RenderStepped:Connect(function()
            frames += 1
            local now = tick()
            if now-last >= 1 then
                local fps = math.floor(frames/(now-last)+0.5)
                frames, last = 0, now
                label.Text = ("ZNQ • %s (%d)  |  FPS: %d"):format(LP.Name, LP.UserId, fps)
            end
        end)
        return sg
    end)
    return ok and gui
end
if not DISABLE_UI then pcall(mount_gui) end

-- ===== Marker writer như trước =====
local function safe_isfile(p) return (typeof(isfile)=="function" and isfile(p)) end
local function safe_read(p)
    local ok, data = pcall(function() return readfile(p) end)
    return ok and data or nil
end
local function safe_write(p, data)
    if typeof(makefolder)=="function" then
        local dir = p:match("^(.*)/[^/]+$"); if dir then pcall(makefolder, dir) end
    end
    pcall(writefile, p, data)
end
local function safe_delfile(p) pcall(function() if safe_isfile(p) then delfile(p) end end) end

task.spawn(function()
    while task.wait(UPDATE_INTERVAL) do
        local payload = {
            username = LP.Name, userId = LP.UserId,
            placeId = game.PlaceId, jobId = game.JobId, ts = os.time()
        }
        local ok, json = pcall(HttpService.JSONEncode, HttpService, payload)
        if ok then safe_write(("%s/%d.json"):format(MARKER_DIR, LP.UserId), json) end
    end
end)

-- ===== Hotkeys cũ =====
pcall(function()
    UIS.InputBegan:Connect(function(input, gpe)
        if gpe then return end
        if input.KeyCode == Enum.KeyCode.F8 then
            pcall(TeleportService.Teleport, TeleportService, game.PlaceId, LP)
        elseif input.KeyCode == Enum.KeyCode.F9 then
            pcall(TeleportService.TeleportToPlaceInstance, TeleportService, game.PlaceId, game.JobId, LP)
        end
    end)
end)

-- ===== Command watcher (mới) =====
task.spawn(function()
    local CMD = MARKER_DIR.."/cmd.json"
    while task.wait(0.8) do
        local s = safe_read(CMD)
        if s and #s > 0 then
            local ok, obj = pcall(HttpService.JSONDecode, HttpService, s)
            if ok and type(obj)=="table" and obj.action=="rejoin" then
                local same = obj.same_server == true
                local pid  = tonumber(obj.placeId) or game.PlaceId
                local jid  = tostring(obj.jobId or "") ~= "" and tostring(obj.jobId) or game.JobId
                if same and jid then
                    pcall(TeleportService.TeleportToPlaceInstance, TeleportService, pid, jid, LP)
                else
                    pcall(TeleportService.Teleport, TeleportService, pid, LP)
                end
            end
            safe_delfile(CMD) -- tránh lặp
        end
    end
end)

-- (API) cho phép tool gọi nếu muốn
getgenv().ZNQ_Rejoin = function(same_server, placeId, jobId)
    local same = same_server == true
    local pid  = tonumber(placeId) or game.PlaceId
    local jid  = tostring(jobId or "") ~= "" and tostring(jobId) or game.JobId
    if same and jid then
        pcall(TeleportService.TeleportToPlaceInstance, TeleportService, pid, jid, LP)
    else
        pcall(TeleportService.Teleport, TeleportService, pid, LP)
    end
end
