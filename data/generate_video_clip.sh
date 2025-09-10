#!/bin/bash

# This script is running in m3-agent/data directory where contains original videos

# Function to format time in hours, minutes, and seconds
format_time() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))
    
    if [[ $hours -gt 0 ]]; then
        printf "%dh %dm %ds" $hours $minutes $secs
    elif [[ $minutes -gt 0 ]]; then
        printf "%dm %ds" $minutes $secs
    else
        printf "%ds" $secs
    fi
}

# Directory containing the videos
VIDEO_DIR="videos/robot"
CLIP_DIR="clips/robot"

# Array of video files to process. FIXME: add args point to dataset dir rather than hardcode the filenames  
video_files=("gym_01" "gym_02" "gym_03" "gym_04")

# Start timing the entire process
total_start_time=$(date +%s)

# Display header
printf "\n%-10s | %-15s | %-15s | %-15s | %-15s\n" "Video" "Duration" "Segments" "Process Time" "Status"
printf "%-10s-+-%-15s-+-%-15s-+-%-15s-+-%-15s\n" "----------" "---------------" "---------------" "---------------" "---------------"

# Process each video file
for video_base in "${video_files[@]}"; do
    # Start timing this video
    video_start_time=$(date +%s)
    
    # Set input and output paths
    input="$VIDEO_DIR/${video_base}.mp4"
    
    # Create output directory if it doesn't exist
    mkdir -p "$CLIP_DIR/$video_base"
    
    # Get video duration
    duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$input")
    duration_seconds=$(echo "$duration" | awk '{print int($1)}')
    
    # Calculate number of segments
    segments=$((duration_seconds / 30 + 1))
    
    # Process each segment (with less verbose output)
    for ((i=0; i<segments; i++)); do
        start=$((i * 30))
        output="$CLIP_DIR/$video_base/$i.mp4"
        
        # Use -loglevel warning to reduce ffmpeg output
        ffmpeg -loglevel warning -ss $start -i "$input" -t 30 -c copy "$output"
        
        # Show progress indicator
        printf "\rProcessing %s: [%d/%d] segments" "$video_base" $((i+1)) $segments
    done
    
    # Calculate processing time for this video
    video_end_time=$(date +%s)
    video_process_time=$((video_end_time - video_start_time))
    formatted_process_time=$(format_time $video_process_time)
    
    # Clear the progress line
    printf "\r%-80s\r" " "
    
    # Print the result in table format
    printf "%-10s | %-15s | %-15d | %-15s | %-15s\n" \
           "$video_base" \
           "$(format_time $duration_seconds)" \
           "$segments" \
           "$formatted_process_time" \
           "Completed"
done

# Calculate total processing time
total_end_time=$(date +%s)
total_process_time=$((total_end_time - total_start_time))
formatted_total_time=$(format_time $total_process_time)

# Print summary
printf "%-10s-+-%-15s-+-%-15s-+-%-15s-+-%-15s\n" "----------" "---------------" "---------------" "---------------" "---------------"
printf "\nAll videos processed successfully!\n"
printf "Total processing time: %s\n\n" "$formatted_total_time"


