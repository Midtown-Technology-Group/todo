param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$installer = New-Object -ComObject WindowsInstaller.Installer
$database = $installer.GetType().InvokeMember(
    "OpenDatabase",
    "InvokeMethod",
    $null,
    $installer,
    @($Path, 0)
)
$view = $database.GetType().InvokeMember(
    "OpenView",
    "InvokeMethod",
    $null,
    $database,
    @("SELECT `Value` FROM `Property` WHERE `Property`='ProductCode'")
)
$view.GetType().InvokeMember("Execute", "InvokeMethod", $null, $view, $null) | Out-Null
$record = $view.GetType().InvokeMember("Fetch", "InvokeMethod", $null, $view, $null)
$value = $record.GetType().InvokeMember("StringData", "GetProperty", $null, $record, 1)
Write-Output $value
