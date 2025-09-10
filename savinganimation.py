import pygame
import sys
import random
import os
import subprocess

# Initialize Pygame
pygame.init()

# Create a directory for frames if it doesn't exist
if not os.path.exists("frames"):
    os.makedirs("frames")

# Constants
SCREEN_WIDTH = 1280  # 16:9 aspect ratio (1280x720 for YouTube)
SCREEN_HEIGHT = 720
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
BLUE = (173, 216, 230)  # Light blue for the walls
BROWN = (139, 69, 19)   # Brown for floor
TEACHER_ARM_COLOR = (160, 82, 45)  # Brownish color for the arms to make them visible
FPS = 30  # Frames per second
DURATION = 10  # The total time for writing to complete (in seconds)

# Set your whiteboard text here
WHITEBOARD_TEXT = "The Secret to Cleaning Up Your Cells: How Exercise Recycles Proteins for Better Brain Health!"

# Load the MDI logo image
mdi_logo = pygame.image.load('MDI_Logo.jpg')
mdi_logo = pygame.transform.scale(mdi_logo, (200, 200))  # Initial size of the logo

# Logo expansion variables
LOGO_EXPANSION_DURATION = 1.5  # Time in seconds for logo to expand
LOGO_EXPANSION_START = 12 * FPS  # Frame count when the logo expansion begins
EXPANSION_FRAMES = int(LOGO_EXPANSION_DURATION * FPS)
LOGO_INITIAL_POSITION = (1000, 150)  # Initial position of the logo

# Load chaos animals (simple shapes for now)
chaos_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0)]  # More colors
chaos_positions = [(900, 500), (1050, 550), (1150, 510), (1000, 600), (1100, 570)]
chaos_speeds = [random.choice([-2, 2]) for _ in chaos_positions]

# Create screen object
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Classroom Animation")

# Define clock to control the frame rate
clock = pygame.time.Clock()

# Function to split the text into multiple lines to fit on the chalkboard
def split_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = words[0]

    for word in words[1:]:
        # Check if adding the word to the current line exceeds the max width
        if font.size(current_line + " " + word)[0] < max_width:
            current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)  # Append the last line

    return lines

# Function to draw the classroom background (walls, floor, etc.)
def draw_classroom():
    # Draw the walls (light blue)
    screen.fill(BLUE)
    
    # Draw the floor (brown)
    pygame.draw.rect(screen, BROWN, (0, SCREEN_HEIGHT - 200, SCREEN_WIDTH, 200))  
    
    # Replace the window with the logo
    screen.blit(mdi_logo, LOGO_INITIAL_POSITION)

    # Add a simple clock on the wall
    pygame.draw.circle(screen, BLACK, (150, 100), 50)  # Clock outline
    pygame.draw.circle(screen, WHITE, (150, 100), 48)  # Clock face
    pygame.draw.line(screen, BLACK, (150, 100), (150, 60), 5)  # Clock hour hand
    pygame.draw.line(screen, BLACK, (150, 100), (180, 100), 3)  # Clock minute hand

# Function to draw the chalkboard
def draw_chalkboard():
    pygame.draw.rect(screen, BLACK, (50, 50, 900, 400))  # Chalkboard
    pygame.draw.rect(screen, GREEN, (45, 45, 910, 410), 5)  # Chalkboard border

# Function to draw the teacher while writing (facing the chalkboard)
def draw_teacher_writing(x, y, arm_up=False):
    # Body
    pygame.draw.circle(screen, (255, 224, 189), (x, y - 80), 70)  # Head behind the body
    pygame.draw.line(screen, BLACK, (x, y + 80), (x - 70, y + 200), 15)  # Left leg
    pygame.draw.line(screen, BLACK, (x, y + 80), (x + 70, y + 200), 15)  # Right leg
    pygame.draw.line(screen, TEACHER_ARM_COLOR, (x + 10, y - 40), (x + 100, y), 15)  # Right arm in front

    if arm_up:
        pygame.draw.line(screen, TEACHER_ARM_COLOR, (x - 50, y - 40), (x - 150, y - 130), 15)  # Arm up (writing)
        pygame.draw.rect(screen, (255, 215, 0), (x - 160, y - 140, 50, 8))  # Pencil body
        pygame.draw.rect(screen, (255, 0, 0), (x - 160, y - 140, 10, 8))  # Pencil eraser
        pygame.draw.rect(screen, BLACK, (x - 120, y - 140, 5, 8))  # Pencil tip
        pygame.draw.rect(screen, (255, 255, 255), (x - 60, y - 80, 120, 200))  # Body
    else:
        pygame.draw.line(screen, TEACHER_ARM_COLOR, (x - 50, y - 40), (x - 150, y - 20), 15)  # Arm down
        pygame.draw.rect(screen, (255, 255, 255), (x - 60, y - 80, 120, 200))  # Body

