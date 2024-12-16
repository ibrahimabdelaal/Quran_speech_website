const startButton = document.getElementById('start-recognition');
let recording = false;
let mediaRecorder;
let audioChunks = [];
let stream; // Declare stream variable outside the event listener to access it later
const constraints = { audio: true }; // Constraints for audio
let isSending = false; // Flag to control sequential chunk sending
let recordingIndex = 0; // To track recording sessions
let isProgrammaticClick = false; // Flag to distinguish click events

startButton.addEventListener('click', async () => {
    if (recording) {
        // Stop recording if already recording
        mediaRecorder.stop();
    } else {
        // Check if the click is programmatic
        if (isProgrammaticClick) {
            isProgrammaticClick = false; // Reset the flag for future clicks
            return; // Exit if the click was programmatic
        }

        try {
            clearRecordedAudio();
            stream = await navigator.mediaDevices.getUserMedia(constraints); // Assign the stream to the variable
            mediaRecorder = new MediaRecorder(stream);

            // Update button style when recording starts
            startButton.classList.add('recording');
            startButton.innerText = 'إيقاف التسجيل';
            startButton.style.backgroundColor = 'rgb(59, 9, 20)'; // Change the background color

            mediaRecorder.ondataavailable = (event) => {
                const audioChunk = event.data;

                // Save the chunk locally for debugging or backup
                audioChunks.push(audioChunk);

                // Send real-time chunks to the server for processing (sequentially)
                if (!isSending) {
                    sendAudioChunkToServer(audioChunk, recordingIndex);
                }
            };

            mediaRecorder.onstart = () => {
                console.log('Recording started...');
                recording = true;
                recordingIndex++;
            };

            mediaRecorder.onstop = () => {
                console.log('Recording stopped.');
                recording = false;

                // Update button style when recording stops
                startButton.classList.remove('recording');
                startButton.innerText = 'ابدأ التسجيل';
                startButton.style.backgroundColor = ''; // Reset background color

                // Stop the media stream and associated tracks (including microphone)
                stream.getTracks().forEach((track) => track.stop());
            };

            // Start recording, and trigger `ondataavailable` every 2 seconds
            mediaRecorder.start(2000);
        } catch (error) {
            console.error('Error recording audio:', error);
        }
    }
});

// Function to send real-time audio chunks to the server sequentially
let audioQueue = [];
async function sendAudioChunkToServer(audioChunk, recordingIndex) {
    audioQueue.push({ audioChunk, recordingIndex });

    while (audioQueue.length > 0) {
        const { audioChunk, recordingIndex } = audioQueue[0];
        try {
            const audioBlob = new Blob([audioChunk], { type: 'audio/webm' });
            const formData = new FormData();
            formData.append('audio', audioBlob);
            formData.append('verse_id', document.getElementById("verse-text-display").dataset.syllables);
            formData.append('recording_index', recordingIndex);

            const response = await fetch('/upload_real_time', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Server response error');
            const transcriptionData = await response.json();
            updateHighlightedSurah(transcriptionData.aligned_text);
        } catch (error) {
            console.error('Error sending audio chunk:', error);
        } finally {
            audioQueue.shift(); // Remove the processed chunk
        }
    }
}

async function restartRecording() {
    if (recording) mediaRecorder.stop();
    await startRecording();
}

async function startRecording() {
    try {
        clearRecordedAudio();
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (event) => {
            sendAudioChunkToServer(event.data, recordingIndex);
        };
        mediaRecorder.start(2000); // Record in 2-second chunks
    } catch (error) {
        console.error('Error starting recording:', error);
    }
}

// Function to update the Surah text with highlights
function updateHighlightedSurah(alignedText) {
    const surahDisplayElement = document.getElementById("verse-text-display");
    surahDisplayElement.innerHTML = alignedText; // Replace the displayed Surah text
}

// Function to clear recorded audio
function clearRecordedAudio() {
    audioChunks = [];
    recordingIndex = 0; // Reset recording index
}
