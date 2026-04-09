[Setup]
; 基础信息配置
AppId={{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}}
AppName=Pywidget
AppVersion=1.0.0
AppPublisher=CCLEENDWW

; 安装路径配置 (autopf 指代 Program Files 或 Program Files (x86))
DefaultDirName={autopf}\Pywidget

; 开始菜单文件夹名称
DefaultGroupName=Pywidget

; 编译输出配置
OutputDir=.\Output
OutputBaseFilename=Pywidget_Setup_v1.0.0

; 压缩算法 (lzma2 压缩率极高)
Compression=lzma2/ultra64
SolidCompression=yes

; 权限要求 (admin 确保写入 Program Files 不会报错)
PrivilegesRequired=admin

; 卸载程序配置
UninstallDisplayIcon={app}\widget.exe

[Files]
; 核心：将 widget.dist 目录下的所有文件递归打包
; 注意：Source 路径必须指向你的 nuitka 产物真实路径
Source: "widget.dist\widget.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "widget.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 创建开始菜单快捷方式
Name: "{group}\Pywidget"; Filename: "{app}\widget.exe"
; 创建开始菜单卸载快捷方式
Name: "{group}\卸载 Pywidget"; Filename: "{uninstallexe}"
; 创建桌面快捷方式
Name: "{autodesktop}\Pywidget"; Filename: "{app}\widget.exe"

[Run]
; 安装完成后提供运行选项
Filename: "{app}\widget.exe"; Description: "运行 Pywidget"; Flags: nowait postinstall skipifsilent