import cv2
import mediapipe as mp
import math
import pygame
import time
import numpy as np
import random
import os

# Şarkı seçme menüsü pygame ayarları
pygame.init()
screen = pygame.display.set_mode((920, 700))
pygame.display.set_caption("Equaliter - Şarkı Seç")
title_font = pygame.font.SysFont("helvetica", 50, bold=True)
font = pygame.font.SysFont("helvetica", 40)

# Dosyaları otomatik bulma
def find_music_files(directory="songs"):
    music_extensions = ['.mp3', '.wav']
    music_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(tuple(music_extensions))]
    if not music_files:
        default_songs = [
            "Meczup - Can Bonomo.mp3", "İZMİR MARŞI.mp3", "ATABARI.mp3", "ÇÖKERTME.mp3",
            "Delinin Düşü - Can Bonomo.mp3", "Güneş - Can Bonomo.mp3", "Love Me Back - Can Bonomo.mp3",
            "Rüyamda Buluttum - Can Bonomo.mp3", "SELANİK TÜRKÜSÜ.mp3", "Tastamam - Can Bonomo.mp3"
        ]
        return [os.path.join(directory, f) for f in default_songs]
    return music_files

songs = find_music_files()
selected = 0
pulse = 0  # Dümenden Animasyon

def draw_menu():
    global pulse
    pulse = (pulse + 0.1) % (2 * math.pi)
    scale = 1 + 0.05 * math.sin(pulse)

    screen.fill((20, 30, 40))
    title = title_font.render("eQUALİTER", True, (255, 255, 255))
    title = pygame.transform.scale(title, (int(title.get_width() * scale), int(title.get_height() * scale)))
    screen.blit(title, (200 - title.get_width()//2, 20))

    for i, song_path in enumerate(songs):
        song_name = os.path.basename(song_path)  # sadece dosya adı
        color = (255, 0, 0) if i == selected else (150, 150, 150)
        text = font.render(song_name, True, color)
        screen.blit(text, (50, 80 + i * 50))
    pygame.display.flip()


# Şarkı seçme menüsü
running = True
clock = pygame.time.Clock()
while running:
    clock.tick(60)
    draw_menu()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                selected = (selected - 1) % len(songs)
            elif event.key == pygame.K_DOWN:
                selected = (selected + 1) % len(songs)
            elif event.key == pygame.K_RETURN:
                running = False
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()

pygame.quit()

# Mediapip ve OpenCV
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.3, min_tracking_confidence=0.3)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Kamera yok")
    exit()

# tam ekran
cv2.namedWindow("Equaliter", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Equaliter", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Pygame mixer 
pygame.mixer.init()
try:
    pygame.mixer.music.load(songs[selected])  # artık tam dosya yolu içeriyor
    pygame.mixer.music.play()
except Exception as e:
    print(f"Sarki yuklenemedi: {e}")
    exit()


# Görselleştirme sınıfları
class AudioVisualizer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.bars = 10
        self.bar_width = width // self.bars
        self.amplitudes = np.zeros(self.bars)
        self.colors = [(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)) for _ in range(self.bars)]
    
    def update(self, volume):
        target = np.zeros(self.bars)
        if volume > 0.05:
            intensity = volume * 100
            mid = self.bars // 2
            for i in range(self.bars):
                dist_factor = 1 - (abs(i - mid) / mid)
                target[i] = intensity * dist_factor * random.uniform(0.7, 1.2)
        self.amplitudes = self.amplitudes * 0.8 + target * 0.2
    
    def draw(self, frame):
        for i in range(self.bars):
            x = i * self.bar_width
            height = int(self.amplitudes[i])
            cv2.rectangle(frame, (x, self.height - height), (x + self.bar_width, self.height), self.colors[i], -1)

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_particle(self, x, y):
        self.particles.append({
            'x': x, 'y': y,
            'vx': random.uniform(-1, 1),
            'vy': random.uniform(-3, -1),
            'size': random.randint(3, 6),
            'color': (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255)),
            'life': 0.5
        })
    
    def update(self):
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 0.1
            p['size'] *= 0.9
            if p['life'] <= 0 or p['size'] < 1:
                self.particles.remove(p)
    
    def draw(self, frame):
        for p in self.particles:
            cv2.circle(frame, (int(p['x']), int(p['y'])), int(p['size']), p['color'], -1)

