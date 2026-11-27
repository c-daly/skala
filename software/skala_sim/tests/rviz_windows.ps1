param([int]$EnableX=205, [int]$EnableY=535, [string]$Output)
$ErrorActionPreference = 'Stop'
Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class SkalaDesktop {
 public delegate bool Callback(IntPtr h, IntPtr p);
 [StructLayout(LayoutKind.Sequential)] public struct Point {public int X,Y;}
 [DllImport("user32.dll")] public static extern bool EnumWindows(Callback cb, IntPtr p);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref Point p);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint x,uint y,uint data,IntPtr extra);
 [DllImport("user32.dll")] public static extern void keybd_event(byte key,byte scan,uint flags,IntPtr extra);
 public static IntPtr Find() {
  IntPtr result=IntPtr.Zero;
  EnumWindows((h,p)=>{var b=new StringBuilder(512);GetWindowText(h,b,512);if(b.ToString().Contains(" - RViz"))result=h;return true;},IntPtr.Zero);
  return result;
 }
 public static void Click(IntPtr h,int x,int y) {
  var p=new Point{X=x,Y=y};ClientToScreen(h,ref p);SetForegroundWindow(h);SetCursorPos(p.X,p.Y);
  mouse_event(2,0,0,0,IntPtr.Zero);mouse_event(4,0,0,0,IntPtr.Zero);
 }
 public static void Key(byte key,bool down) {keybd_event(key,0,down?0u:2u,IntPtr.Zero);}
}
'@
$base='http://localhost:18765'
function Status { Invoke-RestMethod "$base/status" }
function Wait-Mode($mode) {
    foreach ($attempt in 1..50) {if ((Status).mode -eq $mode) {return}; Start-Sleep -Milliseconds 100}
    throw "Mode did not become $mode"
}
$null=[SkalaDesktop]::SetProcessDPIAware()
$window=[SkalaDesktop]::Find()
if ($window -eq [IntPtr]::Zero) {throw 'No RViz window'}
$report=@{status='failed';input='Windows desktop mouse and keyboard injection into actual RViz';checks=@{}}
try {
    [SkalaDesktop]::Click($window,$EnableX,$EnableY)
    Wait-Mode 'keyboard'
    Start-Sleep -Milliseconds 400
    $before=(Status).pose
    $report.start_pose=$before
    [SkalaDesktop]::Key(0x57,$true)
    Start-Sleep -Milliseconds 1400
    [SkalaDesktop]::Key(0x57,$false)
    Start-Sleep -Milliseconds 700
    $after=(Status).pose
    $report.end_pose=$after
    $report.mode_after_drive=(Status).mode
    $distance=[Math]::Sqrt([Math]::Pow($after.x-$before.x,2)+[Math]::Pow($after.y-$before.y,2))
    if ($distance -lt .05) {throw "Native W did not move the SLAM pose: $distance"}
    $report.checks.forward_release=@{distance_m=$distance}
    [SkalaDesktop]::Key(0x20,$true);[SkalaDesktop]::Key(0x20,$false)
    Wait-Mode 'stopped'
    $report.checks.space_stop=$true
    $report.status='passed'
} catch {
    $report.error=$_.Exception.Message
    throw
} finally {
    [SkalaDesktop]::Key(0x57,$false)
    [SkalaDesktop]::Key(0x20,$true);[SkalaDesktop]::Key(0x20,$false)
    $json=$report | ConvertTo-Json -Depth 5
    if ($Output) {[IO.File]::WriteAllText($Output,$json+[Environment]::NewLine)}
    Write-Output $json
}
