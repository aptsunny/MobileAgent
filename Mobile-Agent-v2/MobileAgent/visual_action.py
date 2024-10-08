import os, math
from PIL import Image, ImageDraw, ImageFont

# Define a class to manage screenshots and operations
class ScreenshotManager:
    def __init__(self, screenshot_path, iter=0):
        self.screenshot_path = screenshot_path
        self.font = ImageFont.truetype('simsun.ttc', 30)
        self.tag_font = ImageFont.truetype("arial.ttf", 40)
        self.iter = iter


    def tap(self, x, y):
        # Perform clicks
        print(f"Tapping at ({x}, {y})")
        self.annotate_screenshot(x, y, "Tap", "blue", 40, 10)

    def swipe(self, x1, y1, x2, y2):
        # Perform sliding operation
        print(f"Swiping from ({x1}, {y1}) to ({x2}, {y2})")
        self.annotate_screenshot(x1, y1, "Swipe", "red", 10, 5, x2, y2, "arrow")

    def type(self, text, x=None, y=None):
        # Enter text operation
        print(f"Typing: {text}")
        self.annotate_screenshot(x, y, f"Type: {text}", "green", 30, 15)

    def back(self, x=None, y=None):
        # Execution return operation
        print("Back button pressed")
        self.annotate_screenshot(x, y, "Back", "red", 30, 15)

    def home(self, x=None, y=None):
        # Perform back to the desktop operation
        print("Home button pressed")
        self.annotate_screenshot(x, y, "Home", "purple", 30, 15)

    def stop(self, x=None, y=None):
        # Stop operation
        print("Stop button pressed")
        self.annotate_screenshot(x, y, "Stop", "orange", 30, 15)

    def annotate_screenshot(self, x, y, action, color, circle_radius, line_width, end_x=None, end_y=None, arrow=None):
        # Load screenshot
        screenshot = Image.open(self.screenshot_path)
        draw = ImageDraw.Draw(screenshot)

        # Draw an operation instruction
        if end_x is not None and end_y is not None:
            # Draw the sliding path and arrow
            draw.line((x, y, end_x, end_y), fill=color, width=line_width)
            if arrow:
                self.draw_arrow(draw, (x, y), (end_x, end_y), color)
            action += f" ({x}, {y}) -> ({end_x}, {end_y})"
        else:
            # Draw a click position
            draw.ellipse((x-circle_radius, y-circle_radius, x+circle_radius, y+circle_radius), fill=color)

        # Add text description
        text_width, text_height = draw.textsize(action, font=self.font)
        draw.rectangle([x - text_width // 2 - 5, y - text_height // 2 - 5, x + text_width // 2 + 5, y + text_height // 2 + 5], fill=color)
        draw.text((x - text_width // 2, y - text_height // 2), action, fill='white', font=self.font)


        # Save the screenshot after the marking
        new_screenshot_path = self.screenshot_path.replace(".png", "_annotated.png")
        # print(self.iter)
        # import pdb;pdb.set_trace()
        
        screenshot.save(new_screenshot_path)
        print(f"Screenshot saved with annotations: {new_screenshot_path}")

    def draw_arrow(self, draw, start, end, color):
        # Draw an arrow
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = (dx**2 + dy**2)**0.5
        angle = (dy / length) * 30
        if dy < 0:
            angle = -angle
        draw.line([end[0], end[1], end[0] + dx * 0.1, end[1] + dy * 0.1], fill=color, width=5)
        draw.line([end[0], end[1], end[0] + dx * 0.1 * math.cos(angle), end[1] + dy * 0.1 * math.sin(angle)], fill=color, width=5)
        draw.line([end[0], end[1], end[0] + dx * 0.1 * math.cos(-angle), end[1] + dy * 0.1 * math.sin(-angle)], fill=color, width=5)

    def add_tag(self, tag_text):
        # Add labels to the bottom of the screenshot
        screenshot = Image.open(self.screenshot_path)
        draw = ImageDraw.Draw(screenshot)
        tag_width, tag_height = draw.textsize(tag_text, font=self.tag_font)
        draw.rectangle([0, screenshot.height - tag_height - 10, screenshot.width, screenshot.height], fill="black")
        draw.text((screenshot.width // 2 - tag_width // 2, screenshot.height - tag_height - 10), tag_text, fill='white', font=self.tag_font, anchor="mm")
        new_screenshot_path = self.screenshot_path.replace(".jpg", "_tagged.jpg")
        screenshot.save(new_screenshot_path)
        print(f"Screenshot saved with tag: {new_screenshot_path}\n")
