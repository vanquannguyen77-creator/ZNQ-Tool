-- ZNQ AutoExec v1.1
-- Lưu file marker trong thư mục Download/ZNQ_Markers
--  - Heartbeat:  <uid>.heartbeat
--  - State:      <uid>.state  (JSON: JOINED_OK / DISCONNECT / v.v.)
--  - Main flag:  <uid>.main   (executor đã load)
--
-- Không gửi HTTP, chỉ ghi file -> tool ngoài (Termux/1.py) đọc.
-- ------------------------------------------------------------

-- ========== Cấu hình ==========
local MARKER_DIR = "/storage/emulated/0/Download/ZNQ_Markers/"
local HEARTBEAT_INTERVAL   = 5
local FREEZE_GAP_SEC       = 12
local SOFT_REJOIN_COOLDOWN = 20
local JOINED_OK_DELAY      = 5
local CREATE_EXECUTOR_MAIN = true

-- ========== Roblox Services ==========
local Players = game:GetService("Players")
local TS      = game:GetService("TeleportService")
local Run     = game:GetService("RunService")
local Hs      = game:GetService("HttpService")
local CoreGui = game:GetService("CoreGui")

local lp = Players.LocalPlayer
local USER_ID  = tostring(lp and lp.UserId or 0)
local PLACE_ID = game.PlaceId

-- ========== File API ==========
local _isfile = isfile or function(path)
    local ok, res = pcall(readfile, path)
    return ok and type(res)=="string"
end
local _readfile = readfile or function(path)
    local ok, res = pcall(function() return readfile(path) end)
    return ok and res or nil
end
local _writefile = writefile or function(path, txt)
    warn("[ZNQ] writefile not available -> skip: "..path)
end
local _makefolder = makefolder or function(path)
    pcall(function() _writefile(path.."/.__znq_probe","x") end)
end

local function ensure_dir(path)
    if path:sub(-1) ~= "/" then path = path.."/" end
    local testf = path.."__znq_ok"
    if not _isfile(testf) then
        _makefolder(path)
        _writefile(testf,"ok")
    end
end

local function json_encode(tbl)
    local ok,res = pcall(function() return Hs:JSONEncode(tbl) end)
    return ok and res or "{}"
end

-- ========== Marker Files ==========
ensure_dir(MARKER_DIR)
local HB_FILE   = MARKER_DIR..USER_ID..".heartbeat"
local ST_FILE   = MARKER_DIR..USER_ID..".state"
local MAIN_FILE = MARKER_DIR..USER_ID..".main"

if CREATE_EXECUTOR_MAIN and not _isfile(MAIN_FILE) then
    _writefile(MAIN_FILE,"1")
end

-- ========== Heartbeat ==========
local function write_heartbeat()
    pcall(function() _writefile(HB_FILE, tostring(os.time())) end)
end
task.spawn(function()
    while task.wait(HEARTBEAT_INTERVAL) do write_heartbeat() end
end)

-- ========== Ghi state ==========
local function set_state(state, reason)
    local payload = { state=state, reason=reason or "", ts=os.time() }
    local j = json_encode(payload)
    _writefile(ST_FILE, j)
end

-- ========== Freeze detect ==========
local lastBeat = os.clock()
Run.Heartbeat:Connect(function() lastBeat = os.clock() end)
task.spawn(function()
    while task.wait(HEARTBEAT_INTERVAL) do
        if os.clock() - lastBeat > FREEZE_GAP_SEC then
            set_state("FREEZE_SUSPECT","heartbeat gap")
        end
    end
end)

-- ========== Mark JOINED_OK ==========
local function mark_joined_ok()
    task.delay(JOINED_OK_DELAY,function()
        set_state("JOINED_OK","Spawned")
    end)
end
if lp.Character then mark_joined_ok() end
lp.CharacterAdded:Connect(mark_joined_ok)

-- ========== Soft Rejoin ==========
local lastSoft = 0
local function soft_rejoin(reason)
    if os.clock() - lastSoft < SOFT_REJOIN_COOLDOWN then return end
    lastSoft = os.clock()
    set_state("SOFT_REJOIN_TRY", reason or "")
    task.spawn(function()
        local ok,err = pcall(function() TS:Teleport(PLACE_ID,lp) end)
        if not ok then set_state("DISCONNECT","TeleportFail:"..tostring(err)) end
    end)
end

-- ========== Prompt/Kick/Disconnect hook ==========
local function looks_bad(txt)
    if not txt or #txt==0 then return false end
    txt = txt:lower()
    local patterns={"disconnect","lost connection","kicked","error","teleport failed","unexpected error","reconnect"}
    for _,p in ipairs(patterns) do if txt:find(p,1,true) then return true end end
    return false
end

local function scan_gui(gui)
    for _,d in ipairs(gui:GetDescendants()) do
        if d:IsA("TextLabel") or d:IsA("TextButton") then
            local txt = d.Text or ""
            if looks_bad(txt) then soft_rejoin("Prompt:"..txt) end
            d:GetPropertyChangedSignal("Text"):Connect(function()
                if looks_bad(d.Text) then soft_rejoin("Prompt:"..d.Text) end
            end)
        end
    end
end

task.defer(function()
    for _,c in ipairs(CoreGui:GetChildren()) do scan_gui(c) end
    CoreGui.ChildAdded:Connect(scan_gui)
end)

-- ========== TeleportFail ==========
TS.TeleportInitFailed:Connect(function(_,res,msg)
    set_state("TELEPORT_FAIL",tostring(res)..":"..tostring(msg))
    soft_rejoin("TeleportInitFailed")
end)

print("[ZNQ] AutoExec loaded, user "..USER_ID.." place "..PLACE_ID)
print("[ZNQ] Markers at: "..MARKER_DIR)
