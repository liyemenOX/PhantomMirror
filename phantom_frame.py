#!/usr/bin/env python3
"""
PhantomMirror - Apple Device Display Silhouette & Shape Engine
Automatically adapts the mirroring viewport to the exact physical display shape,
corner radius, aspect ratio, and camera cutout of the connected device.
Supports both Linux (X11 XShape) and Windows (Native Win32 DWM / SetWindowRgn).
"""

import sys
import os
import re
import math
import time
import shutil
import subprocess
import threading

# Conditional imports for display server backends
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    X = None
    xdisplay = None
    shape = None
else:
    try:
        from Xlib import X, display as xdisplay
        from Xlib.ext import shape
    except ImportError:
        X = None
        xdisplay = None
        shape = None


def get_adb_binary():
    """Locate adb binary across Windows and Linux."""
    if "ADB_PATH" in os.environ and os.path.isfile(os.environ["ADB_PATH"]):
        return os.environ["ADB_PATH"]
    found = shutil.which("adb")
    if found:
        return found
    if sys.platform == "win32":
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
            os.path.expandvars(r"%USERPROFILE%\scoop\shims\adb.exe"),
            r"C:\ProgramData\chocolatey\bin\adb.exe",
            r"C:\scrcpy\adb.exe",
            os.path.expandvars(r"%ProgramFiles%\Android\platform-tools\adb.exe"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
    return "adb"


def get_device_display_profile(serial=None):
    """
    Query connected device via ADB to extract physical display shape,
    corner radius, cutout specifications, and device branding.
    """
    profile = {
        'serial': serial,
        'manufacturer': 'Android',
        'model': 'Device',
        'name': 'Android Device',
        'normalized_radius': 0.12,
        'cutout': {'type': 'punch_hole', 'rel_center_x': 0.5, 'rel_top': 0.008, 'rel_w': 0.06, 'rel_h': 0.03},
    }

    adb_bin = get_adb_binary()
    adb_cmd = [adb_bin]
    if serial:
        adb_cmd.extend(['-s', serial])

    # 1. Device Branding
    try:
        mfg = subprocess.check_output(adb_cmd + ['shell', 'getprop', 'ro.product.manufacturer'], text=True, timeout=2).strip()
        model = subprocess.check_output(adb_cmd + ['shell', 'getprop', 'ro.product.model'], text=True, timeout=2).strip()
        market = subprocess.check_output(adb_cmd + ['shell', 'getprop', 'ro.product.marketname'], text=True, timeout=2).strip()

        mfg_clean = mfg.capitalize() if mfg else 'Android'
        if market:
            dev_name = market if market.lower().startswith(mfg.lower()) else f"{mfg_clean} {market}"
        elif model:
            dev_name = model if model.lower().startswith(mfg.lower()) else f"{mfg_clean} {model}"
        else:
            dev_name = f"{mfg_clean} Device"

        profile['manufacturer'] = mfg_clean
        profile['model'] = model
        profile['name'] = dev_name
    except Exception:
        pass

    # 2. Android DisplayCutout & RoundedCorners from Dumpsys
    try:
        dumpsys = subprocess.check_output(adb_cmd + ['shell', 'dumpsys', 'display'], text=True, timeout=3)

        # A. Rounded Corners Radius
        rc_m = re.search(r'roundedCorners RoundedCorners\{\[(.*?)\]\}', dumpsys)
        if rc_m:
            radii = [int(m.group(1)) for m in re.finditer(r'radius=(\d+)', rc_m.group(1))]
            if radii:
                raw_r = max(radii)
                ds_m = re.search(r'displayWidth=(\d+)', dumpsys)
                ds_w = int(ds_m.group(1)) if ds_m else 1080
                profile['normalized_radius'] = raw_r / ds_w

        # B. Display Cutout Geometry
        cutout_m = re.search(r'DisplayCutout\{insets=Rect\(.*?\)\s+waterfall=.*?\s+boundingRect=\{Bounds=\[(.*?)\]\}', dumpsys)
        if cutout_m:
            rects = re.findall(r'Rect\((\d+),\s*(\d+)\s*-\s*(\d+),\s*(\d+)\)', cutout_m.group(1))
            valid = [tuple(map(int, r)) for r in rects if int(r[2]) > int(r[0]) and int(r[3]) > int(r[1])]
            if valid:
                l, t, r, b = sorted(valid, key=lambda x: x[1])[0]
                ds_m = re.search(r'CutoutPathParserInfo\{displayWidth=(\d+)\s+displayHeight=(\d+)', dumpsys)
                ref_w = int(ds_m.group(1)) if ds_m else 1080
                ref_h = int(ds_m.group(2)) if ds_m else 2400

                cw = r - l
                ch = b - t
                rel_cx = ((l + r) / 2.0) / ref_w
                rel_w = cw / ref_w
                rel_h = ch / ref_h
                rel_t = t / ref_h

                if rel_w > 0.14:
                    cutout_type = 'dynamic_island' if rel_t > 0.004 else 'notch'
                elif abs(rel_cx - 0.5) < 0.1:
                    cutout_type = 'punch_hole'
                else:
                    cutout_type = 'corner_punch_hole'

                profile['cutout'] = {
                    'type': cutout_type,
                    'rel_center_x': rel_cx,
                    'rel_top': rel_t,
                    'rel_w': rel_w,
                    'rel_h': rel_h,
                }
    except Exception:
        pass

    if 'normalized_radius' not in profile or profile['normalized_radius'] <= 0:
        profile['normalized_radius'] = 0.125

    return profile


def get_xshape_rounded_rectangles(w, h, r):
    """
    Compute 1-pixel scanline rectangle slices for X11 SHAPE extension
    to produce smooth hardware-clipped rounded display corners on Linux.
    """
    r = max(1, min(int(r), min(w, h) // 2))
    rects = [(0, r, w, max(1, h - 2 * r))]
    for y in range(r):
        dy = r - y
        dx = int(round(r - math.sqrt(max(0, r * r - dy * dy))))
        row_w = w - 2 * dx
        if row_w > 0:
            rects.append((dx, y, row_w, 1))
            rects.append((dx, h - 1 - y, row_w, 1))
    return rects


def launch_with_apple_frame_linux(profile_data, scrcpy_cmd, scale_h=None):
    """
    Linux X11 viewport shaping and camera cutout implementation via XShape.
    """
    if xdisplay is None or shape is None:
        raise RuntimeError("python3-xlib is not available on this Linux installation")

    token = f"PhantomMirror_{int(time.time() * 1000)}"
    cmd = list(scrcpy_cmd)
    cmd.extend([
        f"--window-title={token}",
        "--window-borderless",
    ])

    if scale_h:
        cmd.append(f"--max-size={int(scale_h)}")

    r_norm = profile_data.get('normalized_radius', 0.125)
    dev_name = profile_data.get('name', 'Android Device')
    cutout = profile_data.get('cutout', {})
    cutout_type = cutout.get('type', 'punch_hole')

    print("==================================================")
    print(" Apple Device Display Silhouette: ACTIVE (Linux X11)")
    print("==================================================")
    print(f"[+] Device Canvas    : {dev_name}")
    print(f"[+] Physical Radius  : {r_norm * 100:.1f}% display curvature")
    print(f"[+] Hardware Cutout  : {cutout_type.upper()}")
    print("[*] Controls: Hold Alt + Left-Click to drag window anywhere")
    print("[*] Shortcuts: Alt+P (Power) • Alt+H (Home) • Alt+B / Right-Click (Back)")
    print("==================================================")

    env = os.environ.copy()
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":0"

    proc = subprocess.Popen(cmd, env=env)

    def shape_worker():
        xdpy = xdisplay.Display()
        root = xdpy.screen().root

        def find_win():
            for c in root.query_tree().children:
                try:
                    if c.get_wm_name() == token:
                        return c
                except Exception:
                    pass
            return None

        # Wait for scrcpy window to be mapped
        t0 = time.time()
        scrcpy_win = None
        while time.time() - t0 < 12:
            if proc.poll() is not None:
                return
            scrcpy_win = find_win()
            if scrcpy_win:
                break
            time.sleep(0.1)

        if not scrcpy_win:
            return

        scrcpy_win.change_attributes(event_mask=X.StructureNotifyMask)
        xdpy.sync()
        time.sleep(1.0)

        cam_win = None
        last_dims = (0, 0)

        def update_shape():
            nonlocal cam_win, last_dims
            try:
                geom = scrcpy_win.get_geometry()
                w, h = geom.width, geom.height
                if (w, h) == last_dims or w <= 50 or h <= 50:
                    return
                last_dims = (w, h)

                short_edge = min(w, h)
                curv_r = max(10, int(round(short_edge * r_norm)))

                # 1. Apply smooth rounded corners to scrcpy window
                rects = get_xshape_rounded_rectangles(w, h, curv_r)
                shape.rectangles(scrcpy_win, shape.SO.Set, shape.SK.Bounding, X.Unsorted, 0, 0, rects)
                xdpy.sync()

                # 2. Position camera punch hole / Dynamic Island
                if cutout_type in ('punch_hole', 'dynamic_island', 'corner_punch_hole'):
                    is_portrait = (h >= w)
                    if is_portrait:
                        pw = max(16, int(round(w * cutout.get('rel_w', 0.06))))
                        ph = max(16, int(round(h * cutout.get('rel_h', 0.03))))
                        if cutout_type == 'punch_hole':
                            ph = pw
                        px = int(round(w * cutout.get('rel_center_x', 0.5))) - (pw // 2)
                        py = max(8, int(round(h * cutout.get('rel_top', 0.008))))
                    else:
                        pw = max(16, int(round(h * cutout.get('rel_w', 0.06))))
                        ph = pw
                        px = max(8, int(round(w * cutout.get('rel_top', 0.008))))
                        py = (h - ph) // 2

                    if not cam_win:
                        cam_win = scrcpy_win.create_window(
                            px, py, pw, ph, 0,
                            geom.depth,
                            X.InputOutput,
                            X.CopyFromParent,
                            background_pixel=0
                        )
                        shape.rectangles(cam_win, shape.SO.Set, shape.SK.Input, X.Unsorted, 0, 0, [])
                        cam_win.map()
                    else:
                        cam_win.configure(x=px, y=py, width=pw, height=ph)

                    cam_r = ph // 2
                    cam_rects = get_xshape_rounded_rectangles(pw, ph, cam_r)
                    shape.rectangles(cam_win, shape.SO.Set, shape.SK.Bounding, X.Unsorted, 0, 0, cam_rects)
                    cam_win.configure(stack_mode=X.Above)
                    xdpy.sync()

            except Exception:
                pass

        update_shape()

        while proc.poll() is None:
            try:
                while xdpy.pending_events():
                    ev = xdpy.next_event()
                    if ev.type == X.ConfigureNotify:
                        update_shape()
                time.sleep(0.2)
            except Exception:
                break

    shape_thread = threading.Thread(target=shape_worker, daemon=True)
    shape_thread.start()

    try:
        proc.wait()
    except KeyboardInterrupt:
        if proc.poll() is None:
            proc.terminate()


def launch_with_apple_frame_windows(profile_data, scrcpy_cmd, scale_h=None):
    """
    Windows Native viewport shaping & camera punch-hole cutout implementation via Win32 API.
    Zero external pip dependencies (uses built-in ctypes).
    """
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    dwmapi = getattr(ctypes.windll, "dwmapi", None)

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class PAINTSTRUCT(ctypes.Structure):
        _fields_ = [
            ("hdc", wintypes.HDC),
            ("fErase", wintypes.BOOL),
            ("rcPaint", RECT),
            ("fRestore", wintypes.BOOL),
            ("fIncUpdate", wintypes.BOOL),
            ("rgbReserved", wintypes.BYTE * 32),
        ]

    class WNDCLASSEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("style", wintypes.UINT),
            ("lpfnWndProc", ctypes.c_void_p),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HCURSOR),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
            ("hIconSm", wintypes.HICON),
        ]

    token = f"PhantomMirror_{int(time.time() * 1000)}"
    cmd = list(scrcpy_cmd)
    cmd.extend([
        f"--window-title={token}",
        "--window-borderless",
    ])

    if scale_h:
        cmd.append(f"--max-size={int(scale_h)}")

    r_norm = profile_data.get('normalized_radius', 0.125)
    dev_name = profile_data.get('name', 'Android Device')
    cutout = profile_data.get('cutout', {})
    cutout_type = cutout.get('type', 'punch_hole')

    print("==================================================")
    print(" Apple Device Display Silhouette: ACTIVE (Windows Win32)")
    print("==================================================")
    print(f"[+] Device Canvas    : {dev_name}")
    print(f"[+] Physical Radius  : {r_norm * 100:.1f}% display curvature")
    print(f"[+] Hardware Cutout  : {cutout_type.upper()}")
    print("[*] Shortcuts: Alt+P (Power) • Alt+H (Home) • Alt+B / Right-Click (Back)")
    print("==================================================")

    proc = subprocess.Popen(cmd)

    def shape_worker_win32():
        # Wait for scrcpy window to appear
        t0 = time.time()
        scrcpy_hwnd = None
        while time.time() - t0 < 12:
            if proc.poll() is not None:
                return
            hwnd = user32.FindWindowW(None, token)
            if hwnd and user32.IsWindowVisible(hwnd):
                scrcpy_hwnd = hwnd
                break
            time.sleep(0.1)

        if not scrcpy_hwnd:
            return

        # Give scrcpy video decoder a brief moment to size the window
        time.sleep(0.8)

        # Register overlay window class for transparent click-through camera cutout
        overlay_class = f"PhantomCutout_{int(time.time() * 1000)}"
        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

        def overlay_proc(hwnd, msg, wparam, lparam):
            if msg == 0x000F:  # WM_PAINT
                ps = PAINTSTRUCT()
                hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
                black_brush = gdi32.GetStockObject(4)  # BLACK_BRUSH
                user32.FillRect(hdc, ctypes.byref(ps.rcPaint), black_brush)
                user32.EndPaint(hwnd, ctypes.byref(ps))
                return 0
            elif msg == 0x0084:  # WM_NCHITTEST -> HTTRANSPARENT (-1) for true click-through
                return -1
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        wndproc_cb = WNDPROC(overlay_proc)
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = 0x0002 | 0x0001  # CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc = ctypes.cast(wndproc_cb, ctypes.c_void_p)
        wc.hInstance = user32.GetWindowLongW(scrcpy_hwnd, -6)  # GWL_HINSTANCE
        wc.hbrBackground = gdi32.GetStockObject(4)  # BLACK_BRUSH
        wc.lpszClassName = overlay_class

        user32.RegisterClassExW(ctypes.byref(wc))

        # Create overlay window: WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        WS_EX_TOPMOST = 0x00000008
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_LAYERED = 0x00080000
        WS_EX_NOACTIVATE = 0x08000000
        WS_POPUP = 0x80000000
        WS_VISIBLE = 0x10000000

        cam_hwnd = user32.CreateWindowExW(
            WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_LAYERED | WS_EX_NOACTIVATE,
            overlay_class,
            "PhantomCutout",
            WS_POPUP | WS_VISIBLE,
            0, 0, 10, 10,
            0, 0, wc.hInstance, 0
        )

        last_rect = (0, 0, 0, 0)

        while proc.poll() is None:
            try:
                rect = RECT()
                if not user32.GetWindowRect(scrcpy_hwnd, ctypes.byref(rect)):
                    break

                w = rect.right - rect.left
                h = rect.bottom - rect.top
                current_rect = (rect.left, rect.top, w, h)

                if w > 50 and h > 50 and current_rect != last_rect:
                    last_rect = current_rect
                    short_edge = min(w, h)
                    curv_r = max(10, int(round(short_edge * r_norm)))

                    # 1. Apply smooth rounded corners to the scrcpy window via SetWindowRgn
                    hrgn = gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, curv_r * 2, curv_r * 2)
                    user32.SetWindowRgn(scrcpy_hwnd, hrgn, True)

                    # Also set Windows 11 DWM rounded corner preference if supported
                    if dwmapi:
                        try:
                            DWMWA_WINDOW_CORNER_PREFERENCE = 33
                            DWMWCP_ROUND = 2
                            dwmapi.DwmSetWindowAttribute(
                                scrcpy_hwnd,
                                DWMWA_WINDOW_CORNER_PREFERENCE,
                                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
                                4
                            )
                        except Exception:
                            pass

                    # 2. Position camera punch hole cutout overlay
                    if cam_hwnd and cutout_type in ('punch_hole', 'dynamic_island', 'corner_punch_hole'):
                        is_portrait = (h >= w)
                        if is_portrait:
                            pw = max(16, int(round(w * cutout.get('rel_w', 0.06))))
                            ph = max(16, int(round(h * cutout.get('rel_h', 0.03))))
                            if cutout_type == 'punch_hole':
                                ph = pw
                            px = int(round(w * cutout.get('rel_center_x', 0.5))) - (pw // 2)
                            py = max(8, int(round(h * cutout.get('rel_top', 0.008))))
                        else:
                            pw = max(16, int(round(h * cutout.get('rel_w', 0.06))))
                            ph = pw
                            px = max(8, int(round(w * cutout.get('rel_top', 0.008))))
                            py = (h - ph) // 2

                        cam_r = ph // 2
                        cam_hrgn = gdi32.CreateRoundRectRgn(0, 0, pw + 1, ph + 1, cam_r * 2, cam_r * 2)
                        user32.SetWindowRgn(cam_hwnd, cam_hrgn, True)

                        # Set overlay position directly over scrcpy window
                        # SWP_NOACTIVATE = 0x0010, SWP_SHOWWINDOW = 0x0040
                        user32.SetWindowPos(
                            cam_hwnd,
                            scrcpy_hwnd,
                            rect.left + px,
                            rect.top + py,
                            pw,
                            ph,
                            0x0010 | 0x0040
                        )

                # Track minimize / restore state
                if cam_hwnd:
                    if user32.IsIconic(scrcpy_hwnd) or not user32.IsWindowVisible(scrcpy_hwnd):
                        user32.ShowWindow(cam_hwnd, 0)  # SW_HIDE
                    else:
                        user32.ShowWindow(cam_hwnd, 4)  # SW_SHOWNOACTIVATE

                # Message pump for overlay
                msg = wintypes.MSG()
                while user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))

                time.sleep(0.1)

            except Exception:
                time.sleep(0.2)

        if cam_hwnd:
            user32.DestroyWindow(cam_hwnd)

    shape_thread = threading.Thread(target=shape_worker_win32, daemon=True)
    shape_thread.start()

    try:
        proc.wait()
    except KeyboardInterrupt:
        if proc.poll() is None:
            proc.terminate()


def launch_with_apple_frame(profile_data, scrcpy_cmd, scale_h=None):
    """
    Cross-platform dispatcher for Apple Device Display Silhouette.
    Automatically chooses native Win32 DWM engine on Windows or X11 XShape on Linux.
    """
    if sys.platform == "win32":
        launch_with_apple_frame_windows(profile_data, scrcpy_cmd, scale_h=scale_h)
    else:
        launch_with_apple_frame_linux(profile_data, scrcpy_cmd, scale_h=scale_h)


def launch_pure_shape(profile_data, scrcpy_cmd, scale_h=None):
    """Alias for direct display shape mode."""
    launch_with_apple_frame(profile_data, scrcpy_cmd, scale_h=scale_h)


if __name__ == "__main__":
    prof = get_device_display_profile()
    print("Self-test profile:", prof)
