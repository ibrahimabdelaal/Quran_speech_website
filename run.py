import logging
from flask import Flask, render_template, jsonify, request, abort, send_file
from werkzeug.utils import secure_filename
import os
import json
import tempfile
from mimetypes import guess_extension
import io
import base64
import wave
import jiwer
from app import create_app
from app.models import Surah, Verse, highlight_alignment_real_time,highlight_alignment_real_time_2, transcribe_audio_file_withoutLMHead, convert_weba_to_wav,get_true_syllables_from_last_index

# Initialize logging
import logging
syllable_store={}
# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s:%(message)s')

# Your Flask app and routes here
CHUNKS_DIR = "chunks"
os.makedirs(CHUNKS_DIR, exist_ok=True)

# WAV file settings
SAMPLE_RATE = 16000  # 16kHz sample rate
NUM_CHANNELS = 1  # Mono audio
SAMPLE_WIDTH = 2  # 16-bit audio (2 bytes per sample)
last_index=0
app = create_app()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/recite_correct')
def recite_correct():
    surahs = Surah.query.all()
    return render_template('recite_correct.html', surahs=surahs)

@app.route('/surah_selection')
def surah_selection():
    surahs = Surah.query.all()
    return render_template('surah_selection.html', surahs=surahs)
@app.route('/mem')
def mem():
    surahs = Surah.query.all()
    return render_template('mem.html', surahs=surahs)

@app.route('/surah/<int:surah_id>')
def surah(surah_id):
    surah = Surah.query.get_or_404(surah_id)
    verses = Verse.query.filter_by(surah_id=surah.id).all()
    return render_template('surah.html', surah=surah, verses=verses)

@app.route('/api/verses/<int:surah_id>')
def get_verses(surah_id):
    verses = Verse.query.filter_by(surah_id=surah_id).all()
    return jsonify([{
        "id": verse.id,
        "verse_number": verse.verse_number,
        "text": verse.text,
        "syllables": verse.syllables,
        "audio": verse.audio_file if verse.audio_file else None
    } for verse in verses])

@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' in request.files and 'verse_id' in request.form:
        file = request.files['audio']
        true_verse = request.form['verse_id'].replace("-", " ")
        extname = guess_extension(file.mimetype)
        if not extname:
            logging.error('Invalid audio format.')
            return jsonify({'error': 'Invalid audio format'}), 400

        with tempfile.TemporaryDirectory() as temp_dir:
            audio_file_path = os.path.join(temp_dir, secure_filename(file.filename))
            file.save(audio_file_path)
            dst_wav = os.path.join(temp_dir, f"{os.path.splitext(secure_filename(file.filename))[0]}.wav")

            if convert_weba_to_wav(audio_file_path, dst_wav):
                transcription = transcribe_audio_file_withoutLMHead(dst_wav)
                comparison, aligned_text = compare_transcriptions_feedback(true_verse, transcription)
                return jsonify({
                    'transcription': transcription,
                    'comparison': comparison,
                    'aligned_text': aligned_text
                })
            else:
                logging.error('Transcription failed.')
                return jsonify({'error': 'Transcription failed'}), 500
    return jsonify({'error': 'No audio file provided'}), 400

@app.route('/api/audio/<int:verse_id>')
def get_audio(verse_id):
    verse = Verse.query.get(verse_id)
    if verse and verse.audio_file:
        return send_file(io.BytesIO(verse.audio_file), mimetype='audio/wav')
    return '', 404


# Define the directory to save audio chunks
SAVED_AUDIO_DIR = "saved_audio_chunks"
os.makedirs(SAVED_AUDIO_DIR, exist_ok=True)  # Create directory if it doesn't exist

# In-memory accumulated transcription
accumulated_transcription = ""

