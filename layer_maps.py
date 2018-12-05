#!/usr/bin/env python

from gimpfu import *
import os
import re


class FilePathHandler:
    # Initialize the values for the path to the info file and save the full paths for the .png file(s)
    info_file_path = ""
    png_files_path = []

    def __init__(self, original_image, dir_path):
        info_file = ""
        png_files = []

        # Iterate over the files in the directory to find the .info and .png files
        for file in os.listdir(dir_path):
            info_match_found = re.match(r'.*?.info', file)
            png_match_found = re.match(r'.*?.png', file)

            # See if a valid match is found for the .png files or the .info file
            if png_match_found and original_image.replace('\\', '/') != dir_path + '/' + file:
                png_files.append(file)

            if info_match_found:
                info_file = file

        # Create and assign the path to each file
        if info_file == "":
            self.info_file_path = ""
        else:
            self.info_file_path = dir_path + '/' + info_file

        for i in range(0, len(png_files)):
            self.png_files_path.append(dir_path + '/' + png_files[i])


def get_dir_path(image_path):
    # Specify the delimiters of the path in order to retrieve the directory path
    delimiter1 = image_path.find("\\Documents\\")
    delimiter2 = image_path.find('\\', delimiter1 + 11)
    dir_path = image_path[:delimiter2]
    dir_path = dir_path.replace('\\', '/')

    # Return the path to the needed directory
    return dir_path


def sort_png_files_by_level(png_files):  # Only pass in the non-base image .png files
    # Find the map height bounds by looking at the end of the file name
    map_bounds = []

    # Iterate over the .png files and save the lower bound height to a list
    for i in range(0, len(png_files)):
        matched = re.search(r'[a-z][_]\d\D', png_files[i])
        num_start = matched.start() + 2
        num_end = png_files[i].find('_', num_start + 1)
        map_bounds.append(float(png_files[i][num_start:num_end]))

    # Sort the list in ascending order using the map_bounds list as the guide (Using Bubble Sort)
    for j in range(0, len(map_bounds) - 1):
        for k in range(0, j):
            if map_bounds[k] > map_bounds[k + 1]:
                temp1 = map_bounds[k]
                temp2 = png_files[k]
                map_bounds[k] = map_bounds[k + 1]
                png_files[k] = png_files[k + 1]
                map_bounds[k + 1] = temp1
                png_files[k + 1] = temp2

    # Return the freshly sorted list of png files
    return png_files


def get_offsets(offset_file, num_files):
    # Initialize a list to hold offsets
    offset_list = []

    # Open the file for reading and read the first (1 + 5) = 6 lines to skip over header information
    file = open(offset_file, 'r')
    line = file.readline()

    for i in range(0, 5):
        line = file.readline()

    # Locate the x and y position based on the first instance of the : (colon) character
    x_start = line.find(":")
    y_start = line.find(' ', x_start + 2)
    y_end = line.find('\n', y_start + 1)

    # Set the values of the offset and add them to the list
    base_image_offset_x = int(line[x_start + 2: y_start])
    base_image_offset_y = int(line[y_start + 1: y_end])
    offset_list.append([base_image_offset_x, base_image_offset_y])

    # Iterate over the remaining .png files to get their offsets
    for j in range(0, num_files):
        print("Inside loop, j = ", j)
        print("list after jth pass: ", offset_list)
        file.readline()  # This line is empty (whitespace)
        line = file.readline()
        x_start = line.find(":")
        y_start = line.find(' ', x_start + 2)
        y_end = line.find('\n', y_start + 1)

        offset_x = int(line[x_start + 2: y_start])
        offset_y = int(line[y_start + 1: y_end])
        offset_list.append([offset_x, offset_y])

    file.close()

    # Return the offset list
    return offset_list


def run_script(timg, tdrw):
    # Set the image and the drawable
    img = gimp.image_list()[0]
    draw = pdb.gimp_image_get_active_drawable(img)

    # Set the height and width of the canvas, which will be eventually resized
    set_height = 3000
    set_width = 3000

    # Resize the image canvas
    pdb.gimp_image_resize(img, set_width, set_height, 0, 0)

    # Create a list to hold all the layers and add the base layer (draw in this case)
    layer_list = [draw]

    # Check if the image is rgb, if so, convert it to gray scale
    if pdb.gimp_drawable_is_rgb(draw):
        pdb.gimp_image_convert_grayscale(img)

    # Get the path to the image that is opened
    map_path = pdb.gimp_image_get_filename(img)

    # Get the path to the directory that we need to pull the additional .png and info file(s) from
    # Also get the full file paths for the .info and .png files and save them
    cwd_path = get_dir_path(map_path)
    file_paths = FilePathHandler(map_path, cwd_path)  # Pass in map_image_name, not the path
    offset_path = file_paths.info_file_path  # This is a string
    image_paths = file_paths.png_files_path  # This is a list

    # Check to see if there are any images, if not, display the problem and terminate the program
    if len(image_paths) == 0:
        pdb.gimp_message("No additional .png map files found to overlay!")  # Change to message box
        return

    # Sort the .png files based on their lower level bound
    image_paths = sort_png_files_by_level(image_paths)

    # Load the images to layers and insert the layers
    for i in range(0, len(image_paths)):
        # Load the layer and add it to the image
        layer = pdb.gimp_file_load_layer(img, image_paths[i])
        pdb.gimp_image_add_layer(img, layer, 0)

        # Make the active layer the drawable and place it into the layer list
        active_layer = pdb.gimp_image_get_active_drawable(img)
        layer_list.append(active_layer)

        # Move the layer to the bottom left corner
        pdb.gimp_layer_translate(active_layer, 0, set_height - active_layer.height)

    # Move the original image to the bottom left corner and resize the layers
    pdb.gimp_layer_translate(layer_list[0], 0, set_height - layer_list[0].height)
    pdb.gimp_image_resize_to_layers(img)

    # Get the list of offsets for the file
    offset_list = get_offsets(offset_path, len(image_paths))  # This is a list, len(offset_list) = len(layer_list)

    # Move each layer, based on the base layer's offset
    bl_offset_x = offset_list[0][0]  # Base layer offset x
    bl_offset_y = offset_list[0][1]  # Base layer offset y

    for j in range(1, len(layer_list)):
        pdb.gimp_layer_translate(layer_list[j], bl_offset_x - offset_list[j][0], abs(bl_offset_y - offset_list[j][1]))

    pdb.gimp_image_resize_to_layers(img)

    # Change the opacity of each layer except the base layer to 0%
    for k in range(1, len(layer_list)):
        pdb.gimp_layer_set_opacity(layer_list[k], 0.0)

    # Set the base layer to be the active layer
    pdb.gimp_image_set_active_layer(img, layer_list[0])


register(
    "layer_maps",
    "Takes the different slices of the store map and places them on top of one another via layers",
    "This plugin runs automatically upon execution and requires the base map to run",
    "Joey Harrison",
    "J.H.",
    "11/18",
    "<Image>/Tools/Transform Tools/Map Cleanup/_Layer Maps",
    "RGB*, GRAY*",
    [],
    [],
    run_script)

main()
