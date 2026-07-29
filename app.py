print("Starting app...")
try:
    import cv2
except ImportError as import_error:
    error_text = str(import_error)
    if "libGL.so.1" in error_text:
        print("[ERROR] OpenCV dependency missing: libGL.so.1")
        print("[FIX] On Debian/Ubuntu run:")
        print("      sudo apt-get update && sudo apt-get install -y libgl1 libglib2.0-0")
        print("[NOTE] For Streamlit Cloud, use streamlit_app.py as the main file.")
        raise SystemExit(1)
    raise
import mediapipe as mp
import numpy as np
import math
import time
import platform
from types import SimpleNamespace

try:
    from pynput.keyboard import Key, Controller
    _keyboard_init_error = None
except Exception as keyboard_import_error:
    _keyboard_init_error = keyboard_import_error

    class Controller:
        def press(self, _key):
            return None

        def release(self, _key):
            return None

    Key = SimpleNamespace(left="left", right="right", up="up", down="down")

DEFAULT_CAMERA_INDEX       = 0
STEERING_DEADZONE_DEGREES  = 12
STEERING_RELEASE_DEGREES   = 6
MAX_STEERING_ANGLE         = 25
FLIP_CAMERA                = True
SHOW_ANGLE                 = True
MIN_DETECTION_CONF         = 0.7
MIN_TRACKING_CONF          = 0.5
HAND_TRACKING_GRACE_FRAMES = 8
OPEN_HAND_FINGER_THRESHOLD = 3

BACKGROUND_COLOR      = (26, 15, 11)   # #0B0F1A
PRIMARY_COLOR         = (255, 217, 0)  # #00D9FF
ACCELERATION_COLOR    = (136, 255, 0)  # #00FF88
BRAKE_COLOR           = (48, 59, 255)  # #FF3B30
WARNING_COLOR         = (0, 165, 255)  # #FFA500
TEXT_COLOR            = (255, 255, 255) # #FFFFFF
MUTED_COLOR           = (195, 183, 176) # #B0B7C3
GLASS_COLOR           = (30, 20, 20)
NEUTRAL_COLOR         = (100, 100, 100)

keyboard   = Controller()
mp_hands   = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def open_camera(camera_index):
    system_name = platform.system().lower()
    backend_candidates = []

    if system_name == "windows":
        backend_candidates = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    elif system_name == "darwin":
        backend_candidates = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
    else:
        backend_candidates = [cv2.CAP_V4L2, cv2.CAP_ANY]

    for backend in backend_candidates:
        capture = cv2.VideoCapture(camera_index, backend)
        if capture.isOpened():
            return capture
        capture.release()

    return None


def is_hand_open(hand_landmarks):
    FINGER_TIPS = [8, 12, 16, 20]
    FINGER_PIPS = [6, 10, 14, 18]
    extended_fingers_count = sum(
        1 for tip, pip in zip(FINGER_TIPS, FINGER_PIPS)
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y
    )
    return extended_fingers_count >= OPEN_HAND_FINGER_THRESHOLD


