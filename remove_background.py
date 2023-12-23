import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import random
import numpy as np
from coordinates import canvas_to_full_img_coords, get_image_position_in_canvas, canvas_coords_to_img_coords

def remove_white_background(image, mask, threshold, random_color=False):
    """
    Removes the white background from an image, respecting the mask.

    Parameters:
    image (PIL.Image): The image to process.
    mask (PIL.Image): The mask image.
    threshold (int): The threshold value to determine white pixels.

    Returns:
    PIL.Image: The processed image with transparent background.
    """
    if image is None:
        return None
    img = image.convert("RGBA")
    datas = img.getdata()
    mask_data = mask.getdata()

    newData = []
    for i, item in enumerate(datas):
        if mask is not None and mask_data[i] == 0:  # If the mask is black, skip changing this pixel
            newData.append(item)
        elif item[0] > threshold and item[1] > threshold and item[2] > threshold:
            # Replace with random color for visualization
            if random_color:
                rgb = np.random.randint(0, 255, 3)
            else:
                rgb = (255, 255, 255)
            newData.append((*rgb, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    return img

def update_image(threshold):
    global image, mask, photo, processed_image, canvas, img_label

    if image is not None:
        processed_image = remove_white_background(image, mask, threshold)
        photo = ImageTk.PhotoImage(processed_image)
        canvas.itemconfig(img_label, image=photo)

def start_drawing(event):
    global lastx, lasty
    lastx, lasty = event.x, event.y
    print("Start drawing at", lastx, lasty)
    draw(event)

def draw_on_mask(x, y):
    global lastx, lasty, mask_draw, mask_canvas, image
    if image is None:
        return

    img_x, img_y = get_image_position_in_canvas(mask_canvas, image.size)
    # Adjust the coordinates relative to the image position
    adj_x = x - img_x
    adj_y = y - img_y
    # Ensure adjusted coordinates are within the image boundaries
    if 0 <= adj_x < image.size[0] and 0 <= adj_y < image.size[1]:
        mask_draw.line([lastx - img_x, lasty - img_y, adj_x, adj_y], fill="black", width=5)

def draw_on_boolean_mask(x, y):
    global lastx, lasty, mask_draw

    if original_image is None:
        return

    # Translate canvas coordinates to full image coordinates
    full_img_x, full_img_y = canvas_to_full_img_coords(canvas, original_image, image, zoom_level, zoom_center, x, y)
    last_full_img_x, last_full_img_y = canvas_to_full_img_coords(canvas, original_image, image, zoom_level, zoom_center, lastx, lasty)

    # Draw on the boolean mask
    mask_draw.line([last_full_img_x, last_full_img_y, full_img_x, full_img_y], fill=0, width=5)

    lastx, lasty = x, y

def update_mask_display():
    global mask, mask_photo, mask_canvas, mask_canvas_image, boolean_mask, max_size
    # Crop the mask to the current view
    mask = resize_image(boolean_mask.crop((left, upper, right, lower)), max_size)
    # print((left, upper, right, lower))
    mask_photo = ImageTk.PhotoImage(mask)
    mask_canvas.itemconfig(mask_canvas_image, image=mask_photo)

def draw(event):
    global lastx, lasty, threshold_slider
    x, y = event.x, event.y
    # draw_on_mask(x, y)
    draw_on_boolean_mask(x, y)
    lastx, lasty = x, y
    update_mask_display()
    update_image(threshold_slider.get())

def open_image():
    global image, photo, canvas, img_label, mask, mask_draw, mask_photo, mask_canvas, mask_canvas_image, original_image
    global boolean_mask, left, upper, right, lower
    global max_size

    file_path = filedialog.askopenfilename()
    if file_path:
        original_image = Image.open(file_path)
        print("Image size:", original_image.size)
        
        # Resize image for display
        max_size = (300, 300)  # Assuming canvas size is 300x300
        image = resize_image(original_image, max_size)
        photo = ImageTk.PhotoImage(image)
        canvas.itemconfig(img_label, image=photo)

        global left, upper, right, lower, zoom_center, zoom_level
        left = upper = 0
        right, lower = original_image.size
        zoom_center = (original_image.size[0] // 2, original_image.size[1] // 2)
        zoom_level = 1.0

        # Initialize the boolean mask based on alpha channel or grayscale
        threshold = threshold_slider.get()
        alpha = None
        if original_image.mode == 'RGBA':
            alpha = original_image.split()[-1]  # Extract alpha channel
         
        alpha = original_image.convert('L')  # Convert to grayscale

        boolean_mask = Image.eval(alpha, lambda px: 255 if px > threshold else 0).convert('1')
        # boolean_mask = Image.new('1', original_image.size, 255)  # '1' for 1-bit pixels, False (0) everywhere
        
        mask = boolean_mask
        mask_draw = ImageDraw.Draw(mask)
        mask_photo = ImageTk.PhotoImage(mask)
        mask_canvas_image = mask_canvas.create_image(150, 150, image=mask_photo)

        # Update the image initially
        update_image(threshold_slider.get())

def resize_image(image, max_size):
    """
    Resize an image to fit within a specified size while maintaining aspect ratio.
    """
    global max_scale_factor, min_scale_factor, scale_factor
    ratio = min(max_size[0] / image.size[0], max_size[1] / image.size[1])
    if max_scale_factor is None:
        max_scale_factor = ratio * 256
        min_scale_factor = ratio
        scale_factor = ratio
    new_size = tuple([int(x*ratio) for x in image.size])
    return image.resize(new_size, Image.ANTIALIAS)

# Create the main window
root = tk.Tk()
root.title("Image Background Remover")

# Initialize global variables
image = None
processed_image = None
mask = None
mask_draw = None
lastx = lasty = 0
original_image = None
max_scale_factor = None
left = upper = 0
right = lower = 300

# Global variables for panning
is_panning = False
start_x, start_y = 0, 0


# Create a canvas to display the image and another for the mask
canvas = tk.Canvas(root, width=300, height=300)
img_label = canvas.create_image(150, 150, anchor=tk.CENTER)
canvas.pack(side=tk.LEFT)

mask_canvas = tk.Canvas(root, width=300, height=300)
mask_canvas.pack(side=tk.RIGHT)

# Bind mouse events for drawing on the mask canvas
mask_canvas.bind("<Button-1>", start_drawing)
mask_canvas.bind("<B1-Motion>", draw)
canvas.bind("<Button-1>", start_drawing)
canvas.bind("<B1-Motion>", draw)

def handle_zoom(event):
    global max_scale_factor, min_scale_factor, scale_factor, zoom_center, zoom_level
    print("Mousewheel event at", event.x, event.y, event.delta)
    x, y = canvas_to_full_img_coords(canvas, original_image, image, zoom_level, zoom_center, event.x, event.y)
    zoom_level += 0.1 if event.delta > 0 else -0.1  # Zoom in for positive delta, out for negative
    zoom_level = max(1.0, min(25, zoom_level))
    # scale_factor = 1.25 if event.delta > 0 else 0.8  # Zoom in for positive delta, out for negative
    print("Zooming to", zoom_level, "at", x, y)

    zoom_image(zoom_level, x, y)

def zoom_image(zoom_level, center_x, center_y):
    global image, photo, mask, mask_photo, canvas, img_label, mask_canvas, mask_canvas_image, original_image, zoom_center
    global left, upper, right, lower
    global max_size

    if original_image is None:
        return

    # Update zoom level and center
    zoom_center = (center_x, center_y)
    # Calculate new cropping area based on zoom level and center
    print("Zoom level:", zoom_level)
    if zoom_level == 1.0:
        left = upper = 0
        right, lower = original_image.size
        print("Resetting crop area to", (left, upper, right, lower))
    else:
        new_width, new_height = int(original_image.size[0] / zoom_level), int(original_image.size[1] / zoom_level)
        print("New size:", new_width, new_height)
        left = max(center_x - new_width // 2, 0)
        upper = max(center_y - new_height // 2, 0)
        right = min(center_x + new_width // 2, original_image.size[0])
        lower = min(center_y + new_height // 2, original_image.size[1])

        left = min(left, original_image.size[0]-1)
        upper = min(upper, original_image.size[1]-1)
        right = max(right, 1)
        lower = max(lower, 1)

        # If the crop area is smaller than the canvas, center it
        if right - left < new_width:
            left = max(0, right - new_width)
            right = min(original_image.size[0], left + new_width)
        if lower - upper < new_height:
            upper = max(0, lower - new_height)
            lower = min(original_image.size[1], upper + new_height)
        
        left, right = min(left, right), max(left, right)
        upper, lower = min(upper, lower), max(upper, lower)

        print("Exp size:", right - left, lower - upper)
    
    crop_area = (left, upper, right, lower)
    print("Crop area:", crop_area)

    zoom_center = (left + (right - left) // 2, upper + (lower - upper) // 2)

    # Crop and update the image and mask
    image = resize_image(original_image.crop(crop_area), max_size)
    photo = ImageTk.PhotoImage(image)
    canvas.itemconfig(img_label, image=photo)

    mask = resize_image(boolean_mask.crop(crop_area), max_size)
    mask_photo = ImageTk.PhotoImage(mask)
    mask_canvas.itemconfig(mask_canvas_image, image=mask_photo)

    # Redraw the image with the updated mask
    update_image(threshold_slider.get())

def start_panning(event):
    global is_panning, start_x, start_y
    is_panning = True
    start_x, start_y = event.x, event.y

def stop_panning(event):
    global is_panning
    is_panning = False

def pan_image(event):
    global start_x, start_y, zoom_center, zoom_level, is_panning

    if not is_panning:
        return

    dx = (start_x - event.x) * zoom_level
    dy = (start_y - event.y) * zoom_level
    zoom_center = (zoom_center[0] + dx, zoom_center[1] + dy)

    zoom_image(zoom_level, zoom_center[0], zoom_center[1])
    start_x, start_y = event.x, event.y

# Initialize zoom level and center
zoom_level = 1.0
zoom_center = (150, 150)  # Initial zoom center, can be adjusted

# In the main part of your script, bind the mouse wheel event
root.bind("<MouseWheel>", handle_zoom)  # For Windows and MacOS
root.bind("<Button-4>", handle_zoom)    # For Linux, scroll up
root.bind("<Button-5>", handle_zoom)    # For Linux, scroll down

# Bind right-click and motion for panning
canvas.bind("<Button-3>", start_panning)
canvas.bind("<B3-Motion>", pan_image)
canvas.bind("<ButtonRelease-3>", stop_panning)

mask_canvas.bind("<Button-3>", start_panning)
mask_canvas.bind("<B3-Motion>", pan_image)
mask_canvas.bind("<ButtonRelease-3>", stop_panning)


def on_threshold_change(value):
    try:
        threshold = int(value)
        threshold_slider.set(threshold)
        update_image(threshold)
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid integer.")

def save_image():
    global processed_image

    if processed_image is not None:
        processed_image = remove_white_background(original_image, boolean_mask, threshold_slider.get())
        file_path = filedialog.asksaveasfilename(defaultextension=".png")
        if file_path:
            processed_image.save(file_path)
            messagebox.showinfo("Image Saved", "Your image has been saved successfully.")
    else:
        messagebox.showwarning("No Image", "No processed image to save.")

# Add a slider and entry for threshold value
threshold_frame = tk.Frame(root)
threshold_slider = tk.Scale(threshold_frame, from_=0, to=255, orient=tk.HORIZONTAL, label="Threshold", command=lambda value: update_image(int(value)))
threshold_slider.set(200)  # Default threshold value
threshold_slider.pack(side=tk.LEFT)

threshold_entry = tk.Entry(threshold_frame, width=5)
threshold_entry.pack(side=tk.LEFT)
threshold_entry.bind("<Return>", lambda event: on_threshold_change(threshold_entry.get()))

threshold_frame.pack()

# Add buttons to open and save an image
open_button = tk.Button(root, text="Open Image", command=open_image)
open_button.pack()

save_button = tk.Button(root, text="Save Image", command=save_image)
save_button.pack()

def display_mouse_position(event):
    global zoom_center, zoom_level

    # Canvas coordinates
    canvas_x, canvas_y = event.x, event.y

    # Image coordinates
    img_x, img_y = get_image_position_in_canvas(canvas, image.size)

    # Other Image coordinates
    adj_x, adj_y = canvas_coords_to_img_coords(canvas, image, canvas_x, canvas_y)

    # Zoomed coordinates
    zoomed_x, zoomed_y = canvas_to_full_img_coords(canvas, original_image, image, zoom_level, zoom_center, canvas_x, canvas_y)

    # Original image coordinates
    if zoomed_x is None or zoomed_y is None:
        original_x, original_y = None, None
    else:
        original_x = int(zoomed_x * zoom_level)
        original_y = int(zoomed_y * zoom_level)

    canvas_coords_label.config(text=f"Canvas Coords: {canvas_x}, {canvas_y}")
    image_coords_label.config(text=f"Image Coords: {img_x}, {img_y}")
    other_image_coords_label.config(text=f"Other Image Coords: {adj_x}, {adj_y}")
    zoomed_coords_label.config(text=f"Zoomed Coords: {zoomed_x}, {zoomed_y}")
    original_coords_label.config(text=f"Original Coords: {original_x}, {original_y}")

# Create labels for displaying coordinates
canvas_coords_label = tk.Label(root, text="Canvas Coords: ")
canvas_coords_label.pack()

image_coords_label = tk.Label(root, text="Image Coords: ")
image_coords_label.pack()

other_image_coords_label = tk.Label(root, text="Other Image Coords: ")
other_image_coords_label.pack()

zoomed_coords_label = tk.Label(root, text="Zoomed Coords: ")
zoomed_coords_label.pack()

original_coords_label = tk.Label(root, text="Original Coords: ")
original_coords_label.pack()

# Bind the mouse motion event to the canvas
canvas.bind("<Motion>", display_mouse_position)
mask_canvas.bind("<Motion>", display_mouse_position)

# Run the application
root.mainloop()
