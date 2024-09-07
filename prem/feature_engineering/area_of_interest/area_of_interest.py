import os
import numpy as np
import pandas as pd
from PIL import Image
import shutil  # Import shutil for moving files
import supervision as sv
from ultralytics import YOLO
from supervision.detection.overlap_filter import box_non_max_merge

# Define constants
MODEL_PATH = 'prem/data/models/who_scored_weights.pt'
MISSING_DETS_FOLDER = 'prem/data/images/missing_dets/'

# Areas of interest polygons
areas_of_interest = [
    np.array([[0, 82], [674, 82], [674, 0], [0, 0]]),
    np.array([[0, 328], [674, 328], [674, 398], [0, 398]])
]

# Initialize the model
model = YOLO(MODEL_PATH)


# Helper Functions
def parse_filename(filename):
    """Parse the image filename to extract metadata."""
    basename = os.path.splitext(filename)[0]
    parts = basename.split('_')

    return {
        'home_team': parts[0],
        'away_team': parts[1],
        'date_time': parts[2],
        'event_type': '_'.join(parts[3:-2]),
        'home_data': int(parts[-2]),
        'away_data': int(parts[-1])
    }


def log_missing_detections(image_path, missing_dets_folder=MISSING_DETS_FOLDER):
    """Log and move images with missing detections."""
    if not os.path.exists(missing_dets_folder):
        os.makedirs(missing_dets_folder)
    filename = os.path.basename(image_path)
    destination = os.path.join(missing_dets_folder, filename)
    shutil.move(image_path, destination)
    print(f"Logged missing detections for: {filename}")


def merge_detections(detections, merge_groups):
    """Merge detections based on non-max merge groups."""
    if len(detections) == 0 or len(merge_groups) == 0:
        return sv.Detections.empty()

    merged_boxes = []
    merged_confidences = []
    merged_class_ids = []

    for group in merge_groups:
        group_boxes = detections.xyxy[group]
        merged_box = np.mean(group_boxes, axis=0)

        group_confidences = detections.confidence[group]
        merged_confidence = np.max(group_confidences)

        merged_class_id = detections.class_id[group[0]]

        merged_boxes.append(merged_box)
        merged_confidences.append(merged_confidence)
        merged_class_ids.append(merged_class_id)

    return sv.Detections(
        xyxy=np.array(merged_boxes),
        confidence=np.array(merged_confidences),
        class_id=np.array(merged_class_ids)
    )


def count_detections(image_path):
    """Count the number of home and away detections in areas of interest."""
    image = Image.open(image_path)
    image = np.array(image)

    if image.dtype != np.uint8:
        image = image.astype(np.uint8)

    results = model(image, imgsz=960, verbose=False, conf=0.25)[0]
    detections = sv.Detections.from_ultralytics(results)

    home_detections = detections[(detections.class_id == 0) & (detections.confidence >= 0.6)]
    away_detections = detections[(detections.class_id == 1) & (detections.confidence >= 0.6)]

    if len(home_detections) == 0 and len(away_detections) == 0:
        log_missing_detections(image_path)
        return 0, 0

    # Apply Non-Max Merge (NMM)
    home_detections_nmm = process_merge(home_detections)
    away_detections_nmm = process_merge(away_detections)

    # Initialize counters
    total_home, total_away = 0, 0

    # Create zones using the image resolution
    zones = [sv.PolygonZone(polygon=polygon) for polygon in areas_of_interest]

    # Count detections within the zones
    for zone in zones:
        if home_detections_nmm:
            total_home += np.sum(zone.trigger(detections=home_detections_nmm))
        if away_detections_nmm:
            total_away += np.sum(zone.trigger(detections=away_detections_nmm))

    return total_home, total_away


def process_merge(detections):
    """Apply the Non-Max Merge (NMM) on detections."""
    if len(detections) > 0:
        predictions = np.hstack((detections.xyxy, detections.confidence[:, None], detections.class_id[:, None]))
        merge_groups = box_non_max_merge(predictions, iou_threshold=0.05)
        return merge_detections(detections, merge_groups)
    else:
        return sv.Detections.empty()


