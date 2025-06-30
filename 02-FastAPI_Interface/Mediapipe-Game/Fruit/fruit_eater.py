import pygame
import pymunk
import random
import os
import cv2
import numpy as np
import mediapipe as mp
import time

class Fruit:
    def __init__(self, space, path, scale=1, grid=(2, 4),
                 animationFrames=None, speedAnimation=1, speed=3, pathSoundSlice=None):
        # Loading Main Image
        self.scale = scale
        img = pygame.image.load(path).convert_alpha()
        width, height = img.get_size()
        img = pygame.transform.smoothscale(img, (int(width * self.scale), (int(height * self.scale))))
        width, height = img.get_size()

        # Split image to get all frames
        if animationFrames is None:  # When animation frames is not defined then use all frames
            animationFrames = grid[0] * grid[1]
        widthSingleFrame = width / grid[1]
        heightSingleFrame = height / grid[0]
        self.imgList = []
        counter = 0
        for row in range(grid[0]):
            for col in range(grid[1]):
                counter += 1
                if counter <= animationFrames:
                    imgCrop = img.subsurface(col * widthSingleFrame, row * heightSingleFrame,
                                              widthSingleFrame, heightSingleFrame)
                    self.imgList.append(imgCrop)

        self.img = self.imgList[0]
        self.rectImg = self.img.get_rect()
        self.path = path
        self.animationCount = 0
        self.speedAnimation = speedAnimation
        self.isAnimating = False
        self.speed = speed
        self.pathSoundSlice = pathSoundSlice
        if self.pathSoundSlice:
            self.soundSlice = pygame.mixer.Sound(self.pathSoundSlice)
        self.slice = False

        self.widthWindow, self.heightWindow = pygame.display.get_surface().get_size()
        self.pos = random.randint(0, self.widthWindow), 100

        # Physics
        self.mass = 1
        self.moment = pymunk.moment_for_circle(self.mass, 0, 30)
        self.body = pymunk.Body(self.mass, self.moment)
        self.shape = pymunk.Circle(self.body, 30)
        self.shape.body.position = self.pos
        self.space = space
        self.space.add(self.body, self.shape)

        self.isStartingFrame = True
        self.width, self.height = self.img.get_size()

        if "bomb" in path:
            self.isBomb = True
        else:
            self.isBomb = False

    def draw(self, window):
        if self.isStartingFrame:
            if self.pos[0] < self.widthWindow // 2:
                randX = random.randint(-200, 200)
            else:
                randX = random.randint(-200, 200)
            randY = random.randint(700, 1000)  # Consistent downward push
            self.shape.body.apply_impulse_at_local_point((randX, -randY), (0, 0))  # Negative for downward
            self.isStartingFrame = False

        # Draw
        x, y = int(self.body.position[0]), self.heightWindow - int(self.body.position[1])
        self.rectImg.x, self.rectImg.y = x - self.width // 2, y - self.height // 2
        window.blit(self.img, self.rectImg)

    def get_rect(self):
        return self.rectImg 

