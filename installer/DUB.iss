; DUB installer. Build it with build.ps1 (produces installer\Output\DUB-Setup.exe)
#define AppName "DUB"
#define AppVersion "1.0.0"

[Setup]
AppId={{6F2B8E1C-4D3A-4C57-9B0E-DB5A1C7E2F41}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=STUKJE
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\dub.ico
UninstallDisplayIcon={app}\DUB\DUB.exe
UninstallDisplayName=DUB
WizardStyle=modern
WizardImageFile=build\wizard.bmp,build\wizard@2x.bmp
WizardSmallImageFile=build\wizard_small.bmp,build\wizard_small@2x.bmp
WizardImageBackColor=$282322
OutputDir=Output
OutputBaseFilename=DUB-Setup
Compression=lzma2/max
SolidCompression=yes
CloseApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Messages]
english.WelcomeLabel1=Welcome to DUB
english.WelcomeLabel2=DUB is a calm blob that sits in the corner of your screen. It sits at its desk while your Claudes work, bobs its head to your music, and lets you know when a Claude finishes or needs you.%n%nIt installs for your user only. No administrator rights needed.
portuguese.WelcomeLabel1=Bem-vindo ao DUB
portuguese.WelcomeLabel2=O DUB é um blob calmo que fica no canto do ecrã. Senta-se à secretaria enquanto os teus Claudes trabalham, abana a cabeça ao som da música e avisa-te quando um Claude termina ou precisa de ti.%n%nVai ser instalado só para o teu utilizador. Não precisa de administrador.

[CustomMessages]
portuguese.TaskClaude=Mostrar o consumo do Claude (5h e semanal)
portuguese.TaskClaudeHint=Liga a status line do Claude Code. Só funciona com subscrição Pro ou Max.
portuguese.TaskAutostart=Abrir o DUB quando o Windows arranca
portuguese.GroupExtras=Extras:
portuguese.ClaudeHasOther=Já tens uma status line configurada no Claude Code, por isso não lhe mexi.%nO consumo do Claude só aparece no DUB se usares a do DUB (ver o USAGE.md).
portuguese.ClaudeError=Não consegui configurar a status line do Claude Code (o settings.json não é um JSON válido?).%nO DUB funciona na mesma, mas sem o consumo do Claude.
portuguese.RunDub=Abrir o DUB agora
english.TaskClaude=Show Claude usage (5h and weekly)
english.TaskClaudeHint=Turns on the Claude Code status line. Needs a Pro or Max subscription.
english.TaskAutostart=Start DUB when Windows starts
english.GroupExtras=Extras:
english.ClaudeHasOther=You already have a Claude Code status line, so I left it alone.%nClaude usage only shows in DUB if you use DUB's one (see USAGE.md).
english.ClaudeError=Could not set up the Claude Code status line (is settings.json valid JSON?).%nDUB works anyway, just without Claude usage.
english.RunDub=Launch DUB now

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "claudeusage"; Description: "{cm:TaskClaude}"; GroupDescription: "{cm:GroupExtras}"
Name: "autostart"; Description: "{cm:TaskAutostart}"; GroupDescription: "{cm:GroupExtras}"; Flags: unchecked

[Files]
Source: "build\dist\DUB\*"; DestDir: "{app}\DUB"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "build\dist\dub-statusline\*"; DestDir: "{app}\statusline"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\USAGE.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\DUB"; Filename: "{app}\DUB\DUB.exe"; WorkingDir: "{app}\DUB"; Comment: "DUB"
Name: "{autodesktop}\DUB"; Filename: "{app}\DUB\DUB.exe"; WorkingDir: "{app}\DUB"; Comment: "DUB"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "DUB"; \
  ValueData: """{app}\DUB\DUB.exe"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\DUB\DUB.exe"; Description: "{cm:RunDub}"; WorkingDir: "{app}\DUB"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\statusline\dub-statusline.exe"; Parameters: "--uninstall"; Flags: runhidden; RunOnceId: "DubStatusline"

[Code]
procedure StopDub;
var
  code: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/f /im DUB.exe', '', SW_HIDE, ewWaitUntilTerminated, code);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  StopDub;                 // when updating, the old DUB may still be running
  Result := '';
end;

function InitializeUninstall(): Boolean;
begin
  StopDub;
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  code: Integer;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('claudeusage') then
  begin
    if Exec(ExpandConstant('{app}\statusline\dub-statusline.exe'), '--install', '', SW_HIDE,
            ewWaitUntilTerminated, code) then
    begin
      if code = 2 then
        MsgBox(CustomMessage('ClaudeHasOther'), mbInformation, MB_OK)
      else if code <> 0 then
        MsgBox(CustomMessage('ClaudeError'), mbError, MB_OK);
    end;
  end;
end;
