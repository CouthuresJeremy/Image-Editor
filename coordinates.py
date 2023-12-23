
def get_image_position_in_canvas(canvas, img_size):
    """
    Calculate the position of the image in the canvas.
    Returns the top-left corner (x, y).
    """
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    x = (canvas_width - img_size[0]) // 2
    y = (canvas_height - img_size[1]) // 2
    return x, y

def canvas_coords_to_img_coords(canvas, image, x, y):
    """
    Convert canvas coordinates to image coordinates.
    Returns the image coordinates (x, y).
    """
    img_x, img_y = get_image_position_in_canvas(canvas, image.size)
    # Adjust the coordinates relative to the image position
    adj_x = x - img_x
    adj_y = y - img_y
    # Ensure adjusted coordinates are within the image boundaries
    if 0 <= adj_x < image.size[0] and 0 <= adj_y < image.size[1]:
        return adj_x, adj_y
    return None, None

def full_img_to_canvas_coords(x, y):
    global image, mask_canvas
    img_x, img_y = get_image_position_in_canvas(mask_canvas, image.size)
    # Adjust the coordinates relative to the image position
    adj_x = x - img_x
    adj_y = y - img_y
    return adj_x, adj_y

def img_coords_to_resized_img_coords(x, y):
    global image
    resized_x = int(x * image.width / original_image.size[0])
    resized_y = int(y * image.height / original_image.size[1])
    print(f"{x}, {y} -> {resized_x}, {resized_y}")
    print(f"{x*min_scale_factor}, {y*min_scale_factor}")
    return resized_x, resized_y

def resized_img_coords_to_img_coords(original_image, image, x, y):
    img_x = int(x * original_image.size[0] / image.width)
    img_y = int(y * original_image.size[1] / image.height)
    return img_x, img_y

def center_coords(image, x, y):
    center_x = x - image.width / 2
    center_y = y - image.height / 2
    return center_x, center_y

def unzoom_coords(x, y, zoom_level):
    unzoom_x = x / zoom_level
    unzoom_y = y / zoom_level
    return unzoom_x, unzoom_y

def canvas_to_full_img_coords(canvas, original_image, image, zoom_level, zoom_center, x, y):
    x, y = canvas_coords_to_img_coords(canvas, image, x, y)
    if x is None or y is None:
        return None, None
    x, y = max(0, x), max(0, y)
    x, y = min(x, image.width), min(y, image.height)
    center_x, center_y = center_coords(image, x, y)
    unzoom_x, unzoom_y = unzoom_coords(center_x, center_y, zoom_level)
    img_x, img_y = resized_img_coords_to_img_coords(original_image, image, unzoom_x, unzoom_y)
    full_img_x, full_img_y = img_x + zoom_center[0], img_y + zoom_center[1]
    return int(full_img_x), int(full_img_y)