# --- Yardımcı --- (gpt)
def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def is_hand_valid(hand_landmarks):
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    return (0 <= thumb_tip.x <= 1 and 0 <= thumb_tip.y <= 1 and
            0 <= index_tip.x <= 1 and 0 <= index_tip.y <= 1)

def check_pause_gesture(hand_landmarks):
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb_y = thumb_tip.y
    index_y = index_tip.y
    try:
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y
        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y
        return (abs(thumb_y - index_y) < 0.05 and
                (middle_tip > thumb_y + 0.1 or ring_tip > thumb_y + 0.1 or pinky_tip > thumb_y + 0.1))
    except:
        return abs(thumb_y - index_y) < 0.05

# Ana döngü 
visualizer = AudioVisualizer(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
particles = ParticleSystem()
paused = False
volume_smooth = 0.5
speed_smooth = 1.0
last_pos = 0
last_update_time = time.time()
pause_cooldown = time.time()
fps_list = []
wave_time = 0  # Ekolayzer dalgası

while True:
    success, img = cap.read()
    if not success:
        print("Kamera görüntüsü alınamadı!")
        break
    img = cv2.flip(img, 1)
    h, w, c = img.shape
    
    # FPS
    current_time = time.time()
    fps = 1 / (current_time - last_update_time) if current_time != last_update_time else 0
    fps_list.append(fps)
    if len(fps_list) > 30:
        fps_list.pop(0)
    avg_fps = sum(fps_list) / len(fps_list) if fps_list else 0
    
    # arka plan (koyu mavi-gri)
    bg_intensity = int(volume_smooth * 50)
    img[:] = cv2.addWeighted(img, 0.8, np.full_like(img, (20, 30, 40 + bg_intensity)), 0.2, 0)
    
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)
    
    left_hand = None
    right_hand = None
    left_valid = False
    right_valid = False
    
    if result.multi_hand_landmarks and result.multi_handedness:
        for idx, handLms in enumerate(result.multi_hand_landmarks):
            hand_label = result.multi_handedness[idx].classification[0].label
            if hand_label == 'Left' and is_hand_valid(handLms):
                left_hand = handLms
                left_valid = True
            elif hand_label == 'Right' and is_hand_valid(handLms):
                right_hand = handLms
                right_valid = True
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
    
    if left_valid:
        # Duraklatma kontrolü
        if check_pause_gesture(left_hand) and current_time - pause_cooldown > 1.0:
            paused = not paused
            if paused:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
            pause_cooldown = current_time
        
        # Hız kontrolü
        if not paused:
            l_thumb = left_hand.landmark[mp_hands.HandLandmark.THUMB_TIP]
            l_index = left_hand.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            l_x1, l_y1 = int(l_thumb.x * w), int(l_thumb.y * h)
            l_x2, l_y2 = int(l_index.x * w), int(l_index.y * h)
            left_distance = calculate_distance(l_x1, l_y1, l_x2, l_y2)
            
            target_speed = 0.5 + (left_distance / 200) * (2.0 - 0.5)
            target_speed = max(0.5, min(2.0, target_speed))
            speed_smooth = speed_smooth * 0.9 + target_speed * 0.1
            
            if current_time - last_update_time > 0.2:
                current_pos = pygame.mixer.music.get_pos()
                if current_pos == -1:
                    current_pos = 0
                new_pos = last_pos + (200 * speed_smooth)
                pygame.mixer.music.pause()
                pygame.mixer.music.play(start=new_pos / 1000.0)
                last_pos = new_pos
                last_update_time = current_time
                
                particles.add_particle(l_x1, l_y1)
                particles.add_particle(l_x2, l_y2)
            
            # Sol el çubuğu (koyu gri)
            cv2.line(img, (l_x1, l_y1), (l_x2, l_y2), (0, 0, 0), 3)
            cv2.circle(img, (l_x1, l_y1), 5, (200, 200, 200), cv2.FILLED)
            cv2.circle(img, (l_x2, l_y2), 5, (200, 200, 200), cv2.FILLED)
    
    # Ses seviyesi kontrolü ve ekolayzer çizgisi
    if left_valid and right_valid:
        l_thumb = left_hand.landmark[mp_hands.HandLandmark.THUMB_TIP]
        l_index = left_hand.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        r_thumb = right_hand.landmark[mp_hands.HandLandmark.THUMB_TIP]
        r_index = right_hand.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
        l_x1, l_y1 = int(l_thumb.x * w), int(l_thumb.y * h)
        l_x2, l_y2 = int(l_index.x * w), int(l_index.y * h)
        r_x1, r_y1 = int(r_thumb.x * w), int(r_thumb.y * h)
        r_x2, r_y2 = int(r_index.x * w), int(r_index.y * h)
        
        # Sol ve sağ el çubuklarının orta nokta
        left_center = ((l_x1 + l_x2) // 2, (l_y1 + l_y2) // 2)
        right_center = ((r_x1 + r_x2) // 2, (r_y1 + r_y2) // 2)
        hands_distance = calculate_distance(left_center[0], left_center[1], right_center[0], right_center[1])
        
        min_hd, max_hd = 50, 300
        target_volume = (hands_distance - min_hd) / (max_hd - min_hd)
        target_volume = max(0.0, min(1.0, target_volume))
        volume_smooth = volume_smooth * 0.9 + target_volume * 0.1
        
        pygame.mixer.music.set_volume(volume_smooth)
        
        # Sağ el çubuğu 
        cv2.line(img, (r_x1, r_y1), (r_x2, r_y2), (255, 255, 255), 3)
        cv2.circle(img, (r_x1, r_y1), 5, (200, 200, 200), cv2.FILLED)
        cv2.circle(img, (r_x2, r_y2), 5, (200, 200, 200), cv2.FILLED)
        
        # Ekolayzer çizgisi (beyaz)
        wave_time += 0.1
        num_points = 20
        points = []
        for i in range(num_points + 1):
            t = i / num_points
            x = int(left_center[0] + t * (right_center[0] - left_center[0]))
            y = int(left_center[1] + t * (right_center[1] - left_center[1]))
            wave_amplitude = volume_smooth * 30 * (1 + 0.5 * math.sin(wave_time + t * 2 * math.pi))
            y_offset = int(wave_amplitude * math.sin(t * 4 * math.pi + wave_time))
            points.append([x, y + y_offset])
        
        points = np.array(points, dtype=np.int32)
        
        cv2.polylines(img, [points], False, (255, 255, 255), 2)
        # Beyaz üst katman
        cv2.polylines(img, [points], False, (255, 255, 255), 1)
        
        # Dalganın tepe noktalarında parçacıklar
        if random.random() < volume_smooth:
            for i in range(0, num_points + 1, 5):  # Her 5. noktada
                particles.add_particle(points[i][0], points[i][1])
            # Sol ve sağ orta noktalar
            particles.add_particle(left_center[0], left_center[1])
            particles.add_particle(right_center[0], right_center[1])
    else:
        volume_smooth = volume_smooth * 0.9
        pygame.mixer.music.set_volume(volume_smooth)
    
    visualizer.update(volume_smooth)
    visualizer.draw(img)
    particles.update()
    particles.draw(img)
    
    # Görseller (beyaz metin, helvetica)
    cv2.putText(img, f"eQUALITEr", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, f"Hiz: {speed_smooth:.2f}x", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, f"Ses: {volume_smooth:.2f}", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, f"FPS: {int(avg_fps)}", (w-100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, "Sol El Basparmak-Isaret: Hiz ve Durdur/Baslat", (10, h-50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, "Iki El arasi mesafe: Ses Yuksekligi", (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.imshow("Equaliter - Camera", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
