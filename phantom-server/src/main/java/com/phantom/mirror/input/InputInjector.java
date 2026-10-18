package com.phantom.mirror.input;

import java.lang.reflect.Method;

/**
 * InputInjector bridges incoming client UDP touch/mouse packets directly
 * to Android's internal InputManager service via reflection.
 * Injects MotionEvents and KeyEvents directly with async mode (0ms latency).
 */
public class InputInjector {

    public static final int ACTION_DOWN = 0;
    public static final int ACTION_UP = 1;
    public static final int ACTION_MOVE = 2;
    public static final int ACTION_CANCEL = 3;
    public static final int ACTION_SCROLL = 8;

    // Special Android Keycodes
    public static final int KEYCODE_HOME = 3;
    public static final int KEYCODE_BACK = 4;
    public static final int KEYCODE_VOLUME_UP = 24;
    public static final int KEYCODE_VOLUME_DOWN = 25;
    public static final int KEYCODE_POWER = 26;
    public static final int KEYCODE_APP_SWITCH = 187;

    private Object inputManagerInstance;
    private Method injectInputEventMethod;
    private boolean initialized = false;

    public void initialize() {
        try {
            // Access android.hardware.input.InputManager
            Class<?> inputManagerClass = Class.forName("android.hardware.input.InputManager");
            Method getInstanceMethod = inputManagerClass.getMethod("getInstance");
            inputManagerInstance = getInstanceMethod.invoke(null);

            // Locate injectInputEvent(InputEvent event, int mode)
            Class<?> inputEventClass = Class.forName("android.view.InputEvent");
            injectInputEventMethod = inputManagerClass.getMethod("injectInputEvent", inputEventClass, Integer.TYPE);
            initialized = true;
            System.out.println("[+] Successfully hooked into android.hardware.input.InputManager");

        } catch (Exception e) {
            System.err.println("[!] Notice: Operating in standalone / fallback input mode: " + e.getMessage());
        }
    }

    /**
     * Inject touch/pointer events directly into Android's window manager
     * @param action MotionEvent action code
     * @param pointerId Identifier of the touch point
     * @param normX Normalized X coordinate (0 - 65535)
     * @param normY Normalized Y coordinate (0 - 65535)
     * @param pressure Touch pressure or scroll delta
     */
    public void injectTouchEvent(int action, int pointerId, int normX, int normY, float pressure) {
        if (!initialized) {
            return;
        }

        try {
            // Map normalized coordinates (0 - 65535) to device physical screen resolution
            float screenX = (normX / 65535.0f) * 1080.0f;
            float screenY = (normY / 65535.0f) * 2400.0f;

            Class<?> motionEventClass = Class.forName("android.view.MotionEvent");
            Method obtainMethod = motionEventClass.getMethod("obtain",
                    Long.TYPE, Long.TYPE, Integer.TYPE, Float.TYPE, Float.TYPE, Float.TYPE,
                    Float.TYPE, Integer.TYPE, Float.TYPE, Float.TYPE, Integer.TYPE, Integer.TYPE);

            long now = System.currentTimeMillis();
            // Source: 0x00001002 = InputDevice.SOURCE_TOUCHSCREEN
            Object motionEvent = obtainMethod.invoke(null,
                    now, now, action, screenX, screenY, pressure, 1.0f, 0, 1.0f, 1.0f, 0, 0);

            // Mode 0 = INJECT_INPUT_EVENT_MODE_ASYNC
            injectInputEventMethod.invoke(inputManagerInstance, motionEvent, 0);

        } catch (Exception e) {
            System.err.println("[-] Touch injection error: " + e.getMessage());
        }
    }

    /**
     * Inject hardware/software key events (Home, Back, Volume, Power, Unicode)
     */
    public void injectKeyEvent(int action, int keyCode, int metaState) {
        if (!initialized) {
            return;
        }

        try {
            Class<?> keyEventClass = Class.forName("android.view.KeyEvent");
            Method obtainMethod = keyEventClass.getMethod("obtain",
                    Long.TYPE, Long.TYPE, Integer.TYPE, Integer.TYPE, Integer.TYPE, Integer.TYPE);

            long now = System.currentTimeMillis();
            Object keyEvent = obtainMethod.invoke(null, now, now, action, keyCode, 0, metaState);
            injectInputEventMethod.invoke(inputManagerInstance, keyEvent, 0);

        } catch (Exception e) {
            System.err.println("[-] Key injection error: " + e.getMessage());
        }
    }
}
