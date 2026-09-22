/* GameArt AI Toolkit - 3ds Max user startup integration.
   This file is installed into the detected per-user 3ds Max startup folders.
   It creates a visible GameArt AI Toolkit menu and a small manager dialog.
   Third-party scripts are not executed automatically; the manager exposes
   installed plugin folders and safe host actions. */

global GameArtToolkitRoot = getINISetting (getDir #plugcfg + "\\GameArtToolkit.ini") "Toolkit" "Root"
if GameArtToolkitRoot == "" do
(
    GameArtToolkitRoot = getDir #userScripts
)

fn GameArtToolkitOpenFolder path =
(
    if doesFileExist path or doesDirectoryExist path then
    (
        shellLaunch "explorer.exe" path
        true
    )
    else false
)

fn GameArtToolkitShowManager =
(
    local dlg = newRolloutFloater "GameArt AI Toolkit" 430 360
    rollout r "GameArt AI Toolkit" width:410 height:320
    (
        label info "Toolkit is installed and registered for this 3ds Max user profile." align:#left
        label rootText "Root:" align:#left
        editText rootEdit "" height:28 readOnly:true
        button openRoot "Open Toolkit Folder" width:190
        button openPlugins "Open Installed Plugins" width:190
        button refresh "Refresh / Verify" width:190
        label helpText "Third-party plugins are kept isolated. Use their documented launcher or script entry point." align:#left
        on r open do rootEdit.text = GameArtToolkitRoot
        on openRoot pressed do GameArtToolkitOpenFolder GameArtToolkitRoot
        on openPlugins pressed do GameArtToolkitOpenFolder (GameArtToolkitRoot + "\\plugins")
        on refresh pressed do messageBox "Toolkit files are present. Third-party scripts are not auto-executed by startup." title:"GameArt AI Toolkit"
    )
    addRollout r dlg
)

fn GameArtToolkitInstallMenu =
(
    try (menuMan.unRegisterMenu "GameArt AI Toolkit") catch()
    local mainMenu = menuMan.getMainMenu()
    local menu = menuMan.createMenu "GameArt AI Toolkit"
    local item = menuMan.createActionItem "GameArt AI Toolkit Manager" "GameArt AI Toolkit"
    menuMan.addItem menu item -1
    menuMan.setMainMenuBar mainMenu
    menuMan.updateMenuBar()
)
try
(
    macroScript GameArtAI_Toolkit_Manager
        category:"GameArt AI Toolkit"
        tooltip:"GameArt AI Toolkit Manager"
        buttonText:"GameArt AI Toolkit"
    (
        on execute do GameArtToolkitShowManager()
    )
    GameArtToolkitInstallMenu()
)
catch
(
    format "GameArt AI Toolkit startup registration failed: %\n" (getCurrentException())
)