class VirtualSteeringController:
    def __init__(self):
        self.keys_held              = {Key.left: False, Key.right: False, Key.up: False, Key.down: False}
        self.steering_angle_history = []
        self.HISTORY_LENGTH         = 1

    def _press(self, key):
        if not self.keys_held[key]:
            keyboard.press(key)
            self.keys_held[key] = True

    def _release(self, key):
        if self.keys_held[key]:
            keyboard.release(key)
            self.keys_held[key] = False

    def release_all(self):
        for key in list(self.keys_held.keys()):
            try:
                keyboard.release(key)
            except Exception:
                pass
            self.keys_held[key] = False
        self.steering_angle_history.clear()

    def smooth_angle(self, raw_angle):
        self.steering_angle_history.append(raw_angle)
        if len(self.steering_angle_history) > self.HISTORY_LENGTH:
            self.steering_angle_history.pop(0)
        return float(np.mean(self.steering_angle_history))

    def update_steer(self, left_wrist, right_wrist):
        dx = right_wrist[0] - left_wrist[0]
        dy = right_wrist[1] - left_wrist[1]

        raw_steering_angle_radians = math.atan2(dy, dx)
        raw_steering_angle_degrees = math.degrees(raw_steering_angle_radians)
        steering_angle = self.smooth_angle(raw_steering_angle_degrees)

        steering_direction = "STRAIGHT"
        if steering_angle < -STEERING_DEADZONE_DEGREES:
            steering_direction = "LEFT"
        elif steering_angle > STEERING_DEADZONE_DEGREES:
            steering_direction = "RIGHT"
        elif self.keys_held[Key.left] and steering_angle > -STEERING_RELEASE_DEGREES:
            steering_direction = "STRAIGHT"
        elif self.keys_held[Key.right] and steering_angle < STEERING_RELEASE_DEGREES:
            steering_direction = "STRAIGHT"

        steering_strength = 0.0
        if steering_direction == "LEFT":
            steering_strength = min(1.0, (abs(steering_angle) - STEERING_DEADZONE_DEGREES) / (MAX_STEERING_ANGLE - STEERING_DEADZONE_DEGREES))
            self._press(Key.left)
            self._release(Key.right)
        elif steering_direction == "RIGHT":
            steering_strength = min(1.0, (abs(steering_angle) - STEERING_DEADZONE_DEGREES) / (MAX_STEERING_ANGLE - STEERING_DEADZONE_DEGREES))
            self._press(Key.right)
            self._release(Key.left)
        else:
            self._release(Key.left)
            self._release(Key.right)

        return steering_angle, steering_direction, steering_strength

    def update_throttle(self, is_left_hand_open, is_right_hand_open):
        are_both_hands_open   = is_left_hand_open and is_right_hand_open
        are_both_hands_closed = (not is_left_hand_open) and (not is_right_hand_open)

        if are_both_hands_closed:
            self._press(Key.up)
            self._release(Key.down)
            return "ACCEL"
        elif are_both_hands_open:
            self._press(Key.down)
            self._release(Key.up)
            return "BRAKE"
        else:
            self._release(Key.up)
            self._release(Key.down)
            return "NEUTRAL"


def render_steering_wheel(camera_frame, center, angle_deg, steering_direction, steering_strength):
    center_x, center_y = center
    radius = 70
    
    # Outer thick rim
    cv2.circle(camera_frame, (center_x, center_y), radius, (40, 40, 40), 12)
    cv2.circle(camera_frame, (center_x, center_y), radius, PRIMARY_COLOR, 2)
    
    # Inner ring
    cv2.circle(camera_frame, (center_x, center_y), radius - 15, (50, 50, 50), 2)
    
    # 3 Spokes
    angles = [90, 210, 330]
    for current_angle in angles:
        radians_angle = math.radians(current_angle + angle_deg)
        x1 = int(center_x + (radius - 15) * math.cos(radians_angle))
        y1 = int(center_y + (radius - 15) * math.sin(radians_angle))
        x2 = int(center_x + 15 * math.cos(radians_angle))
        y2 = int(center_y + 15 * math.sin(radians_angle))
        cv2.line(camera_frame, (x1, y1), (x2, y2), (80, 80, 80), 8)
        cv2.line(camera_frame, (x1, y1), (x2, y2), PRIMARY_COLOR, 1)

    # Center hub
    cv2.circle(camera_frame, (center_x, center_y), 15, (30, 30, 30), -1)
    cv2.circle(camera_frame, (center_x, center_y), 15, PRIMARY_COLOR, 1)
    
    # Small center circle
    cv2.circle(camera_frame, (center_x, center_y), 5, PRIMARY_COLOR, -1)


