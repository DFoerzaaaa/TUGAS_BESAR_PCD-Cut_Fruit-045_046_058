import cv2
import pygame
import mediapipe as mp
import random
import pymunk
import time
import math
import sys

# Setup
pygame.init()
width, height = 1280, 720
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Permainan Tangkap Buah")
clock = pygame.time.Clock()

cap = cv2.VideoCapture(0)
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

space = pymunk.Space()
space.gravity = (0, 900)

# Load gambar
buah_imgs = [pygame.image.load("semangka.png"), pygame.image.load("apel.png")]
bom_img = pygame.image.load("bom.png")
keranjang_img = pygame.image.load("keranjang.png")

# Scaling ukuran
for i in range(len(buah_imgs)):
    buah_imgs[i] = pygame.transform.scale(buah_imgs[i], (130, 130))
bom_img = pygame.transform.scale(bom_img, (120, 120))
keranjang_img = pygame.transform.scale(keranjang_img, (500, 400))

# Font & warna
font = pygame.font.SysFont(None, 60)
big_font = pygame.font.SysFont(None, 120)
black = (0, 0, 0)

# Variabel game
skor = 0
nyawa = 3
durasi = 60
start_time = time.time()
game_over = False
buah_list = []
next_spawn_time = 0

class Objek:
    def __init__(self, is_bom=False):
        self.image = bom_img if is_bom else random.choice(buah_imgs)
        mass = 1
        radius = 75
        inertia = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, inertia)
        self.body.position = random.randint(100, width - 100), 0
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.6
        self.is_bom = is_bom
        space.add(self.body, self.shape)

    def draw(self, surface):
        x, y = self.body.position
        img_rect = self.image.get_rect(center=(int(x), int(y)))
        surface.blit(self.image, img_rect)

running = True
while running:
    screen.fill((255, 255, 255))
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    if h > w:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    frame = cv2.resize(frame, (width, height))

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hasil = pose.process(rgb)

    tangan_kanan = tangan_kiri = None
    keranjang_pos = None

    if hasil.pose_landmarks:
        h_img, w_img, _ = frame.shape
        tangan_kanan = (
            int(hasil.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].x * w_img),
            int(hasil.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].y * h_img)
        )
        tangan_kiri = (
            int(hasil.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].x * w_img),
            int(hasil.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].y * h_img)
        )

        if tangan_kanan and tangan_kiri:
            jarak = math.hypot(tangan_kanan[0] - tangan_kiri[0], tangan_kanan[1] - tangan_kiri[1])
            if jarak < 100:
                keranjang_pos = ((tangan_kanan[0] + tangan_kiri[0]) // 2, (tangan_kanan[1] + tangan_kiri[1]) // 2)

    # Tampilkan kamera di layar pygame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = pygame.surfarray.make_surface(frame)
    frame = pygame.transform.rotate(frame, -90)
    frame = pygame.transform.flip(frame, True, False)
    screen.blit(frame, (0, 0))

    if not game_over:
        if time.time() > next_spawn_time:
            is_bom = random.random() < 0.2
            buah_list.append(Objek(is_bom))
            next_spawn_time = time.time() + 1.5

        for obj in buah_list[:]:
            obj.draw(screen)
            x, y = obj.body.position

            if keranjang_pos:
                jarak_ke_keranjang = math.hypot(x - keranjang_pos[0], y - keranjang_pos[1])
                if jarak_ke_keranjang < 120:
                    buah_list.remove(obj)
                    space.remove(obj.body, obj.shape)
                    if obj.is_bom:
                        nyawa -= 1
                    else:
                        skor += 1
                    continue

            if y > height + 100:
                buah_list.remove(obj)
                space.remove(obj.body, obj.shape)
                nyawa -= 1

        if nyawa <= 0:
            game_over = True

        space.step(1 / 60)

        if keranjang_pos:
            keranjang_rect = keranjang_img.get_rect(center=keranjang_pos)
            screen.blit(keranjang_img, keranjang_rect)

        screen.blit(font.render(f"Skor: {skor}", True, (255, 102, 0)), (20, 20))
        screen.blit(font.render(f"Nyawa: {nyawa}", True, (255, 102, 0)), (20, 80))

        waktu_sisa = max(0, int(durasi - (time.time() - start_time)))
        screen.blit(font.render(f"Waktu: {waktu_sisa}", True, (255, 102, 0)), (1050, 20))

        if waktu_sisa == 0:
            game_over = True

    else:
        screen.fill((0, 200, 100))
        screen.blit(big_font.render("GAME OVER!!!", True, black), (350, 200))
        screen.blit(big_font.render(f"Score: {skor}", True, black), (420, 300))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Restart
                skor = 0
                nyawa = 3
                start_time = time.time()
                buah_list.clear()
                game_over = False
            elif event.key == pygame.K_q:
                running = False

    pygame.display.update()
    clock.tick(60)

cap.release()
pygame.quit()
