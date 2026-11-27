param([switch]$Probe)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class SkalaXInput {
  [StructLayout(LayoutKind.Sequential)] public struct Pad {
    public ushort Buttons;
    public byte LeftTrigger, RightTrigger;
    public short LX, LY, RX, RY;
  }
  [StructLayout(LayoutKind.Sequential)] public struct State {
    public uint Packet;
    public Pad Gamepad;
  }
  [DllImport("xinput1_4.dll", EntryPoint="XInputGetState")]
  public static extern uint GetState(uint index, out State state);
}
'@
if ($Probe) {
    $found = @()
    foreach ($index in 0..3) {
        $state = New-Object SkalaXInput+State
        if ([SkalaXInput]::GetState($index, [ref]$state) -eq 0) { $found += $index }
    }
    @{ xinput_loaded = $true; connected_indices = $found; physical_controller_tested = $false } | ConvertTo-Json
    exit 0
}
Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [TimeSpan]::FromSeconds(1)
$base = 'http://localhost:18765'
$html = $client.GetStringAsync($base).GetAwaiter().GetResult()
if ($html -notmatch 'name="skala-token" content="([^"]+)"') { throw 'Simulation control service is unavailable' }
$client.DefaultRequestHeaders.Add('X-Skala-Token', $Matches[1])
$identity = [Guid]::NewGuid().ToString()
$script:sequence = 0
function Send-Control($mode, [double]$linear = 0, [double]$angular = 0) {
    $script:sequence++
    $data = @{client=$identity; sequence=$script:sequence; linear=$linear; angular=$angular}
    if ($mode) { $data.mode = $mode }
    $body = New-Object System.Net.Http.StringContent(($data | ConvertTo-Json -Compress), [Text.Encoding]::UTF8, 'application/json')
    try {
        $response = $client.PostAsync("$base/control", $body).GetAwaiter().GetResult()
        try { $null = $response.EnsureSuccessStatusCode() } finally { $response.Dispose() }
    } finally { $body.Dispose() }
}
function Axis([short]$value) {
    $v = [Math]::Max(-1, $value / 32767.0)
    if ([Math]::Abs($v) -lt 0.15) { return 0.0 }
    return [Math]::Sign($v) * ([Math]::Abs($v)-0.15)/0.85
}
$active = $false
$lastHold = $false
Write-Host 'Skala simulation controller. Keep the RViz map visible.'
Write-Host 'Xbox/XInput: hold LB + left stick. Release LB to stop. B disables. Ctrl+C exits.'
Write-Host 'After B/Space stop, release and press LB again to resume. Waiting for a controller...'
try {
    while ($true) {
        $connected = $false
        foreach ($index in 0..3) {
            $state = New-Object SkalaXInput+State
            if ([SkalaXInput]::GetState($index, [ref]$state) -eq 0) { $connected = $true; break }
        }
        if (!$connected) {
            if ($active) { Send-Control 'stopped'; Write-Host 'Controller disconnected; stopped.' }
            $active = $false; $lastHold = $false
            Start-Sleep -Milliseconds 100
            continue
        }
        $hold = ($state.Gamepad.Buttons -band 0x100) -ne 0
        $stop = ($state.Gamepad.Buttons -band 0x2000) -ne 0
        if ($stop) {
            if ($active) { Send-Control 'stopped'; Write-Host 'Stopped. Release LB, then hold it to resume.' }
            $active = $false
        } elseif ($hold -and !$lastHold) {
            Send-Control 'manual'; $active = $true
            Write-Host 'Controller active.'
        }
        if ($active) {
            $linear = 0.0; $angular = 0.0
            if ($hold) { $linear = (Axis $state.Gamepad.LY)*.15; $angular = -(Axis $state.Gamepad.LX)*.6 }
            Send-Control $null $linear $angular
        }
        $lastHold = $hold
        Start-Sleep -Milliseconds 50
    }
} finally {
    try { Send-Control 'stopped' } catch { Write-Warning 'Connection unavailable; the simulation command timeout stops motion.' }
    $client.Dispose()
}
