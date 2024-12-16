// Include the WebRTC VAD package
   
//  positiveSpeechThreshold: This parameter determines the threshold above which a 
//  probability is considered to indicate the presence of speech.   
//  negativeSpeechThreshold: This parameter determines the threshold below which a 
//  probability is considered to indicate the absence of speech.   






let myvad;

const startButton = document.getElementById('start-recognition');

startButton.addEventListener('click', async () => {
    if (startButton.textContent === 'ابدأ التسجيل') {
        startButton.classList.add('recording');
        startButton.textContent = 'إيقاف التسجيل';
        startButton.style.backgroundColor = 'rgb(59, 9, 20)'; // Change the background color

        // Initialize VAD and start listening
        myvad = await vad.MicVAD.new({
            positiveSpeechThreshold: 0.7, // Adjust as needed
            negativeSpeechThreshold: 0.5, // Adjust as needed
            onSpeechStart: () => {
                console.log("Speech start detected");
            },
            onSpeechEnd: (audio) => {
                console.log("Speech end detected");

                // Handle audio (Float32Array of audio samples at 16000 Hz)
                handleAudioChunk(audio);
            },
            onError: (error) => {
                console.error("VAD Error:", error);
            },
            debug: false, // Enable if debugging is needed
        });

        myvad.start();
    } else {
        startButton.classList.remove('recording');
        startButton.textContent = 'ابدأ التسجيل';
        startButton.style.backgroundColor = ''; // Change the background color

        if (myvad) {
            await myvad.destroy(); // Correct method to stop VAD
            console.log("VAD destroyed.");
        }
    }
});



function convertFloat32ToInt16(buffer) {
    let length = buffer.length;
    let result = new Int16Array(length);
    for (let i = 0; i < length; i++) {
        result[i] = Math.max(-1, Math.min(1, buffer[i])) * 0x7FFF; // Scale float to int16
    }
    return result.buffer;
}

function handleAudioChunk(audio) {
    // Send the raw PCM Float32Array audio chunk to the server
    const pcmData = convertFloat32ToInt16(audio);
    sendAudioChunk(pcmData);
}

async function sendAudioChunk(chunkBuffer) {
    try {
        const response = await fetch('/process_audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/octet-stream'
            },
            body: chunkBuffer, // Send raw PCM data
        });

        if (response.ok) {
            const data = await response.text(); // Adjusted to handle plain text response
            console.log('Server Response:', data);
        } else {
            console.error('Failed to upload audio chunk');
        }
    } catch (error) {
        console.error('Error uploading audio chunk:', error);
    }
}