def process_directory(directory_path):
    """Process all images in a directory and build a dataframe."""
    data = {}
    file_count = 0
    for filename in os.listdir(directory_path):
        if filename.endswith('.png'):
            file_count += 1
            print(f"Processing file {file_count}: {filename}")
            image_path = os.path.join(directory_path, filename)
            metadata = parse_filename(filename)

            # Create a unique key for the game
            game_key = (metadata['home_team'], metadata['away_team'], metadata['date_time'])
            # Count detections
            total_home, total_away = count_detections(image_path)

            # Initialize the game entry if it doesn't exist
            if game_key not in data:
                data[game_key] = {
                    'home_team': metadata['home_team'],
                    'away_team': metadata['away_team'],
                    'date_time': metadata['date_time']
                }

            # Store event type counts and wide event counts in the game entry
            data[game_key][f"wide_{metadata['event_type']}_home"] = total_home
            data[game_key][f"wide_{metadata['event_type']}_away"] = total_away
            data[game_key][f"total_{metadata['event_type']}_home"] = metadata['home_data']
            data[game_key][f"total_{metadata['event_type']}_away"] = metadata['away_data']

    df = pd.DataFrame.from_dict(data, orient='index')
    df.reset_index(drop=True, inplace=True)
    return df


def prepare_dataframe(df):
    """Prepare the dataframe by renaming, reshaping, and calculating percentages."""
    # Add 'home' column to indicate if the team is playing at home
    df['home_flag'] = 1

    # Convert datetime and extract the date
    df['datetime'] = pd.to_datetime(df['date_time'], format='%d-%b-%y')
    df['date'] = df['datetime'].dt.date
    df.drop('date_time', axis=1, inplace=True)

    # Rename columns
    df = df.rename(columns={'home_team': 'team', 'away_team': 'opp'})

    # Create the opponent DataFrame
    df_opp = swap_team_opp(df)

    # Concatenate the original and opponent DataFrames
    df_final = pd.concat([df, df_opp], ignore_index=True)

    # Calculate percentages
    df_final = calculate_percentages(df_final)

    return df_final


def swap_team_opp(df):
    """Swap team and opponent in the DataFrame for reshaping."""
    df_opp = df.copy()
    df_opp['team'], df_opp['opp'] = df['opp'], df['team']
    df_opp['home_flag'] = 0
    return df_opp


def calculate_percentages(df):
    """Calculate percentage stats for the wide columns."""
    for col in df.columns:
        if col.startswith('wide_'):
            total_col = col.replace('wide_', 'total_')
            if total_col in df.columns:
                percentage_col = col.replace('wide_', 'pct_wide_')
                df[percentage_col] = (df[col] / df[total_col]) * 100

        elif col.startswith('conc_wide_'):
            total_col = col.replace('conc_wide_', 'conc_total_')
            if total_col in df.columns:
                percentage_col = col.replace('conc_wide_', 'conc_pct_wide_')
                df[percentage_col] = (df[col] / df[total_col]) * 100

    # Special handling for aerial duels
    if 'wide_aerial_duels' in df.columns and 'conc_wide_aerial_duels' in df.columns:
        df['total_aerial_duels_combined'] = df['total_aerial_duels'] + df['conc_total_aerial_duels']
        df['pct_wide_aerial_duels'] = (df['wide_aerial_duels'] / df['total_aerial_duels_combined']) * 100
        df['conc_pct_wide_aerial_duels'] = (df['conc_wide_aerial_duels'] / df['total_aerial_duels_combined']) * 100

    return df


def process_images_to_dataframe(directory_path):
    # Process the new data from images
    df = process_directory(directory_path)
    df = prepare_dataframe(df)

    # Check if the historical data file exists
    csv_path = 'prem/data/processed/area_of_interest_processed.csv'
    if os.path.exists(csv_path):
        # Load the existing historical data
        hist_df = pd.read_csv(csv_path)
        # Concatenate the historical and new data
        df_final = pd.concat([hist_df, df], ignore_index=True)
    else:
        # If no existing file, only use the new data
        df_final = df

    # Drop duplicates based on 'team' and 'date' columns
    df_final.drop_duplicates(subset=['team', 'date'], inplace=True)

    # Save the updated DataFrame back to the CSV file
    df_final.to_csv(csv_path, index=False)

    return df_final
