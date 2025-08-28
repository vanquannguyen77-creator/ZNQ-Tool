-- ZNQ Check (AutoExecute) - v2.6-notify
-- Tác giả: ZNQ
-- Công dụng: heartbeat + thực thi lệnh join/rejoin qua ZNQ/cmd.json
-- Có thông báo trong game để dễ kiểm tra

getgenv().ZNQ_CFG = getgenv().ZNQ_CFG or {
    heartbeat_interval = 1.5,
    cmd_poll_interval  = 1.0,
    verbose_log        = false,
    notify             = true,   -- Bật/tắt notify
}

-- ===== Notify helper =====
local function notify(title, text, dur)
    if not getgenv().ZNQ_CFG.notify then return end
    pcall(function()
        game:GetService("StarterGui"):SetCore("SendNotification", {
            Title = title or "ZNQ",
            Text  = text or "",
            Duration = dur or 3
        })
    end)
end

-- ===== Executor FS wrappers =====
local has = function(x) return type(x) ~= "nil" end
local _isfile   = isfile or (has(is_file) and is_file) or function(p) return false end
local _isfolder = isfolder or (has(is_folder) and is_folder) or function(p) return false end
local _makefolder = makefolder or (has(make_folder) and make_folder) or function(p) end
local _readfile = readfile or (has(read_file) and read_file) or function(p) return nil end
local _writefile = writefile or (has(write_file) and write_file) or function(p, d) end
local _delfile  = delfile or (has(deletefile) and deletefile) or function(p) end
local _listfiles = listfiles or (has(list_files) and list_files)

local function log(...) if getgenv().ZNQ_CFG.verbose_log then print("[ZNQ]", ...) end end

-- ===== Roblox services =====
local HttpService = game:GetService("HttpService")
local TeleportService = game:GetService("TeleportService")
local Players = game:GetService("Players")
local lp = Players.LocalPlayer or Players.PlayerAdded:Wait()
local uid = tostring(lp.UserId or 0)

-- ===== Tìm thư mục ZNQ =====
local function testWritable(dir)
    local ok=false; pcall(function()
        if not _isfolder(dir) then _makefolder(dir) end
        local tf = dir.."/.znq_w"
        _writefile(tf,"ok"); ok=_isfile(tf); _delfile(tf)
    end)
    return ok
end

local function pickZNQ()
    local forced = rawget(getgenv(),"ZNQ_FORCE_ZNQ_DIR")
    if type(forced)=="string" and #forced>0 and testWritable(forced) then return forced end

    local pkgs={"com.roblox.client","com.roblox.client64"}
    local bases={"/storage/emulated/0/Android/data","/sdcard/Android/data","/data/data"}
    for _,base in ipairs(bases) do
        for _,pkg in ipairs(pkgs) do
            local d=base.."/"..pkg.."/files/ZNQ"
            if testWritable(d) then return d end
        end
    end
    return testWritable("ZNQ") and "ZNQ" or nil
end

local ZNQ_DIR = pickZNQ()
if not ZNQ_DIR then
    notify("ZNQ Check","Không tìm thấy thư mục ZNQ",6)
    return
end

notify("ZNQ Check","Đã khởi động! UID="..uid,5)
log("ZNQ_DIR=",ZNQ_DIR)

-- ===== Heartbeat =====
local hb_path = ZNQ_DIR.."/"..uid..".json"
local function writeHeartbeat()
    local payload={uid=uid,t=os.time(),placeId=game.PlaceId,jobId=game.JobId}
    local ok,data=pcall(function() return HttpService:JSONEncode(payload) end)
    if ok then pcall(function() _writefile(hb_path,data) end) end
end

-- ===== Cmd runner =====
local cmd_path = ZNQ_DIR.."/cmd.json"
local function readCmd()
    if not _isfile(cmd_path) then return nil end
    local ok,text=pcall(function() return _readfile(cmd_path) end)
    if not ok or not text or #text==0 then return nil end
    local ok2,obj=pcall(function() return HttpService:JSONDecode(text) end)
    return ok2 and obj or nil
end

local function doJoin(placeId, jobId)
    if typeof(placeId)~="number" then return end
    notify("ZNQ","Join game "..placeId,4)
    if jobId and #jobId>0 then
        TeleportService:TeleportToPlaceInstance(placeId,jobId,lp)
    else
        TeleportService:Teleport(placeId,lp)
    end
end

local function doRejoin(same)
    local pid=game.PlaceId
    if same and game.JobId and #game.JobId>0 then
        notify("ZNQ","Rejoin same server",4)
        TeleportService:TeleportToPlaceInstance(pid,game.JobId,lp)
    else
        notify("ZNQ","Rejoin place "..pid,4)
        TeleportService:Teleport(pid,lp)
    end
end

local function processCmd()
    local obj=readCmd(); if not obj then return end
    local a=(tostring(obj.action or ""):lower())
    if a=="join" then doJoin(tonumber(obj.place_id or obj.placeId),obj.job_id or obj.jobId)
    elseif a=="rejoin" then doRejoin(obj.same_server or obj.sameServer)
    else notify("ZNQ","Lệnh không hợp lệ",3) end
    pcall(function() _delfile(cmd_path) end)
end

-- ===== Loops =====
task.spawn(function()
    while task.wait(getgenv().ZNQ_CFG.heartbeat_interval) do pcall(writeHeartbeat) end
end)
task.spawn(function()
    while task.wait(getgenv().ZNQ_CFG.cmd_poll_interval) do pcall(processCmd) end
end)
