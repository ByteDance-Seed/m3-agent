# Copyright (2025) Bytedance Ltd. and/or its affiliates

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import json
import logging
import argparse
import glob
import pickle

from mmagent.videograph import VideoGraph
from mmagent.utils.video_processing import process_video_clip
from mmagent.face_processing import process_faces
from mmagent.voice_processing import process_voices
from mmagent.memory_processing_qwen import process_memories, generate_memories

logger = logging.getLogger(__name__)
processing_config = json.load(open("configs/processing_config.json"))
memory_config = json.load(open("configs/memory_config.json"))

preprocessing = []

def process_segment(
    video_graph,
    base64_video,
    base64_frames,
    base64_audio,
    clip_id,
    sample,
    clip_path
):
    save_path = sample["intermediate_path"]
    
    id2voices = process_voices(
        video_graph,
        base64_audio,
        base64_video,
        save_path=os.path.join(save_path, f"clip_{clip_id}_voices.json"),
        preprocessing=[],
    )

    id2faces = process_faces(
        video_graph,
        base64_frames,
        save_path=os.path.join(save_path, f"clip_{clip_id}_faces.json"),
        preprocessing=[],
    )

    episodic_memories, semantic_memories = generate_memories(
        base64_frames,
        id2faces,
        id2voices,
        clip_path,
    )

    process_memories(video_graph, episodic_memories, clip_id, type="episodic")
    process_memories(video_graph, semantic_memories, clip_id, type="semantic")

def streaming_process_video(video_graph, sample):
    """Process video segments at specified intervals with given fps.

    Args:
        video_graph (VideoGraph): Graph object to store video information
        video_path (str): Path to the video file or directory containing clips
        interval_seconds (float): Time interval between segments in seconds
        fps (float): Frames per second to extract from each segment

    Returns:
        None: Updates video_graph in place with processed segments
    """
    clips = glob.glob(sample["clip_path"] + "/*")
    for clip_path in clips:
        clip_id = int(clip_path.split("/")[-1].split(".")[0])
        base64_video, base64_frames, base64_audio = process_video_clip(clip_path)

        # Process frames for this interval
        if base64_frames:
            process_segment(
                video_graph,
                base64_video,
                base64_frames,
                base64_audio,
                clip_id,
                sample,
                clip_path
            )
    
    video_graph.refresh_equivalences()
    with open(sample["mem_path"], "wb") as f:
        pickle.dump(video_graph, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_file", type=str, default="data/data.jsonl")
    args = parser.parse_args()
    video_inputs = []
    
    with open(args.data_file, "r") as f:
        for line in f:
            sample = json.loads(line)
            if not os.path.exists(sample["mem_path"]):
                video_graph = VideoGraph(**memory_config)
                streaming_process_video(video_graph, sample)
