import pygame
import pymunk
import random
import os
import mediapipe as mp
import cv2
import numpy as np
import time

# Fruit Class
class Fruit:
    def __init__(self, space, path, scale=1, grid=(2, 4),
                 animationFrames=None, speedAnimation=1, speed=3, pathSoundSlice=None):
        # Loading Main Image
        self.scale = scale
        try:
            img = pygame.image.load(path).convert_alpha()
        except pygame.error:
            raise FileNotFoundError(f"Image file not found: {path}")
        width, height = img.get_size()
        img = pygame.transform.smoothscale(img, (int(width * self.scale), int(height * self.scale)))
        width, height = img.get_size()

        # Split image to get all frames
        if animationFrames is None:
            animationFrames = grid[0] * grid[1]
        widthSingleFrame = width / grid[1]
        heightSingleFrame = height / grid[0]
        self.imgList = []
        counter = 0
        for row in range(grid[0]):
            for col in range(grid[1]):
                counter += 1
                if counter <= animationFrames:
                    imgCrop = img.subsurface((col * widthSingleFrame, row * heightSingleFrame,
                                              widthSingleFrame, heightSingleFrame))
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
            try:
                self.soundSlice = pygame.mixer.Sound(self.pathSoundSlice)
            except pygame.error:
                raise FileNotFoundError(f"Sound file not found: {pathSoundSlice}")
        self.slice = False

        self.widthWindow, self.heightWindow = pygame.display.get_surface().get_size()
        self.pos = random.randint(0, self.widthWindow), 100

        # Physics
        self.mass = 1
        self.moment = pymunk.moment_for_circle(self.mass, 0, 30)
        self.body = pymunk.Body(self.mass, self.moment)
        self.shape = pymunk.Circle(self.body, 30)
        self.shape.body.position = self.pos

        # Add to Space
        self.space = space
        self.space.add(self.body, self.shape)

        self.isStartingFrame = True
        self.width, self.height = self.img.get_size()

        self.isBomb = "bomb" in path.lower()

    def draw(self, window):
        if self.isStartingFrame:
            if self.pos[0] < self.widthWindow // 2:
                randX = random.randint(100, 300)
            else:
                randX = random.randint(-300, -100)
            randY = random.randint(900, 1100)
            self.shape.body.apply_impulse_at_local_point((randX, randY), (0, 0))
            self.isStartingFrame = False

        # Draw
        x, y = int(self.body.position[0]), self.heightWindow - int(self.body.position[1])
        self.rectImg.x, self.rectImg.y = x - self.width // 2, y - self.height // 2
        window.blit(self.img, self.rectImg)

    def checkSlice(self, x, y):
        # Adjusted hitbox
        fx, fy = self.rectImg.x + self.width // 2, self.rectImg.y + self.height // 2
        fw, fh = self.width * 0.7, self.height * 0.7

        if fx - fw // 2 < x < fx + fw // 2 and fy - fh // 2 < y < fy + fh // 2 and not self.isAnimating:
            self.isAnimating = True
            if self.pathSoundSlice:
                self.soundSlice.play()

        if self.isAnimating:
            if self.animationCount < len(self.imgList) - 1:
                self.animationCount += 1
                self.img = self.imgList[self.animationCount]
            else:
                self.slice = True
                self.space.remove(self.shape, self.body)

        if self.slice:
            return 2 if self.isBomb else 1
        return None

