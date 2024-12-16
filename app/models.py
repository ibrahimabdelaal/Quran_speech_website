# Standard library imports
import os
import io
import subprocess
import tempfile
from base64 import b64decode
from io import BytesIO
import shutil

# Third-party imports
import numpy as np
import pandas as pd
import torch
import torchaudio
import jiwer
from pydub import AudioSegment
from datasets import Dataset, load_dataset
from transformers import Wav2Vec2Processor, Wav2Vec2ProcessorWithLM, Wav2Vec2ForCTC
from IPython.display import Javascript

# Database setup
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

def load_models():
    print("Loading models...")
    LMprocessor ='' #Wav2Vec2ProcessorWithLM.from_pretrained('IbrahimSalah/Wav2vecXXl_quran_syllables')
    processor=Wav2Vec2Processor.from_pretrained('IbrahimSalah/Wav2vecXXl_quran_syllables')
    model = Wav2Vec2ForCTC.from_pretrained("IbrahimSalah/Wav2vecXXl_quran_syllables")
    print("Models loaded successfully.")
    return processor, model,LMprocessor
processor, model,LMprocessor = load_models()

class Surah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    surah_number = db.Column(db.Integer, nullable=False)
    surah_name = db.Column(db.String, nullable=False)
    verses = db.relationship('Verse', backref='surah', lazy=True)

class Verse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    surah_id = db.Column(db.Integer, db.ForeignKey('surah.id'), nullable=False)
    verse_number = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    syllables = db.Column(db.Text, nullable=True)
    audio_file = db.Column(db.String, nullable=True)  # New column for audio recordings