@app.route('/upload_real_time', methods=['POST'])
def upload_real_time():
    global accumulated_transcription  # To handle accumulated transcription across requests
    if 'audio' in request.files :#and 'verse_id' in request.form:
        print("audiooooooo exist")
        audio_chunk = request.files['audio']
    
    try:
        os.makedirs(CHUNKS_DIR, exist_ok=True)
        chunk_filename = os.path.join(CHUNKS_DIR, f"chunk_{len(os.listdir(CHUNKS_DIR))}.wav")

        # Convert raw audio data to WAV format
        with wave.open(chunk_filename, 'wb') as wav_file:
            wav_file.setnchannels(NUM_CHANNELS)  # Example: Mono channel
            wav_file.setsampwidth(SAMPLE_WIDTH)  # Example: 2 bytes (16-bit audio)
            wav_file.setframerate(SAMPLE_RATE)  # Example: 48000 Hz
            wav_file.writeframes(audio_chunk)

        logging.info(f"Saved WAV file to {chunk_filename}, size: {len(audio_chunk)} bytes")

        # Transcribe the chunk
        chunk_transcription = transcribe_audio_file_withoutLMHead(chunk_filename)

        # Accumulate transcription
        accumulated_transcription += f" {chunk_transcription}".strip()

        # Compare transcriptions
        true_verse = request.form['verse_id'].replace("-", " ").strip()
        comparison, accumulated_alignment = compare_transcriptions(true_verse, accumulated_transcription)

        # Return response with updated transcription and alignment
        return jsonify({
            'transcription': accumulated_transcription,
            'comparison': comparison,
            'aligned_text': accumulated_alignment,
            'saved_audio_path': chunk_filename
        })

    except Exception as e:
        logging.error(f"Error processing audio chunk: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/process_syllable', methods=['POST'])
def process_syllable():
    try:
        # Parse the incoming JSON data
        data = request.get_json()
        syllable_index = data.get('syllable_index')
        syllable_text = data.get('syllable_text')
        verse_number = data.get('verse_number')

        # Log the received data
        #print(f"Received syllable index: {syllable_index}, text: {syllable_text}, verse: {verse_number}")

        # Save the syllable data using a helper function
        save_syllable_data(syllable_index, syllable_text, verse_number)

        # Respond with confirmation
        
        return jsonify({'message': 'Syllable data processed successfully', 'status': 'success'})
    except Exception as e:
        logging.error(f"Error processing syllable data: {e}")
        return jsonify({'error': 'Failed to process syllable data', 'status': 'error'}), 500


def save_syllable_data(syllable_index, syllable_text, verse_number):
    """
    Save the syllable data in the global dictionary.
    """
    global syllable_store  # Access the global dictionary

    # Create a unique key using verse_number and syllable_index
    key = f"{syllable_index}"

    # Save the syllable data
    syllable_store[key] = {
        'syllable_index': syllable_index,
        'syllable_text': syllable_text,
        'verse_number': verse_number
    }

    # Log the saved data
    #print(f"Saved syllable data: {syllable_store}")

@app.route('/process_audio2', methods=['POST'])
def process_audio2():
    # Receive the audio chunk
    audio_chunk = request.data

    # Generate the WAV file path
    chunk_filename = os.path.join(CHUNKS_DIR, f"chunk_{len(os.listdir(CHUNKS_DIR))}.wav")

    # Convert raw audio data to WAV format
    with wave.open(chunk_filename, 'wb') as wav_file:
        wav_file.setnchannels(NUM_CHANNELS)
        wav_file.setsampwidth(SAMPLE_WIDTH)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio_chunk)

    print(f"Saved WAV file to {chunk_filename}, size: {len(audio_chunk)} bytes")
    with open('trans.txt','a',encoding='utf-8') as t:
        transcription = transcribe_audio_file_withoutLMHead(chunk_filename)
        print(transcription)
        t.write(transcription+"\n")

   


    return "Chunk received", 200



@app.route('/process_audio', methods=['POST'])
def process_audio():
    # Receive the audio chunk
    audio_chunk = request.data

    # Generate the WAV file path
    chunk_filename = os.path.join(CHUNKS_DIR, f"chunk_{len(os.listdir(CHUNKS_DIR))}.wav")

    # Convert raw audio data to WAV format
    with wave.open(chunk_filename, 'wb') as wav_file:
        wav_file.setnchannels(NUM_CHANNELS)
        wav_file.setsampwidth(SAMPLE_WIDTH)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio_chunk)

    print(f"Saved WAV file to {chunk_filename}, size: {len(audio_chunk)} bytes")

    # Generate transcription using the model
    transcription = transcribe_audio_file_withoutLMHead(chunk_filename)
    print(f"Transcription: {transcription}")

    # Save the transcription in a file
    with open('trans.txt', 'a', encoding='utf-8') as t:
        t.write(transcription + "\n")

    # Align the transcription with the true surah syllables
    # Here, syllable_store stores the last syllable index and the true syllables
    global last_index 
    true_verse,map_index_dict = get_true_syllables_from_last_index(syllable_store,last_index)
    # Use compare_transcriptions to align the transcription with the true surah
    true_verse = " ".join(true_verse)  # Use a space as a delimiter or "" for no space
    print(true_verse)
    print("******************************************")
    print(transcription)
    print(type(true_verse),type(transcription))
    alignment_result, aligned_text = compare_transcriptions(true_verse, transcription,map_index_dict)
    # Update the syllable_store with the new last syllable index after alignment
    # Return the aligned text (for real-time highlighting) and the WER/other metrics

    #updating last index
    last_index= aligned_text['last_index']
    return jsonify({
        'aligned_text': aligned_text['syllables'],
        'wer': alignment_result['wer'],
        'substitutions': alignment_result['substitutions'],
        'insertions': alignment_result['insertions'],
        'deletions': alignment_result['deletions'],
        'last_index': aligned_text['last_index']
    }), 200
























def compare_transcriptions_feedback(true_verse, transcription):
    transformed_true_verse = [true_verse]
    transformed_transcription = [transcription]
    comparison = jiwer.compute_measures(transformed_true_verse, transformed_transcription)
    aligned_text = highlight_alignment_real_time(transformed_true_verse, [transcription])
    return {
        'wer': comparison['wer'],
        'substitutions': comparison['substitutions'],
        'insertions': comparison['insertions'],
        'deletions': comparison['deletions']
    }, aligned_text
def compare_transcriptions(true_verse, transcription,map_index_dict):
    transformed_true_verse = [true_verse]
    transformed_transcription = [transcription]
    comparison = jiwer.compute_measures(transformed_true_verse, transformed_transcription)
    aligned_text = highlight_alignment_real_time_2(transformed_true_verse, [transcription],map_index_dict)
    return {
        'wer': comparison['wer'],
        'substitutions': comparison['substitutions'],
        'insertions': comparison['insertions'],
        'deletions': comparison['deletions']
    }, aligned_text
@app.route('/submit_value', methods=['POST'])
def submit_value():
    global last_index
    try:
        # Get the raw data sent in the request
        value = request.data.decode('utf-8').strip()

        if value == '0':
            print("Received value: 0")
            return "Value is 0", 200
        elif value == '1':
            last_index=0
            return "Value is 1", 200
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred on the server.", 500
if __name__ == '__main__':
    app.run(debug=True)