def Game():
    # Initialize
    pygame.init()
    pygame.mixer.init()
    pygame.event.clear()

    # Window
    width, height = 1200, 686
    window = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Fruit Slicer & Catcher")

    # Clock
    fps = 23
    clock = pygame.time.Clock()

    # Images
    try:
        imgGameOver = pygame.image.load("./fru.jpg").convert()
    except FileNotFoundError:
        print("File 'fru.jpg' not found. Please check the path.")
        pygame.quit()
        return

    # MediaPipe Face Mesh (for mouth)
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.7)

    # Webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        pygame.quit()
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # Physics
    space = pymunk.Space()
    space.gravity = (0.0, -100.0)  # Standard gravity for natural falling

    # Parameters
    timeTotal = 60
    fruits_eaten = 0
    mouth_open_threshold = 0.03
    attraction_threshold = 100  # Distance threshold for mouth attraction

    # Variables
    fruitList = []
    timeGenerator = time.time()
    timeStart = time.time()
    gameOver = False
    score = 0

    # Colors
    blue = (255, 127, 0)
    yellow = (0, 255, 255)
    black = (0, 0, 0)

    # Fruit Paths
    pathFruitFolder = "./Fruits"
    if not os.path.exists(pathFruitFolder):
        print(f"Fruit folder '{pathFruitFolder}' not found.")
        pygame.quit()
        return
        
    pathListFruit = os.listdir(pathFruitFolder)

    def generateFruit():
        randomScale = round(random.uniform(0.6, 0.8), 2)
        randomFruitPath = pathListFruit[random.randint(0, len(pathListFruit) - 1)]
        pathSoundSlice = './explosion.wav' if "bomb" in randomFruitPath else './slice.wav'
        fruit = Fruit(space, path=os.path.join(pathFruitFolder, randomFruitPath),
                      grid=(4, 4), animationFrames=14, scale=randomScale,
                      pathSoundSlice=pathSoundSlice)
        fruit.body.position = (random.randint(100, width - 100), height + 50)  # Start from top
        fruitList.append(fruit)

    def is_mouth_open(landmarks, img_w, img_h):
        upper_lip = landmarks[13]
        lower_lip = landmarks[14]
        mouth_height = abs(lower_lip.y * img_h - upper_lip.y * img_h) / img_h
        return mouth_height > mouth_open_threshold

    def get_mouth_position(landmarks, img_w, img_h):
        upper_lip = landmarks[13]
        lower_lip = landmarks[14]
        mouth_x = int((upper_lip.x + lower_lip.x) / 2 * img_w)
        mouth_y = int((upper_lip.y + lower_lip.y) / 2 * img_h)
        return mouth_x, mouth_y

    # Main Loop
    running = True
    while cap.isOpened() and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

        if not running:
            break

        if not gameOver and running:
            success, img = cap.read()
            if not success:
                continue
            h, w = img.shape[:2]

            # Process Face Mesh (mouth)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(img_rgb)
            mouth_open = False
            mouth_pos = (w // 2, h // 2)
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    landmarks = face_landmarks.landmark
                    mouth_open = is_mouth_open(landmarks, w, h)
                    mouth_pos = get_mouth_position(landmarks, w, h)
                    cv2.circle(img, mouth_pos, 10, yellow, -1)

            # Display webcam feed
            frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = pygame.surfarray.make_surface(frame)
            frame = pygame.transform.scale(frame, (width, height))
            window.blit(frame, (0, 0))

            # Generate fruits
            if time.time() - timeGenerator > 1:
                generateFruit()
                timeGenerator = time.time()

            # Update fruits
            for i, fruit in enumerate(fruitList):
                if fruit:
                    fruit_pos = fruit.body.position
                    target_x, target_y = mouth_pos
                    target_x = target_x
                    target_y = height - target_y
                    dx = target_x - fruit_pos.x
                    dy = target_y - fruit_pos.y
                    distance = (dx**2 + dy**2)**0.5

                    # Only attract to mouth if close enough
                    if distance < attraction_threshold and mouth_open:
                        if distance > 0:
                            speed = 300
                            fruit.body.velocity = (dx / distance * speed, dy / distance * speed)
                    else:
                        # Let gravity work
                        pass

                    fruit.draw(window)

                    fruit_rect = fruit.get_rect()
                    mouth_rect = pygame.Rect(mouth_pos[0] - 20, height - (mouth_pos[1] + 20), 40, 40)
                    if mouth_open and fruit_rect.colliderect(mouth_rect):
                        if fruit.isBomb:
                            gameOver = True
                            pygame.mixer.music.stop()
                        else:
                            fruitList[i] = None
                            fruits_eaten += 1
                            score += 1
                            pygame.mixer.Sound('./slice.wav').play()

            fruitList = [f for f in fruitList if f is not None]

            # Time and score
            timeLeft = int(timeTotal - (time.time() - timeStart))
            if timeLeft <= 0:
                gameOver = True
                pygame.mixer.music.stop()

            font = pygame.font.Font(None, 60)
            textScore = font.render(f"Score: {score}", True, blue)
            textTime = font.render(f"Time: {timeLeft}", True, blue)
            window.blit(textScore, (225, 35))
            window.blit(textTime, (1100, 38))

        elif running:
            window.blit(imgGameOver, (0, 0))
            font = pygame.font.Font(None, 150)
            textLose = font.render("Game Over!", True, black)
            textScore = font.render(f"Score: {score}", True, black)
            window.blit(textLose, (400, 143))
            window.blit(textScore, (350, 243))

        pygame.display.update()
        clock.tick(fps)
        space.step(1 / fps)

    # Clean up
    cap.release()
    pygame.quit()

if __name__ == "__main__":
    Game()