def render_dashboard(camera_frame, dashboard_state, steering_angle, steering_direction, steering_strength, throttle_state, are_both_hands_visible, is_left_hand_open, is_right_hand_open, current_fps):
    frame_height, frame_width = camera_frame.shape[:2]

    # Glass panel bottom 25%
    dashboard_height = int(frame_height * 0.25)
    dashboard_y_position = frame_height - dashboard_height
    
    transparent_overlay = camera_frame.copy()
    cv2.rectangle(transparent_overlay, (0, dashboard_y_position), (frame_width, frame_height), GLASS_COLOR, -1)
    cv2.addWeighted(transparent_overlay, 0.7, camera_frame, 0.3, 0, camera_frame)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # ---------------- TOP STATUS BAR ----------------
    cv2.rectangle(camera_frame, (0, 0), (frame_width, 25), GLASS_COLOR, -1)
    cv2.putText(camera_frame, f"FPS: {current_fps:.0f}", (10, 17), font, 0.4, PRIMARY_COLOR, 1)
    
    camera_status_color = ACCELERATION_COLOR
    cv2.putText(camera_frame, "Camera", (100, 17), font, 0.4, TEXT_COLOR, 1)
    cv2.circle(camera_frame, (160, 13), 4, camera_status_color, -1)
    
    tracking_status_color = ACCELERATION_COLOR if are_both_hands_visible else BRAKE_COLOR
    cv2.putText(camera_frame, "Tracking", (200, 17), font, 0.4, TEXT_COLOR, 1)
    cv2.circle(camera_frame, (270, 13), 4, tracking_status_color, -1)
    
    controller_status_color = ACCELERATION_COLOR
    cv2.putText(camera_frame, "Controller", (310, 17), font, 0.4, TEXT_COLOR, 1)
    cv2.circle(camera_frame, (390, 13), 4, controller_status_color, -1)

    # ---------------- BOTTOM PANELS ----------------
    panel_width = frame_width // 3
    
    # --- LEFT PANEL: Speedometer ---
    speedometer_center_x = panel_width // 2
    speedometer_center_y = dashboard_y_position + dashboard_height // 2 - 10
    speedometer_radius = dashboard_height // 2 - 5
    
    # Draw ticks
    for tick_value in range(0, 221, 10):
        tick_angle = 150 + (tick_value / 220.0) * 240
        tick_radians = math.radians(tick_angle)
        inner_radius = speedometer_radius - (10 if tick_value % 20 == 0 else 5)
        tick_x1 = int(speedometer_center_x + inner_radius * math.cos(tick_radians))
        tick_y1 = int(speedometer_center_y + inner_radius * math.sin(tick_radians))
        tick_x2 = int(speedometer_center_x + speedometer_radius * math.cos(tick_radians))
        tick_y2 = int(speedometer_center_y + speedometer_radius * math.sin(tick_radians))
        tick_color = PRIMARY_COLOR if tick_value % 20 == 0 else MUTED_COLOR
        cv2.line(camera_frame, (tick_x1, tick_y1), (tick_x2, tick_y2), tick_color, 1 if tick_value % 20 != 0 else 2)
        if tick_value % 40 == 0:
            text_x = int(speedometer_center_x + (speedometer_radius - 22) * math.cos(tick_radians))
            text_y = int(speedometer_center_y + (speedometer_radius - 22) * math.sin(tick_radians))
            cv2.putText(camera_frame, str(tick_value), (text_x - 10, text_y + 5), font, 0.3, TEXT_COLOR, 1)
            
    # Draw needle
    simulated_speed = dashboard_state['simulated_speed']
    needle_angle = 150 + (simulated_speed / 220.0) * 240
    needle_radians = math.radians(needle_angle)
    needle_x = int(speedometer_center_x + (speedometer_radius - 5) * math.cos(needle_radians))
    needle_y = int(speedometer_center_y + (speedometer_radius - 5) * math.sin(needle_radians))
    cv2.line(camera_frame, (speedometer_center_x, speedometer_center_y), (needle_x, needle_y), BRAKE_COLOR, 2)
    cv2.circle(camera_frame, (speedometer_center_x, speedometer_center_y), 4, PRIMARY_COLOR, -1)
    
    # Speed text
    cv2.putText(camera_frame, f"{int(simulated_speed)} km/h", (speedometer_center_x - 30, speedometer_center_y + speedometer_radius + 15), font, 0.5, PRIMARY_COLOR, 1)
    
    # --- CENTER PANEL: Steering Wheel ---
    steering_wheel_center_x = panel_width + panel_width // 2
    steering_wheel_center_y = dashboard_y_position + dashboard_height // 2 - 15
    render_steering_wheel(camera_frame, (steering_wheel_center_x, steering_wheel_center_y), dashboard_state['steering_animation_angle'], steering_direction, steering_strength)
    
    # Angle text
    cv2.putText(camera_frame, "STEERING", (steering_wheel_center_x - 30, steering_wheel_center_y + 40), font, 0.3, MUTED_COLOR, 1)
    cv2.putText(camera_frame, steering_direction, (steering_wheel_center_x - 25, steering_wheel_center_y + 55), font, 0.4, PRIMARY_COLOR, 1)
    cv2.putText(camera_frame, f"ANGLE {int(steering_angle)} deg", (steering_wheel_center_x - 45, steering_wheel_center_y + 70), font, 0.4, TEXT_COLOR, 1)
    
    # --- RIGHT PANEL: Throttle & Brake ---
    throttle_panel_start_x = panel_width * 2 + 20
    throttle_panel_start_y = dashboard_y_position + 20
    
    cv2.putText(camera_frame, "ACCEL", (throttle_panel_start_x, throttle_panel_start_y), font, 0.4, MUTED_COLOR, 1)
    accel_blocks = int(dashboard_state['acceleration_animation'] * 10)
    progress_bar_height = 10
    for block_index in range(10):
        block_x = throttle_panel_start_x + 50 + block_index * 12
        block_y = throttle_panel_start_y - 8
        block_color = ACCELERATION_COLOR if block_index < accel_blocks else (50, 50, 50)
        cv2.rectangle(camera_frame, (block_x, block_y), (block_x + 10, block_y + progress_bar_height), block_color, -1)
        
    cv2.putText(camera_frame, "BRAKE", (throttle_panel_start_x, throttle_panel_start_y + 25), font, 0.4, MUTED_COLOR, 1)
    brake_blocks = int(dashboard_state['brake_animation'] * 10)
    for block_index in range(10):
        block_x = throttle_panel_start_x + 50 + block_index * 12
        block_y = throttle_panel_start_y + 17
        block_color = BRAKE_COLOR if block_index < brake_blocks else (50, 50, 50)
        cv2.rectangle(camera_frame, (block_x, block_y), (block_x + 10, block_y + progress_bar_height), block_color, -1)
        
    mode_color = ACCELERATION_COLOR if throttle_state == "ACCEL" else (BRAKE_COLOR if throttle_state == "BRAKE" else PRIMARY_COLOR)
    cv2.putText(camera_frame, throttle_state, (throttle_panel_start_x, throttle_panel_start_y + 50), font, 0.5, mode_color, 1)
    
    left_hand_display_state = "Open" if is_left_hand_open else "Closed"
    right_hand_display_state = "Open" if is_right_hand_open else "Closed"
    left_hand_color = TEXT_COLOR if is_left_hand_open else PRIMARY_COLOR
    right_hand_color = TEXT_COLOR if is_right_hand_open else PRIMARY_COLOR
    cv2.putText(camera_frame, f"L: {left_hand_display_state}", (throttle_panel_start_x + 90, throttle_panel_start_y + 45), font, 0.4, left_hand_color, 1)
    cv2.putText(camera_frame, f"R: {right_hand_display_state}", (throttle_panel_start_x + 90, throttle_panel_start_y + 60), font, 0.4, right_hand_color, 1)
    
    # --- STEERING INDICATOR ---
    indicator_y_position = dashboard_y_position - 15
    indicator_center_x = frame_width // 2
    indicator_width = 200
    cv2.line(camera_frame, (indicator_center_x - indicator_width//2, indicator_y_position), (indicator_center_x + indicator_width//2, indicator_y_position), (80, 80, 80), 2)
    cv2.putText(camera_frame, "LEFT", (indicator_center_x - indicator_width//2 - 35, indicator_y_position + 4), font, 0.4, MUTED_COLOR, 1)
    cv2.putText(camera_frame, "RIGHT", (indicator_center_x + indicator_width//2 + 5, indicator_y_position + 4), font, 0.4, MUTED_COLOR, 1)
    
    indicator_px = indicator_center_x + int(dashboard_state['steering_indicator_position'] * (indicator_width//2))
    cv2.circle(camera_frame, (indicator_px, indicator_y_position), 5, PRIMARY_COLOR, -1)
    cv2.circle(camera_frame, (indicator_px, indicator_y_position), 8, PRIMARY_COLOR, 1)


def render_hand_connection(camera_frame, left_wrist, right_wrist):
    left_x, left_y = left_wrist
    right_x, right_y = right_wrist
    
    transparent_overlay = camera_frame.copy()
    cv2.line(transparent_overlay, (left_x, left_y), (right_x, right_y), PRIMARY_COLOR, 6)
    cv2.circle(transparent_overlay, (left_x, left_y), 15, PRIMARY_COLOR, -1)
    cv2.circle(transparent_overlay, (right_x, right_y), 15, PRIMARY_COLOR, -1)
    cv2.addWeighted(transparent_overlay, 0.4, camera_frame, 0.6, 0, camera_frame)
    
    cv2.line(camera_frame, (left_x, left_y), (right_x, right_y), PRIMARY_COLOR, 1)
    cv2.circle(camera_frame, (left_x, left_y), 10, TEXT_COLOR, -1)
    cv2.circle(camera_frame, (right_x, right_y), 10, TEXT_COLOR, -1)
    cv2.circle(camera_frame, (left_x, left_y), 15, PRIMARY_COLOR, 2)
    cv2.circle(camera_frame, (right_x, right_y), 15, PRIMARY_COLOR, 2)


def main():
    if _keyboard_init_error is not None:
        print("[WARN] pynput keyboard backend unavailable; key presses are disabled.")
        print(f"       Reason: {_keyboard_init_error}")

    video_capture = open_camera(DEFAULT_CAMERA_INDEX)
    if video_capture is None:
        print("[ERROR] Cannot open camera.")
        print("  -> Check webcam permissions and close apps using the camera.")
        print("  -> Linux: ensure your user can access /dev/video*.")
        print("  -> macOS: System Settings > Privacy & Security > Camera.")
        print("  -> Windows: Settings > Privacy > Camera.")
        return

    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    video_capture.set(cv2.CAP_PROP_FPS, 60)
    video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    steering_controller = VirtualSteeringController()

    hand_detector = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        model_complexity=0,
        min_detection_confidence=MIN_DETECTION_CONF,
        min_tracking_confidence=MIN_TRACKING_CONF,
    )

    hand_connection_style = mp_drawing.DrawingSpec(color=PRIMARY_COLOR, thickness=1)
    hand_landmark_style   = mp_drawing.DrawingSpec(color=TEXT_COLOR, thickness=1, circle_radius=3)

    prev_time          = time.time()
    steering_angle     = 0.0
    steering_direction = "STRAIGHT"
    steering_strength  = 0.0
    throttle_state     = "NEUTRAL"
    is_left_hand_open  = False
    is_right_hand_open = False
    lost_frames        = 0

    dashboard_state = {
        'simulated_speed': 0.0,
        'steering_animation_angle': 0.0,
        'acceleration_animation': 0.0,
        'brake_animation': 0.0,
        'steering_indicator_position': 0.0
    }

    print("=" * 55)
    print("  Virtual Steering Wheel  |  Press Q to quit")
    print("=" * 55)
    print("  FIST  = Accelerate (UP)    OPEN = Brake (DOWN)")
    print("  Tilt hands LEFT/RIGHT to steer — works in any mode")
    print("=" * 55)

    try:
        while True:
            frame_read_success, camera_frame = video_capture.read()
            if not frame_read_success or camera_frame is None:
                time.sleep(0.01)
                continue

            if FLIP_CAMERA:
                camera_frame = cv2.flip(camera_frame, 1)

            frame_height, frame_width = camera_frame.shape[:2]

            rgb_camera_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
            rgb_camera_frame.flags.writeable = False
            hand_detection_results = hand_detector.process(rgb_camera_frame)
            rgb_camera_frame.flags.writeable = True

            are_both_hands_visible = False

            if hand_detection_results.multi_hand_landmarks and hand_detection_results.multi_handedness:
                detected_hands = {}

                for hand_landmarks, handedness in zip(hand_detection_results.multi_hand_landmarks, hand_detection_results.multi_handedness):
                    label = handedness.classification[0].label

                    mp_drawing.draw_landmarks(camera_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS, hand_landmark_style, hand_connection_style)

                    wrist = hand_landmarks.landmark[0]
                    wrist_pixel_x = int(wrist.x * frame_width)
                    wrist_pixel_y = int(wrist.y * frame_height)
                    is_opened = is_hand_open(hand_landmarks)
                    detected_hands[label] = (wrist.x, wrist.y, wrist_pixel_x, wrist_pixel_y, is_opened)

                if "Left" in detected_hands and "Right" in detected_hands:
                    are_both_hands_visible = True
                    lost_frames  = 0

                    left_wrist_normalized_x, left_wrist_normalized_y, left_wrist_pixel_x, left_wrist_pixel_y, is_left_hand_open  = detected_hands["Left"]
                    right_wrist_normalized_x, right_wrist_normalized_y, right_wrist_pixel_x, right_wrist_pixel_y, is_right_hand_open = detected_hands["Right"]

                    render_hand_connection(camera_frame, (left_wrist_pixel_x, left_wrist_pixel_y), (right_wrist_pixel_x, right_wrist_pixel_y))
                    steering_angle, steering_direction, steering_strength = steering_controller.update_steer((left_wrist_normalized_x, left_wrist_normalized_y), (right_wrist_normalized_x, right_wrist_normalized_y))
                    throttle_state = steering_controller.update_throttle(is_left_hand_open, is_right_hand_open)
                else:
                    lost_frames += 1
                    if lost_frames >= HAND_TRACKING_GRACE_FRAMES:
                        steering_controller.release_all()
                        steering_angle, steering_direction, steering_strength = 0.0, "STRAIGHT", 0.0
                        throttle_state = "NEUTRAL"
                        is_left_hand_open = is_right_hand_open = False
            else:
                lost_frames += 1
                if lost_frames >= HAND_TRACKING_GRACE_FRAMES:
                    steering_controller.release_all()
                    steering_angle, steering_direction, steering_strength = 0.0, "STRAIGHT", 0.0
                    throttle_state = "NEUTRAL"
                    is_left_hand_open = is_right_hand_open = False

            now               = time.time()
            delta_time        = max(now - prev_time, 1e-6)
            current_fps       = 1.0 / delta_time
            prev_time         = now

            target_acceleration = 1.0 if throttle_state == "ACCEL" else 0.0
            target_brake_force  = 1.0 if throttle_state == "BRAKE" else 0.0
            
            # Speed logic
            if throttle_state == "ACCEL":
                dashboard_state['simulated_speed'] += 1.5 * (delta_time * 60)
            elif throttle_state == "BRAKE":
                dashboard_state['simulated_speed'] -= 3.0 * (delta_time * 60)
            else:
                dashboard_state['simulated_speed'] *= 0.98 ** (delta_time * 60)
            dashboard_state['simulated_speed'] = max(0, min(220, dashboard_state['simulated_speed']))
            
            # Smooth interpolation
            interpolation_factor = 1.0 - (0.8 ** (delta_time * 60))
            dashboard_state['steering_animation_angle'] += (steering_angle - dashboard_state['steering_animation_angle']) * interpolation_factor
            dashboard_state['acceleration_animation'] += (target_acceleration - dashboard_state['acceleration_animation']) * interpolation_factor
            dashboard_state['brake_animation'] += (target_brake_force - dashboard_state['brake_animation']) * interpolation_factor
            
            target_steer = 0.0
            if steering_direction == "LEFT":
                target_steer = -steering_strength
            elif steering_direction == "RIGHT":
                target_steer = steering_strength
            dashboard_state['steering_indicator_position'] += (target_steer - dashboard_state['steering_indicator_position']) * interpolation_factor

            render_dashboard(camera_frame, dashboard_state, steering_angle, steering_direction, steering_strength, throttle_state, are_both_hands_visible, is_left_hand_open, is_right_hand_open, current_fps)
            cv2.imshow("Virtual Steering Wheel", camera_frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q'), 27):
                break

    finally:
        steering_controller.release_all()
        hand_detector.close()
        video_capture.release()
        cv2.destroyAllWindows()
        print("\n[INFO] Stopped. All keys released.")


if __name__ == "__main__":
    print("Calling main()")
    main()