# Game Function
def Game():
    # Initialize
    pygame.init()
    pygame.event.clear()

    # Create Window/Display
    width, height = 1200, 686
    window = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Fruit Slicer")

    # Initialize Clock for FPS
    fps = 23
    clock = pygame.time.Clock()

    # Images
    try:
        imgGameOver = pygame.image.load("./fru.jpg").convert()
    except pygame.error:
        raise FileNotFoundError("Game over image not found: ./fru.jpg")

    # Initialize mediapipe pose
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1
    )

    # Webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Error: Cannot open webcam")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Webcam resolution: {actual_width}x{actual_height}")

    # Physics
    space = pymunk.Space()
    space.gravity = 0.0, -1000.0

    # Parameters
    timeTotal = 140  # Changed to 140 seconds
    initial_spawn_interval = 1.0
    min_spawn_interval = 0.3
    initial_fruit_speed = 3
    max_fruit_speed = 5
    lives = 5
    max_lives = 3  # Max lives from point conversion

    # Variables
    fruitList = []
    timeGenerator = time.time()
    timeStart = time.time()
    gameOver = False
    score = 0
    popup_message = None
    popup_time = 0

    # Colors
    white = (255, 255, 255)
    yellow = (0, 255, 255)
    black = (0, 0, 0)
    red = (0, 0, 255)

    # Fruit Path List
    pathFruitFolder = "./Fruits"
    if not os.path.exists(pathFruitFolder):
        raise FileNotFoundError(f"Fruits folder not found: {pathFruitFolder}")
    pathListFruit = os.listdir(pathFruitFolder)

    # Fruit Generation Function
    def generateFruit():
        randomScale = round(random.uniform(0.6, 0.8), 2)
        randomFruitPath = pathListFruit[random.randint(0, len(pathListFruit) - 1)]
        pathSoundSlice = './explosion.wav' if "bomb" in randomFruitPath.lower() else './slice.wav'
        elapsed_time = time.time() - timeStart
        speed = initial_fruit_speed + (max_fruit_speed - initial_fruit_speed) * min((elapsed_time - 60) / 60, 1) if elapsed_time > 60 else initial_fruit_speed
        fruitList.append(Fruit(space, path=os.path.join(pathFruitFolder, randomFruitPath),
                               grid=(4, 4), animationFrames=14, scale=randomScale,
                               pathSoundSlice=pathSoundSlice, speed=speed))

    # Check Life Bonus
    def check_life_bonus():
        nonlocal lives, score, popup_message, popup_time
        if lives == 1 and score >= 15 and lives < max_lives:  # Changed to 15 points
            score -= 15
            lives += 1
            popup_message = "Bonus: Poinmu ditukar untuk 1 life!"
            popup_time = time.time()
        elif lives == 2 and score >= 15 and lives < max_lives:  # Changed to 15 points
            score -= 15
            lives += 1
            popup_message = "Bonus: Poinmu ditukar untuk 1 life!"
            popup_time = time.time()

    # Main loop
    try:
        while cap.isOpened():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            if not gameOver:
                success, img = cap.read()
                if not success:
                    print("Failed to capture image")
                    break
                img = cv2.flip(img, 1)
                h, w = img.shape[:2]

                # Process pose
                imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                keypoints = pose.process(imgRGB)
                img = cv2.cvtColor(imgRGB, cv2.COLOR_RGB2BGR)

                # Get nose position
                nose_x, nose_y = None, None
                if keypoints.pose_landmarks:
                    lm = keypoints.pose_landmarks
                    lmPose = mp_pose.PoseLandmark
                    try:
                        nose_x = int(lm.landmark[lmPose.NOSE].x * w)
                        nose_y = int(lm.landmark[lmPose.NOSE].y * h)
                        cv2.circle(img, (nose_x, nose_y), 20, yellow, -1)
                    except AttributeError:
                        pass

                # Critical effects only when lives <= 2
                if lives <= 2:
                    border_thickness = 10
                    cv2.rectangle(img, (0, 0), (w-1, h-1), red, border_thickness)
                    overlay = np.full((h, w, 3), (0, 0, 255), dtype=np.uint8)
                    img = cv2.addWeighted(img, 0.7, overlay, 0.3, 0.0)

                # Convert to Pygame surface
                imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                imgRGB = np.rot90(imgRGB)
                frame = pygame.surfarray.make_surface(imgRGB).convert()
                frame = pygame.transform.flip(frame, True, False)
                window.blit(frame, (0, 0))

                # Dynamic spawn interval for 140 seconds
                elapsed_time = time.time() - timeStart
                if elapsed_time > 120:
                    spawn_interval = max(min_spawn_interval, initial_spawn_interval - (elapsed_time - 120) * 0.035)  # Last 20s
                elif elapsed_time > 100:
                    spawn_interval = max(min_spawn_interval, initial_spawn_interval - (elapsed_time - 100) * 0.02)  # 100-120s
                else:
                    spawn_interval = initial_spawn_interval

                if time.time() - timeGenerator > spawn_interval:
                    generateFruit()
                    timeGenerator = time.time()

                # Check life bonus
                check_life_bonus()

                # Process fruits
                if nose_x is not None and nose_y is not None:
                    for i, fruit in enumerate(fruitList):
                        if fruit:
                            fruit.draw(window)
                            checkSlice = fruit.checkSlice(nose_x, nose_y)
                            if checkSlice == 2:  # Bomb
                                lives -= 1
                                fruitList[i] = None
                                if lives <= 0:
                                    gameOver = True
                                    pygame.mixer.music.stop()
                            elif checkSlice == 1:  # Fruit
                                fruitList[i] = None
                                score += 1

                fruitList = [fruit for fruit in fruitList if fruit]
                timeLeft = int(timeTotal - elapsed_time)
                if timeLeft <= 0:
                    gameOver = True
                    pygame.mixer.music.stop()

                # Render HUD
                font = pygame.font.Font(None, 60)
                for text, pos in [
                    (f"Score: {score}", (50, 35)),
                    (f"Time: {timeLeft}", (1000, 35)),
                    (f"Lives: {lives}", (10, 100))
                ]:
                    text_color = red if text.startswith("Lives") and lives <= 2 else white
                    textSurf = font.render(text, True, text_color)
                    textOutline = font.render(text, True, black)
                    for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                        window.blit(textOutline, (pos[0] + dx, pos[1] + dy))
                    window.blit(textSurf, pos)

                # Render pop-up
                if popup_message and time.time() - popup_time < 2:
                    font_popup = pygame.font.Font(None, 80)
                    popup_surf = font_popup.render(popup_message, True, white)
                    popup_outline = font_popup.render(popup_message, True, black)
                    popup_rect = popup_surf.get_rect(center=(width // 2, height // 2))
                    for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                        window.blit(popup_outline, (popup_rect.x + dx, popup_rect.y + dy))
                    window.blit(popup_surf, popup_rect)
                elif time.time() - popup_time >= 2:
                    popup_message = None

            else:
                window.blit(imgGameOver, (0, 0))
                font = pygame.font.Font(None, 150)
                # Display "You Win!" if time runs out
                win_text = "You Win!" if timeLeft <= 0 else "You Lose!"
                for text, pos in [
                    (win_text, (400, 143)),
                    ("Your Score:", (350, 243)),
                    (str(score), (600, 343))
                ]:
                    textSurf = font.render(text, True, black)
                    window.blit(textSurf, pos)

            pygame.display.update()
            clock.tick(fps)
            space.step(1 / fps)
    finally:
        cap.release()
        cv2.destroyAllWindows()
        pygame.quit()

if __name__ == "__main__":
    Game()