import pandas as pd
import os
import re
import numpy as np
import cv2
from PIL import Image
from sklearn.cluster import KMeans


def calculate_touches_in_zones(image_path, total_touches):
    # Load the heatmap image
    heatmap = Image.open(image_path)

    # Ensure the image is in RGB format
    heatmap = heatmap.convert('RGB')

    # Convert to numpy array
    heatmap_np = np.array(heatmap)

    # Reshape the image data for clustering
    height, width, channels = heatmap_np.shape
    pixel_data = heatmap_np.reshape((-1, 3))

    # Apply KMeans clustering to segment the image into 7 clusters (for 7 intensity levels)
    kmeans = KMeans(n_clusters=7, random_state=42).fit(pixel_data)

    # Reshape the clustered labels back to the image shape
    clustered = kmeans.labels_.reshape(height, width)

    # Sort clusters by intensity (optional: sort by mean color intensity)
    cluster_means = kmeans.cluster_centers_.mean(axis=1)
    intensity_order = np.argsort(cluster_means)

    # Reassign clusters based on intensity order (0 to 6, from low to high intensity)
    segmented_map = np.zeros_like(clustered)
    for i, cluster in enumerate(intensity_order):
        segmented_map[clustered == cluster] = i

    # Calculate the area (number of pixels) in each intensity region
    areas = [np.sum(segmented_map == i) for i in range(7)]

    # Calculate the total area
    total_area = sum(areas)

    # Define weightings for each intensity level (refined based on observation)
    weights = [0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0]  # These can be adjusted based on the characteristics of your heatmap

    # Calculate touches for each intensity level
    touches = [(areas[i] / total_area) * total_touches * weights[i] for i in range(7)]

    # Normalize to ensure the sum of touches matches the total
    touch_sum = sum(touches)
    touches = [t * total_touches / touch_sum for t in touches]

    # Define zones of interest (polygons)
    zone1 = np.array([[0, 42], [330, 43], [328, 12], [3, 9]])
    zone2 = np.array([[1, 169], [325, 168], [325, 203], [2, 203]])

    # Combine zones into a single mask
    zones = [zone1, zone2]

    # Create a mask for the zones of interest
    zone_mask = np.zeros((height, width), dtype=np.uint8)

    for zone in zones:
        cv2.fillPoly(zone_mask, [zone], 1)

    # Now count the touches within the zones for each intensity level
    touches_in_zones = 0

    # For each intensity level (0 to 6), check which pixels in the segmented map are inside the zones
    for intensity in range(7):
        # Create a mask for the current intensity level
        intensity_mask = (segmented_map == intensity)

        # Combine the intensity mask with the zone mask
        combined_mask = intensity_mask & zone_mask.astype(bool)

        # Count the number of pixels within the zones for this intensity
        pixels_in_zone = np.sum(combined_mask)

        # Add the corresponding touches for this intensity (weighted by the intensity)
        touches_in_zones += (pixels_in_zone / total_area) * total_touches * weights[intensity]

    # Normalize to ensure the sum of touches matches the total
    touches_in_zones *= total_touches / touch_sum

    return int(touches_in_zones)


def process_heatmap_row(row):
    team = row['team']
    date = pd.to_datetime(row['date']).strftime('%d-%b-%y')

    # Construct the file search pattern
    directory = './prem/data/heatmaps/'
    pattern = f"{team}_{date}_heatmap_"
    # Search for the correct file in the directory
    for file_name in os.listdir(directory):
        if file_name.startswith(pattern) and file_name.endswith('.png'):
            # Extract the total touches from the filename using regex
            match = re.search(r'_heatmap_(\d+).png', file_name)
            if match:
                total_touches = int(match.group(1))
                # Construct the full file path
                file_path = os.path.join(directory, file_name)

                # Calculate wide touches using the previously defined function
                wide_touches = calculate_touches_in_zones(file_path, total_touches)

                # Calculate the percentage of wide touches
                wide_touches_pc = (wide_touches / total_touches) * 100

                # Return the results as a dictionary
                return pd.Series({
                    'total_touches': total_touches,
                    'wide_touches': wide_touches,
                    'wide_touches_pc': wide_touches_pc
                })

    # If no matching file is found, return NaN values
    return pd.Series({
        'total_touches': None,
        'wide_touches': None,
        'wide_touches_pc': None
    })

