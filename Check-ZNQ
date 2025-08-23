local ZdqFiPHaYrt = game:GetService("HttpService")
local SGJvTXuLkNA = game:GetService("Players").LocalPlayer
local EoBVWnUPxyC = http_request or request or (syn and syn.request)
if not EoBVWnUPxyC then return end

if not getgenv().disable_ui then
	local rA1pB7eKz6Q = game:GetService("RunService")
	local dP2xV4lMn3J = game:GetService("Players")
	local bT9sN8oFw0L = dP2xV4lMn3J.LocalPlayer

	local kX6eRq2Zd7M = Instance.new("TextLabel", Instance.new("ScreenGui", game.CoreGui))
	kX6eRq2Zd7M.Size = UDim2.new(0, 300, 0, 50)
	kX6eRq2Zd7M.Position = UDim2.new(0, 10, 0, 10)
	kX6eRq2Zd7M.Font = Enum.Font.FredokaOne
	kX6eRq2Zd7M.TextScaled = true
	kX6eRq2Zd7M.BackgroundTransparency = 1
	kX6eRq2Zd7M.TextStrokeTransparency = 0
	kX6eRq2Zd7M.Text = "Nexus Hideout"

	local yM5wKv3Dp1C, xL8qTa9Gf4E, hS0zBr7Wx2U = 0, tick(), 0
	rA1pB7eKz6Q.RenderStepped:Connect(function(oH3vN1cLj8Y)
		hS0zBr7Wx2U = (hS0zBr7Wx2U + oH3vN1cLj8Y * 0.5) % 1
		kX6eRq2Zd7M.TextColor3 = Color3.fromHSV(hS0zBr7Wx2U, 1, 1)
		yM5wKv3Dp1C += 1
		local gQ4nUf6Ey0S = tick()
		if gQ4nUf6Ey0S - xL8qTa9Gf4E >= 1 then
			kX6eRq2Zd7M.Text = ("%s, FPS: %d"):format(bT9sN8oFw0L.Name, yM5wKv3Dp1C / (gQ4nUf6Ey0S - xL8qTa9Gf4E))
			yM5wKv3Dp1C, xL8qTa9Gf4E = 0, gQ4nUf6Ey0S
		end
	end)
end

local LGiDpqakOXv
do
	local GRgksoCmzYH, KeJPhVXMQnf = pcall(function()
		return EoBVWnUPxyC({
			Url = "https://users.roblox.com/v1/usernames/users",
			Method = "POST",
			Headers = {
				["Content-Type"] = "application/json"
			},
			Body = ZdqFiPHaYrt:JSONEncode({
				usernames = { SGJvTXuLkNA.Name },
				excludeBannedUsers = true
			})
		})
	end)

	if not GRgksoCmzYH or not KeJPhVXMQnf or not KeJPhVXMQnf.Success or not KeJPhVXMQnf.Body then return end

	local BXpZbkmYvFc, SqRgNjCvKML = pcall(ZdqFiPHaYrt.JSONDecode, ZdqFiPHaYrt, KeJPhVXMQnf.Body)
	if not BXpZbkmYvFc or typeof(SqRgNjCvKML) ~= "table" or typeof(SqRgNjCvKML.data) ~= "table" then return end

	local sGfdAKTwpxL = SqRgNjCvKML.data[1]
	if not sGfdAKTwpxL or typeof(sGfdAKTwpxL) ~= "table" or typeof(sGfdAKTwpxL.id) ~= "number" then return end

	LGiDpqakOXv = sGfdAKTwpxL.id
end

task.spawn(function()
	local yvQJhACntPo = tostring(LGiDpqakOXv) .. ".main"
	while true do
		pcall(function()
			if isfile(yvQJhACntPo) then
				delfile(yvQJhACntPo)
			end
			writefile(yvQJhACntPo, "https://discord.gg/FcEGmkNDDe")
		end)
		task.wait(1)
	end
end)