# Function to draw the teacher after turning around (facing the audience)
def draw_teacher_turned(x, y, waving=False):
    pygame.draw.line(screen, BLACK, (x, y + 80), (x - 70, y + 200), 15)  # Left leg
    pygame.draw.line(screen, BLACK, (x, y + 80), (x + 70, y + 200), 15)  # Right leg
    pygame.draw.rect(screen, (255, 255, 255), (x - 60, y - 80, 120, 200))  # White shirt

    # Add the logo to the shirt
    logo_size = (70, 70)  # Resize logo to a smaller size
    resized_logo = pygame.transform.scale(mdi_logo, logo_size)
    logo_position = (x - logo_size[0] // 2, y + 15)  # Position it on the shirt, centered
    screen.blit(resized_logo, logo_position)

    # Waving left arm with thumbs-up
    if waving:
        pygame.draw.line(screen, TEACHER_ARM_COLOR, (x - 50, y - 60), (x - 150, y - 150), 15)  # Arm up (waving)
        pygame.draw.circle(screen, WHITE, (x - 150, y - 150), 15)  # Left hand
        pygame.draw.rect(screen, BLACK, (x - 140, y - 155, 5, 10))  # Left thumb up
        pygame.draw.circle(screen, (255, 224, 189), (x, y - 80), 70)  # Head
        pygame.draw.circle(screen, BLACK, (x - 25, y - 90), 8)  # Left eye
        pygame.draw.circle(screen, BLACK, (x + 25, y - 90), 8)  # Right eye
        pygame.draw.arc(screen, BLACK, (x - 25, y - 80, 50, 30), 3.14, 6.28, 3)  # Smile
    else:
        pygame.draw.line(screen, TEACHER_ARM_COLOR, (x - 50, y - 60), (x - 150, y - 100), 15)  # Arm down
        pygame.draw.circle(screen, (255, 224, 189), (x, y - 80), 70)  # Head
        pygame.draw.circle(screen, BLACK, (x - 25, y - 90), 8)  # Left eye
        pygame.draw.circle(screen, BLACK, (x + 25, y - 90), 8)  # Right eye
        pygame.draw.arc(screen, BLACK, (x - 25, y - 80, 50, 30), 3.14, 6.28, 3)  # Smile

    # Right arm in a natural position, lower than the mouth
    pygame.draw.line(screen, TEACHER_ARM_COLOR, (x + 48, y), (x + 100, y + 60), 15)  # Right arm lowered
    pygame.draw.circle(screen, WHITE, (x + 100, y + 60), 15)  # Right hand
    pygame.draw.rect(screen, BLACK, (x + 110, y + 55, 5, 10))  # Right thumb

# Function to display text on the chalkboard
def write_on_board(lines, font, x, y, total_visible_chars):
    visible_chars = total_visible_chars  # The total number of characters revealed across all lines

    # Loop through the lines and display them, revealing them progressively
    for i, line in enumerate(lines):
        if visible_chars > len(line):
            text_surface = font.render(line, True, WHITE)  # Render the full line
            screen.blit(text_surface, (x, y + i * 50))
            visible_chars -= len(line)  # Deduct the characters in this line from the total
        else:
            visible_text = line[:visible_chars]  # Reveal only part of the current line
            text_surface = font.render(visible_text, True, WHITE)
            screen.blit(text_surface, (x, y + i * 50))
            break  # Stop after rendering the partially revealed line

# Function for chaos animation
def draw_chaos(chaos_positions, chaos_colors):
    for i in range(len(chaos_positions)):
        x, y = chaos_positions[i]
        pygame.draw.circle(screen, chaos_colors[i], (x, y), 30)  # Representing animals as colored circles
        chaos_positions[i] = (x + chaos_speeds[i], y + random.choice([-1, 1]))
        if x <= 800 or x >= 1200:
            chaos_speeds[i] *= -1  # Reverse direction

# Function to expand the logo from the top-right corner (fixed)
def expand_logo_from_wall_top_right(frame_count):
    if frame_count > LOGO_EXPANSION_START:
        # Calculate how many frames have passed since the expansion started
        elapsed_frames = frame_count - LOGO_EXPANSION_START
        scale_factor = min(1 + (elapsed_frames / EXPANSION_FRAMES) * 5, 6)  # Scale up to 6x original size

        # Calculate the new logo size
        new_width = int(200 * scale_factor)
        new_height = int(200 * scale_factor)

        # Calculate the new top-left position (anchored to the top-right corner)
        new_left_x = 1200 - new_width  # Anchoring to the right, with the top-right corner fixed
        new_top_y = 150  # Keep the top-y position fixed as it expands downwards

        # Resize the logo
        new_logo = pygame.transform.scale(mdi_logo, (new_width, new_height))

        # Draw the expanded logo from the new position
        screen.blit(new_logo, (new_left_x, new_top_y))

# Main loop
def main():
    font = pygame.font.Font(None, 60)  # Font for chalkboard writing (larger font for better visibility)
    arm_up = False
    frame_count = 0
    teacher_x, teacher_y = 300, 550  # Adjusted teacher position closer to chalkboard
    waving = False
    turned_around = False

    # Split the text into multiple lines
    lines = split_text(WHITEBOARD_TEXT, font, 800)

    total_chars = sum(len(line) for line in lines)  # Total number of characters in the message
    chars_per_frame = total_chars / (DURATION * FPS)  # Calculate how many characters per frame

    total_visible_chars = 0  # Total number of characters revealed across all lines

    while frame_count < DURATION * FPS + EXPANSION_FRAMES:  # Set a limit on the total frames
        draw_classroom()  # Draw the classroom
        draw_chalkboard()  # Draw the chalkboard

        # Animate text writing by revealing characters at a rate to finish in 10 seconds
        total_visible_chars += chars_per_frame

        # Stop arm movement and turn the teacher around when text is done
        if total_visible_chars >= total_chars:
            total_visible_chars = total_chars  # Ensure we don't reveal more than the total characters
            turned_around = True
            if frame_count % 30 < 15:
                waving = True
            else:
                waving = False
        else:
            # Alternate arm movement every 5 frames (to sync with writing speed)
            if frame_count % 10 < 5:
                arm_up = True
            else:
                arm_up = False

        # Draw the chaos scene in the bottom right (before the teacher turns)
        if not turned_around:
            draw_chaos(chaos_positions, chaos_colors)
            draw_teacher_writing(teacher_x, teacher_y, arm_up)  # Draw the teacher writing
        else:
            draw_teacher_turned(teacher_x, teacher_y, waving)  # Draw the teacher after turning

        write_on_board(lines, font, 100, 100, int(total_visible_chars))  # Write text on the chalkboard
        
        # Trigger the logo expansion at the correct time
        if frame_count >= LOGO_EXPANSION_START:
            expand_logo_from_wall_top_right(frame_count)

        # Save each frame as an image
        pygame.image.save(screen, f"frames/frame_{frame_count:04d}.png")

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Update display and frame count
        pygame.display.update()
        frame_count += 1
        clock.tick(FPS)  # Run at 30 frames per second

    # After saving all frames, use ffmpeg to create a video from the frames
    generate_video()

# Function to generate video from frames using ffmpeg
def generate_video():
    # Call ffmpeg command to convert frames into video
    try:
        subprocess.run([
            "ffmpeg", "-r", "30", "-i", "frames/frame_%04d.png", "-vcodec", "libx264", 
            "-crf", "25", "-pix_fmt", "yuv420p", "animation_video.mp4"
        ], check=True)
        print("Video created successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error creating video: {e}")

if __name__ == "__main__":
    main()
