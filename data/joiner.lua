(function()
    repeat wait() until game:IsLoaded()

    local WebSocketURL = "ws://127.0.0.1:51948"

    local Players = game:GetService("Players")
    local CoreGui = game:GetService("CoreGui")
    local UserInputService = game:GetService("UserInputService")

    -- anti-kick / thanks to fractal hub for bypass
    hookfunction(isfunctionhooked, function(func) if func == tick then return false end end)
    local origTick = getfenv()["tick"]
    getfenv()["tick"] = function() return math.huge end
    hookfunction(tick, function() return math.huge end)

    -- lagger bypass (thanks to fractal hub)
    for _, player in pairs(Players:GetPlayers()) do
        player.CharacterAdded:Connect(function()
            player:ClearCharacterAppearance()
        end)

        if player.Character then player:ClearCharacterAppearance() end
    end
    Players.PlayerAdded:Connect(function(player)
        if player.Character then player:ClearCharacterAppearance() end
        player.CharacterAdded:Connect(function()
            player:ClearCharacterAppearance()
        end)
    end)

    -- Variables
    local joinerActive = false
    local ws = nil
    local settingsOpen = false

    -- Create Main GUI
    local ScreenGui = Instance.new("ScreenGui")
    ScreenGui.Name = "DexterVetterUI"
    ScreenGui.ResetOnSpawn = false
    ScreenGui.Parent = CoreGui

    -- Start Joiner Button
    local StartJoinerBtn = Instance.new("TextButton")
    StartJoinerBtn.Size = UDim2.new(0, 120, 0, 40)
    StartJoinerBtn.Position = UDim2.new(0, 20, 0, 20)
    StartJoinerBtn.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
    StartJoinerBtn.Text = "Start Joiner"
    StartJoinerBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
    StartJoinerBtn.TextSize = 14
    StartJoinerBtn.Font = Enum.Font.GothamBold
    StartJoinerBtn.BorderSizePixel = 0
    StartJoinerBtn.Parent = ScreenGui

    local StartCorner = Instance.new("UICorner")
    StartCorner.CornerRadius = UDim.new(0, 8)
    StartCorner.Parent = StartJoinerBtn

    -- Open Vetter Button
    local OpenVetterBtn = Instance.new("TextButton")
    OpenVetterBtn.Size = UDim2.new(0, 120, 0, 40)
    OpenVetterBtn.Position = UDim2.new(0, 150, 0, 20)
    OpenVetterBtn.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
    OpenVetterBtn.Text = "Open Vetter"
    OpenVetterBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
    OpenVetterBtn.TextSize = 14
    OpenVetterBtn.Font = Enum.Font.GothamBold
    OpenVetterBtn.BorderSizePixel = 0
    OpenVetterBtn.Parent = ScreenGui

    local OpenCorner = Instance.new("UICorner")
    OpenCorner.CornerRadius = UDim.new(0, 8)
    OpenCorner.Parent = OpenVetterBtn

    -- Settings Panel (Vertical, Draggable)
    local SettingsFrame = Instance.new("Frame")
    SettingsFrame.Size = UDim2.new(0, 250, 0, 400)
    SettingsFrame.Position = UDim2.new(0.5, -125, 0.5, -200)
    SettingsFrame.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
    SettingsFrame.BorderSizePixel = 0
    SettingsFrame.Visible = false
    SettingsFrame.Parent = ScreenGui

    local SettingsCorner = Instance.new("UICorner")
    SettingsCorner.CornerRadius = UDim.new(0, 12)
    SettingsCorner.Parent = SettingsFrame

    -- Settings Header (for dragging)
    local SettingsHeader = Instance.new("Frame")
    SettingsHeader.Size = UDim2.new(1, 0, 0, 50)
    SettingsHeader.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
    SettingsHeader.BorderSizePixel = 0
    SettingsHeader.Parent = SettingsFrame

    local HeaderCorner = Instance.new("UICorner")
    HeaderCorner.CornerRadius = UDim.new(0, 12)
    HeaderCorner.Parent = SettingsHeader

    local HeaderTitle = Instance.new("TextLabel")
    HeaderTitle.Size = UDim2.new(1, -50, 1, 0)
    HeaderTitle.Position = UDim2.new(0, 10, 0, 0)
    HeaderTitle.BackgroundTransparency = 1
    HeaderTitle.Text = "Dexter Vetter"
    HeaderTitle.TextColor3 = Color3.fromRGB(255, 255, 255)
    HeaderTitle.TextSize = 18
    HeaderTitle.Font = Enum.Font.GothamBold
    HeaderTitle.TextXAlignment = Enum.TextXAlignment.Left
    HeaderTitle.Parent = SettingsHeader

    -- Close Button
    local CloseBtn = Instance.new("TextButton")
    CloseBtn.Size = UDim2.new(0, 40, 0, 40)
    CloseBtn.Position = UDim2.new(1, -45, 0, 5)
    CloseBtn.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
    CloseBtn.Text = "X"
    CloseBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
    CloseBtn.TextSize = 16
    CloseBtn.Font = Enum.Font.GothamBold
    CloseBtn.BorderSizePixel = 0
    CloseBtn.Parent = SettingsHeader

    local CloseCorner = Instance.new("UICorner")
    CloseCorner.CornerRadius = UDim.new(0, 8)
    CloseCorner.Parent = CloseBtn

    -- Settings Content
    local SettingsContent = Instance.new("Frame")
    SettingsContent.Size = UDim2.new(1, -20, 1, -70)
    SettingsContent.Position = UDim2.new(0, 10, 0, 60)
    SettingsContent.BackgroundTransparency = 1
    SettingsContent.Parent = SettingsFrame

    -- Toggle Switch Frame
    local ToggleFrame = Instance.new("Frame")
    ToggleFrame.Size = UDim2.new(1, 0, 0, 60)
    ToggleFrame.Position = UDim2.new(0, 0, 0, 20)
    ToggleFrame.BackgroundTransparency = 1
    ToggleFrame.Parent = SettingsContent

    local ToggleLabel = Instance.new("TextLabel")
    ToggleLabel.Size = UDim2.new(0.6, 0, 1, 0)
    ToggleLabel.BackgroundTransparency = 1
    ToggleLabel.Text = "Auto Join"
    ToggleLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
    ToggleLabel.TextSize = 16
    ToggleLabel.Font = Enum.Font.Gotham
    ToggleLabel.TextXAlignment = Enum.TextXAlignment.Left
    ToggleLabel.Parent = ToggleFrame

    -- iOS Style Toggle Switch
    local ToggleBackground = Instance.new("Frame")
    ToggleBackground.Size = UDim2.new(0, 50, 0, 30)
    ToggleBackground.Position = UDim2.new(1, -50, 0.5, -15)
    ToggleBackground.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
    ToggleBackground.BorderSizePixel = 0
    ToggleBackground.Parent = ToggleFrame

    local ToggleBgCorner = Instance.new("UICorner")
    ToggleBgCorner.CornerRadius = UDim.new(1, 0)
    ToggleBgCorner.Parent = ToggleBackground

    local ToggleCircle = Instance.new("Frame")
    ToggleCircle.Size = UDim2.new(0, 26, 0, 26)
    ToggleCircle.Position = UDim2.new(0, 2, 0, 2)
    ToggleCircle.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
    ToggleCircle.BorderSizePixel = 0
    ToggleCircle.Parent = ToggleBackground

    local ToggleCircleCorner = Instance.new("UICorner")
    ToggleCircleCorner.CornerRadius = UDim.new(1, 0)
    ToggleCircleCorner.Parent = ToggleCircle

    local ToggleButton = Instance.new("TextButton")
    ToggleButton.Size = UDim2.new(1, 0, 1, 0)
    ToggleButton.BackgroundTransparency = 1
    ToggleButton.Text = ""
    ToggleButton.Parent = ToggleBackground

    -- Dragging functionality
    local dragging = false
    local dragInput, dragStart, startPos

    local function update(input)
        local delta = input.Position - dragStart
        SettingsFrame.Position = UDim2.new(startPos.X.Scale, startPos.X.Offset + delta.X, startPos.Y.Scale, startPos.Y.Offset + delta.Y)
    end

    SettingsHeader.InputBegan:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
            dragging = true
            dragStart = input.Position
            startPos = SettingsFrame.Position

            input.Changed:Connect(function()
                if input.UserInputState == Enum.UserInputState.End then
                    dragging = false
                end
            end)
        end
    end)

    SettingsHeader.InputChanged:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseMovement or input.UserInputType == Enum.UserInputType.Touch then
            dragInput = input
        end
    end)

    UserInputService.InputChanged:Connect(function(input)
        if input == dragInput and dragging then
            update(input)
        end
    end)


    local function prints(str)
        print("[AutoJoiner]: " .. str)
    end

    local function updateToggle()
        if joinerActive then
            ToggleBackground.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
            ToggleCircle:TweenPosition(UDim2.new(0, 22, 0, 2), "Out", "Quad", 0.2, true)
        else
            ToggleBackground.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
            ToggleCircle:TweenPosition(UDim2.new(0, 2, 0, 2), "Out", "Quad", 0.2, true)
        end
    end

    local function findTargetGui()
        local coreGui = game:GetService("CoreGui")

        for _, gui in ipairs(coreGui:GetChildren()) do
            if gui:IsA("ScreenGui") then
                local mainFrame = gui:FindFirstChild("MainFrame")
                if mainFrame and mainFrame:FindFirstChild("ContentContainer") then
                    local contentContainer = mainFrame.ContentContainer
                    local tabServer = contentContainer:FindFirstChild("TabContent_Server")
                    if tabServer then
                        return tabServer
                    end
                end
            end
        end
        return nil
    end

    local function setJobIDText(targetGui, text)
        if not targetGui then return end

        local inputFrame = targetGui:FindFirstChild("Input")
        local textBox = inputFrame:FindFirstChildOfClass("TextBox")

        textBox.Text = text
        firesignal(textBox.FocusLost)

        prints('Textbox updated: ' .. text .. ' (10m+ bypass)')
        return origTick()
    end

    local function clickJoinButton(targetGui)
        for _, buttonFrame in ipairs(targetGui:GetChildren()) do
            if buttonFrame:IsA("Frame") and buttonFrame.Name == "Button" then
                local textLabel = buttonFrame:FindFirstChildOfClass("TextLabel")
                local imageButton = buttonFrame:FindFirstChildOfClass("ImageButton")

                if textLabel and imageButton and textLabel.Text == "Join Job-ID" then
                    return imageButton
                end
            end
        end
        return nil
    end

    local function bypass10M(jobId)
        if not joinerActive then return end
        
        task.defer(function()
            local targetGui = findTargetGui()
            local start = setJobIDText(targetGui, jobId)
            local button = clickJoinButton(targetGui)

            getconnections(button.MouseButton1Click)[1]:Fire()
            prints(string.format("Join server clicked (10m+ bypass) | maybe real delay: %.5fs", origTick() - start))
        end)
    end

    local function justJoin(script)
        if not joinerActive then return end
        
        local func, err = loadstring(script)
        if func then
            local ok, result = pcall(func)
            if not ok then
                prints("Error while executing script: " .. result)
            end
        else
            prints("Some unexcepted error: " .. err)
        end
    end

    local function connect()
        while true do
            prints("Trying to connect to " .. WebSocketURL)
            local success, socket = pcall(WebSocket.connect, WebSocketURL)

            if success and socket then
                prints("Connected to WebSocket")
                ws = socket

                ws.OnMessage:Connect(function(msg)
                    if joinerActive then
                        if not string.find(msg, "TeleportService") then
                            prints("Bypassing 10m server: " .. msg)
                            bypass10M(msg)
                        else
                            prints("Running the script: " .. msg)
                            justJoin(msg)
                        end
                    end
                end)

                local closed = false
                ws.OnClose:Connect(function()
                    if not closed then
                        closed = true
                        prints("The websocket closed, trying to reconnect...")
                        wait(1)
                        connect()
                    end
                end)

                break
            else
                prints("Unable to connect to websocket, trying again..")
                wait(1)
            end
        end
    end

    -- Start Joiner Button Click
    StartJoinerBtn.MouseButton1Click:Connect(function()
        joinerActive = not joinerActive
        
        if joinerActive then
            StartJoinerBtn.BackgroundColor3 = Color3.fromRGB(0, 217, 143)
            StartJoinerBtn.Text = "Joining..."
            prints("Joiner activated!")
        else
            StartJoinerBtn.BackgroundColor3 = Color3.fromRGB(244, 67, 54)
            StartJoinerBtn.Text = "Stopped"
            prints("Joiner stopped!")
            
            wait(2)
            if not joinerActive then
                StartJoinerBtn.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
                StartJoinerBtn.Text = "Start Joiner"
            end
        end
        
        updateToggle()
    end)

    -- Open Vetter Button Click
    OpenVetterBtn.MouseButton1Click:Connect(function()
        settingsOpen = not settingsOpen
        SettingsFrame.Visible = settingsOpen
    end)

    -- Close Button Click
    CloseBtn.MouseButton1Click:Connect(function()
        settingsOpen = false
        SettingsFrame.Visible = false
    end)

    -- Toggle Button Click
    ToggleButton.MouseButton1Click:Connect(function()
        joinerActive = not joinerActive
        updateToggle()
        
        if joinerActive then
            StartJoinerBtn.BackgroundColor3 = Color3.fromRGB(0, 217, 143)
            StartJoinerBtn.Text = "Joining..."
            prints("Joiner activated!")
        else
            StartJoinerBtn.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
            StartJoinerBtn.Text = "Start Joiner"
            prints("Joiner stopped!")
        end
    end)

    connect()
end)()