[Setup]
AppName=QR & Barcode Printer
AppVersion=1.0
AppVerName=QR & Barcode Printer 1.0
AppPublisher=Danny Pham
AppPublisherURL=https://github.com/dannyphamv/nicegui-printer
AppCopyright=Copyright (C) 2026 Danny Pham
PrivilegesRequired=lowest
CloseApplications=yes
CloseApplicationsFilter=QRBarcodePrinter.exe
RestartApplications=yes
LicenseFile=LICENSE.txt
AppId={{9d6adc9e-3bd5-4b19-82de-877d3115f9c5}}
AppComments=A Windows application using NiceGUI for printing QR & Code128 barcodes to any connected printer.

; Install paths
DefaultDirName={autopf}\QR & Barcode Printer
DefaultGroupName=QR & Barcode Printer
DisableProgramGroupPage=yes

; Output
OutputDir=installer_output
OutputBaseFilename=QR & Barcode Printer Setup
SetupIconFile=favicon.ico

; Compression
Compression=lzma
SolidCompression=yes

; Minimum Windows version (Windows 10)
MinVersion=10.0

; Uninstall
UninstallDisplayIcon={app}\QRBarcodePrinter.exe
UninstallDisplayName=QR & Barcode Printer

; Prevents multiple instances of the installer running
AppMutex=QRBarcodePrinterSetupMutex

; Version info shown in installer EXE properties
VersionInfoVersion=1.0
VersionInfoCompany=Danny Pham
VersionInfoDescription=QR & Barcode Printer Installer
VersionInfoProductName=QR & Barcode Printer
VersionInfoProductVersion=1.0

; 64-bit install
ArchitecturesInstallIn64BitMode=x64compatible

; Modern wizard UI
WizardStyle=dynamic

[Code]
function InitializeSetup(): Boolean;
begin
  if not IsWin64 then
  begin
    MsgBox('QR & Barcode Printer requires a 64-bit version of Windows.', mbError, MB_OK);
    Result := False;
  end else
    Result := True;
end;

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"
Name: "startupicon"; Description: "Start automatically with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "QRBarcodePrinter"; ValueData: """{app}\QRBarcodePrinter.exe"""; Tasks: startupicon; Flags: uninsdeletevalue

[Files]
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\QR & Barcode Printer"; Filename: "{app}\QRBarcodePrinter.exe"
Name: "{group}\Uninstall QR & Barcode Printer"; Filename: "{uninstallexe}"
Name: "{userdesktop}\QR & Barcode Printer"; Filename: "{app}\QRBarcodePrinter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\QRBarcodePrinter.exe"; Description: "Launch QR & Barcode Printer"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\cache"
Type: filesandordirs; Name: "{userappdata}\QR & Barcode Printer"