const startButton = document.getElementById('start-recognition');
let recording = false;
let mediaRecorder;
let audioChunks = [];
let audioURL;
let stream; // Declare stream variable outside the event listener to access it later
const constraints = {
    
    audio:true
     // Other constraints if needed
    }


startButton.addEventListener('click', async () => {
    if (!recording) {
        try {
            clearRecordedAudio();
            clearTranscription(); // Clear transcription when starting recording
            stream = await navigator.mediaDevices.getUserMedia(constraints); // Assign the stream to the variable
            mediaRecorder = new MediaRecorder(stream);
            const audioTrack = stream.getAudioTracks()[0];
            const sampleRate = audioTrack.getSettings().sampleRate;
            console.log('Sample rate:', sampleRate);

            // Update button style when recording starts
            startButton.classList.add('recording');
            startButton.innerText = 'إيقاف التسجيل';
            startButton.style.backgroundColor = 'rgb(59, 9, 20)'; // Change the background color


            mediaRecorder.onstart = () => {
                console.log('Recording started...');
                recording = true;
            };

            mediaRecorder.onstop = () => {
                console.log('Recording stopped.');
                recording = false;

                // Update button style when recording stops
                startButton.classList.remove('recording');
                startButton.innerText = 'ابدأ التسجيل';
                startButton.style.backgroundColor = ''; // Change the background color

                // Send audio data to server for transcription
                sendAudioToServer();
                // Stop the media stream and associated tracks (including microphone)
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            // Start recording
            mediaRecorder.start();
        } catch (error) {
            console.error('Error recording audio:', error);
        }
    } else {
        // Stop recording
        mediaRecorder.stop();
    }
});

// Function to send audio data to the server for transcription
async function sendAudioToServer() {
    try {
        // Create Blob from audioChunks
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const audioElement = document.getElementById('recorded-audio');
        audioElement.src = URL.createObjectURL(audioBlob);
        audioElement.controls = true; // Show controls for the audio player
        const verseSyllables = document.getElementById("verse-text-display").dataset.syllables; // Retrieve syllables
        const formData = new FormData();
        formData.append('audio', audioBlob);
        formData.append('verse_id', verseSyllables);

        // Send audio data to server
        const response = await fetch('/upload', {
            method: 'POST',
            cache: "no-cache",
            body: formData,
        });

        // Get transcription from response
        const transcriptionData = await response.json();
        if (transcriptionData.error) {
            console.error('Server error:', transcriptionData.error);
            return;
        }

        // Get highlighted aligned text directly from the server response
        const alignedText = transcriptionData.aligned_text;

        // Inject aligned text into the HTML element
        document.getElementById("transcription").innerHTML = alignedText;
        
    } catch (error) {
        console.error('Error sending audio to server:', error);
    }
}


// Function to clear recorded audio
function clearRecordedAudio() {
    audioChunks = [];
}
function clearTranscription() {
    document.getElementById("transcription").innerHTML = ""; // Clear the transcription container
}