def transcribe_audio_file_withoutLMHead(audio_file):
        dftest = pd.DataFrame(columns=['audio'])
        dftest['audio']=[audio_file]  
        test_dataset1 = Dataset.from_pandas(dftest)
        test_dataset = test_dataset1.map(speech_file_to_array_fn)
        inputs = processor(test_dataset["audio"], sampling_rate=16_000, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = model(inputs.input_values).logits
   
        pred_ids = torch.argmax(logits, dim=-1)
        transcription = processor.batch_decode(pred_ids)[0]   
        
        return transcription
def transcribe_audio_file(audio_file):
    try:
        print(f"Attempting to transcribe: {audio_file}")
        dftest = pd.DataFrame(columns=['audio'])
        dftest['audio'] = [audio_file]  
        test_dataset1 = Dataset.from_pandas(dftest)
        test_dataset = test_dataset1.map(speech_file_to_array_fn)
        inputs = LMprocessor(test_dataset["audio"], sampling_rate=16_000, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = model(inputs.input_values).logits
        
        transcription = processor.batch_decode(logits.numpy()).text
        return transcription[0]
    except Exception as e:
        print(f"Error in transcribe_audio_file: {str(e)}")
        raise

def speech_file_to_array_fn(batch):
    try:
        print(f"Loading audio file: {batch['audio']}")
        speech_array, sampling_rate = torchaudio.load(batch["audio"])
        print(f"Loaded audio file. Shape: {speech_array.shape}, Sampling rate: {sampling_rate}")
        
        resampler = torchaudio.transforms.Resample(sampling_rate, 16_000)
        batch["audio"] = resampler(speech_array).squeeze().numpy()
        print(f"Resampled audio shape: {batch['audio'].shape}")
        return batch
    except Exception as e:
        print(f"Error in speech_file_to_array_fn: {str(e)}")
        raise
import subprocess

import os
import subprocess
import shutil

def convert_weba_to_wav(input_path, output_path):
    ffmpeg_path = r"app\ffmpeg.exe"  # Update this path to the correct location of ffmpeg.exe

    # Validate file before processing
    if not validate_file(input_path):
        return False

    # Copy file to ensure proper writing
    input_path = copy_to_temp(input_path)

    try:
        print(f"Attempting to convert {input_path} to {output_path}")

        result = subprocess.run(
            [ffmpeg_path, '-i', input_path, output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )

        print("FFmpeg Output (stdout):", result.stdout)
        if result.stderr:
            print("FFmpeg Error (stderr):", result.stderr)

        print("Conversion successful")
        return True

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg command failed: {str(e)}")
        print("FFmpeg Error Details:", e.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

def debug_file(file_path):
    if os.path.exists(file_path):
        print(f"File exists: {file_path}")
        print(f"File size: {os.path.getsize(file_path)} bytes")
        with open(file_path, "rb") as f:
            print(f"File first 100 bytes: {f.read(100)}")
    else:
        print(f"File does not exist: {file_path}")


def validate_file(file_path):
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return False
    if os.path.getsize(file_path) == 0:
        print(f"File is empty: {file_path}")
        return False
    print(f"File is valid: {file_path}, Size: {os.path.getsize(file_path)} bytes")
    return True


def copy_to_temp(input_path):
    new_path = r'app\temp\audio'
    shutil.copy(input_path, new_path)
    print(f"Copied file to {new_path}")
    return new_path

def highlight_alignment(true_text, recognized_text):
    """
    Use jiwer alignment to highlight differences between true and recognized texts.
    """
    print("Highlighting text with alignment...")

    # Process the words to get alignment chunks
    alignment_result = jiwer.process_words(true_text, recognized_text)
    alignment_chunks = alignment_result.alignments
    alignment_chunks=alignment_chunks[0]

    # Flatten the alignment chunks if necessary
    # if isinstance(alignment_chunks, list):
    #     alignment_chunks = [chunk for sublist in alignment_chunks for chunk in sublist]

    highlighted_words = []
    true_list=true_text[0].split()
    transcription_list=recognized_text[0].split()

    # Iterate over alignment chunks and format based on type
    for chunk in alignment_chunks:
        if chunk.type == 'equal':
            highlighted_word = f"<span class='highlightright' title='Green: Right'>{true_list[chunk.ref_start_idx:chunk.ref_end_idx]}</span>"
            highlighted_words.append(highlighted_word)
        elif chunk.type == 'substitute':
            highlighted_word = f"<span class='highlightWrong' title='Red: Substituted'>{true_list[chunk.ref_start_idx:chunk.ref_end_idx]}</span>"
            highlighted_words.append(highlighted_word)
        elif chunk.type == 'delete':
            highlighted_word = f"<span class='highlighdeleted' title='Blue: Deleted'>{true_list[chunk.ref_start_idx:chunk.ref_end_idx]}</span>"
            highlighted_words.append(highlighted_word)
        elif chunk.type == 'insert':
            highlighted_word = f"<span class='highlightInserted' title='Yellow: Inserted'>{true_list[chunk.ref_start_idx:chunk.ref_end_idx]}</span>"
            highlighted_words.append(highlighted_word)
            # Print the highlighted word for inserted chunks

    # Join highlighted words into a single string
    aligned_text = ' '.join(highlighted_words)
    print(f"Final aligned text: {aligned_text}")  # Print the final aligned text
    
    return aligned_text


def highlight_alignment_real_time(true_text, recognized_text):
    """
    Highlights the Surah text based on alignment results between the true text and recognized text.
    """
    print("Highlighting Surah text with alignment...")

    # Compute alignment using jiwer
    alignment_result = jiwer.process_words(true_text, recognized_text)
    alignment_chunks = alignment_result.alignments[0]  # Assuming first alignment set

    # Split the true Surah text into words for highlighting
    true_list = true_text[0].split()  # Surah text as a list of words
    highlighted_words = [""] * len(true_list)  # Prepopulate with placeholders for the Surah words

    # Iterate over alignment chunks and map highlights to the true Surah words
    for chunk in alignment_chunks:
        if chunk.type == 'equal':
            # Highlight correct words in green
            for idx in range(chunk.ref_start_idx, chunk.ref_end_idx):
                highlighted_words[idx] = f"<span class='highlightright' title='Correct'>{true_list[idx]}</span>"
        elif chunk.type == 'substitute':
            # Highlight substituted words in red
            for idx in range(chunk.ref_start_idx, chunk.ref_end_idx):
                highlighted_words[idx] = f"<span class='highlightWrong' title='Substituted'>{true_list[idx]}</span>"
        elif chunk.type == 'delete':
            # Highlight deleted words in blue
            for idx in range(chunk.ref_start_idx, chunk.ref_end_idx):
                highlighted_words[idx] = f"<span class='highlighdeleted' title='Missed'>{true_list[idx]}</span>"
        elif chunk.type == 'insert':
            # Handle insertions (add an empty highlight to mark where extra words are detected)
            inserted_text = " ".join(recognized_text[0].split()[chunk.hyp_start_idx:chunk.hyp_end_idx])
            highlighted_words.insert(chunk.ref_end_idx, f"<span class='highlightInserted' title='Inserted'>{inserted_text}</span>")

    # Replace unhighlighted placeholders with the original words
    for idx, word in enumerate(true_list):
        if highlighted_words[idx] == "":
            highlighted_words[idx] = word

    # Join the highlighted words into the final aligned text
    aligned_text = " ".join(highlighted_words)
    print(f"Final highlighted Surah text: {aligned_text}")

    return aligned_text



def highlight_alignment_real_time_2(true_syllables, recognized_syllables,map_index_dict):
    """
    Compares and highlights syllables based on alignment between the true and recognized syllables.

    Args:
        true_syllables (list): List of syllables in the true Surah text.
        recognized_syllables (list): List of syllables in the recognized text.

    Returns:
        dict: A dictionary containing the syllables' indexes and their highlight statuses.
    """

    print("Highlighting Surah text with alignment...")

    # Compute alignment using jiwer
    alignment_result = jiwer.process_words(true_syllables, recognized_syllables,)
    alignment_chunks = alignment_result.alignments[0]  # Assuming first alignment set

    # Prepare the result as a list of dictionaries
    syllable_highlights = []

    # Iterate over alignment chunks and map highlights to the true Surah syllables
    last_index=0
    for chunk in alignment_chunks:
       
        ## get the last index in  the hypothesis
        if chunk.hyp_end_idx>last_index:
            last_index=chunk.hyp_end_idx



        if chunk.type == 'equal':
            # Correct syllables
            for idx in range(chunk.ref_start_idx, chunk.ref_end_idx):
                syllable_highlights.append({"index": map_index_dict[idx], "status": "correct"})
        elif chunk.type == 'substitute':
            # Substituted syllables
            for idx in range(chunk.ref_start_idx, chunk.ref_end_idx):
                syllable_highlights.append({"index": map_index_dict[idx], "status": "wrong"})
        elif chunk.type == 'delete':
            # Deleted syllables
            for idx in range(chunk.ref_start_idx, chunk.ref_end_idx):
                syllable_highlights.append({"index": map_index_dict[idx], "status": "wrong"})
        elif chunk.type == 'insert':
            # Inserted syllables (these don't correspond to true syllables)
            inserted_indices = range(chunk.hyp_start_idx, chunk.hyp_end_idx)
            for hyp_idx in inserted_indices:
                syllable_highlights.append({"index": None, "status": "wrong"})

    #print(f"Final syllable highlights: {syllable_highlights}")4
    try : 
        last=map_index_dict[last_index]
        end_of_surah=0
    except:
        last=map_index_dict[last_index-1]
        end_of_surah=1
    return {
        "syllables": syllable_highlights,
        "wer": alignment_result.wer,
        "substitutions": alignment_result.substitutions,
        "insertions": alignment_result.insertions,
        "deletions": alignment_result.deletions,
        "last_index": last,
        "end":end_of_surah

    }

# Global variable to store the last processed index


def get_true_syllables_from_last_index(syllable_store, last_index):
    print("Inside get_true_syllables_from_last_index")
    
    map_index_dict = {}  # Dictionary to map new indices starting from 0
    true_syllables = []  # List to store the syllables
    syllable_count = 0   # Counter for the number of syllables added
    max_syllables = 50   # Number of syllables to fetch

    # Loop through syllable_store to get the next 50 syllables
    for key, syllable_data in sorted(syllable_store.items(), key=lambda x: int(x[0])):
        current_index = int(syllable_data['syllable_index'])

        # Only process syllables with index >= last_index
        if current_index >= last_index:
            true_syllables.append(syllable_data['syllable_text'])
            map_index_dict[syllable_count] = current_index  # Map new index to original index
            syllable_count += 1

            # Stop if 50 syllables have been added
            if syllable_count > max_syllables:
                break

    return true_syllables, map_index_dict


