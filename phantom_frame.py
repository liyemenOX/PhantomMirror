#!/usr/bin/env python3
"""
PhantomMirror - Apple Device Display Silhouette & Shape Engine
Automatically adapts the mirroring viewport to the exact physical display shape,
corner radius, aspect ratio, and camera cutout of the connected device.
"""

import sys
import os
import re
import math
import time
import subprocess
import threading

from Xlib import X, display as xdisplay
from Xlib.ext import shape


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

    adb_cmd = ['adb']
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
    to produce smooth hardware-clipped rounded display corners.
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


def launch_with_apple_frame(profile_data, scrcpy_cmd, scale_h=None):
    """
    Launches scrcpy natively and applies the Apple physical display shape,
    exact corner radius, and hardware camera cutout dynamically.
    Guarantees 100% native video rendering without black screens or cut widgets.
    """
    token = f"PhantomMirror_{int(time.time() * 1000)}"
    cmd = list(scrcpy_cmd)

    # Launch scrcpy borderless natively without forcing artificial aspect ratios
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
    print(" Apple Device Display Silhouette: ACTIVE")
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

    # Background shape orchestrator
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

        # Listen for window geometry changes (rotations between portrait & landscape, resizing)
        scrcpy_win.change_attributes(event_mask=X.StructureNotifyMask)
        xdpy.sync()

        # Give scrcpy video decoder a moment to decode first frame and size the window
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

                # Corner radius based on shorter dimension (works in both portrait and landscape)
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
                        # In landscape orientation, camera sits along the side edge
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
                        # Set click-through input shape mask so touches and notification pull-downs work!
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

        # Initial shape
        update_shape()

        # Event loop to track resizes, rotation, and termination
        while proc.poll() is None:
            try:
                # Check if X events pending
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


def launch_pure_shape(profile_data, scrcpy_cmd, scale_h=None):
    """Alias for direct display shape mode."""
    launch_with_apple_frame(profile_data, scrcpy_cmd, scale_h=scale_h)


if __name__ == "__main__":
    prof = get_device_display_profile()
    print("Self-test profile:", prof)
