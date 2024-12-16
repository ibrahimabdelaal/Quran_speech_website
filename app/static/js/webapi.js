let audioContext, processor, source;
let accumulatedBuffer = []; // Array to hold accumulated audio data
let previousChunk = null; // For overlapping chunks
const CHUNK_ACCUMULATION_LIMIT = 6; // Number of chunks to accumulate
const OVERLAP_PERCENTAGE = 0.25; // 25% overlap
const CHUNK_SIZE = 16384;

const startButton = document.getElementById('start-recognition');
//const stopButton = document.getElementById('stop-recognition');
const surahDropdown = document.getElementById("surah-dropdown");
const surahTextContainer = document.getElementById("surah-text");
const surahDisplayContainer = document.getElementById("surah-display");
let isRecording=false
startButton.addEventListener('click', async () => {
   
        if (!isRecording) {
            // Start recording
            await startRecording();
            startButton.classList.add('recording');
            startButton.innerText = 'إيقاف التسجيل';
            startButton.style.backgroundColor = 'rgb(59, 9, 20)'; // Change the background color

        } else {
            // Stop recording
            stopRecording();
            startButton.classList.remove('recording');
            startButton.innerText = 'ابدأ التسجيل';
            startButton.style.backgroundColor = ''; // Change the background color
        }
        isRecording = !isRecording;
    // Request audio input from the user
 async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // Initialize the audio context
    audioContext = new AudioContext({ sampleRate: 48000 });

    // Create a media stream source
    source = audioContext.createMediaStreamSource(stream);

    // Create a script processor for raw PCM data
    processor = audioContext.createScriptProcessor(CHUNK_SIZE, 1, 1);
    processor.onaudioprocess = (event) => {
        const input = event.inputBuffer.getChannelData(0); // Mono channel data
        const pcmData = convertFloat32ToInt16(input);

        // Apply overlapping logic
        if (previousChunk) {
            const overlapSize = Math.floor(CHUNK_SIZE * OVERLAP_PERCENTAGE);
            const overlappedData = mergeBuffers([
                previousChunk.slice(-overlapSize),
                pcmData,
            ]);
            accumulatedBuffer.push(overlappedData);
        } else {
            accumulatedBuffer.push(pcmData);
        }

        // Update the previous chunk
        previousChunk = pcmData;

        // Send accumulated data once the limit is reached
        if (accumulatedBuffer.length >= CHUNK_ACCUMULATION_LIMIT) {
            const combinedBuffer = mergeBuffers(accumulatedBuffer);
            sendAudioChunk(combinedBuffer);
            accumulatedBuffer = []; // Reset the buffer
        }
    };

    // Connect the processor and source
    source.connect(processor);
    processor.connect(audioContext.destination);
}
 
});

function stopRecording() {

    // Stop recording and clean up
    processor.disconnect();
    source.disconnect();
    audioContext.close();

    // startButton.disabled = false;
    // stopButton.disabled = true;

    // Send any remaining data in the buffer
    if (accumulatedBuffer.length > 0) {
        const combinedBuffer = mergeBuffers(accumulatedBuffer);
        sendAudioChunk(combinedBuffer);
    }

    // Reset states
    accumulatedBuffer = [];
    previousChunk = null;
};

function sendAudioChunk(pcmData) {
    fetch('/process_audio', {
        method: 'POST',
        body: pcmData,
    }).then(response => {
        if (response.ok) {
            console.log("Audio chunk sent successfully");
        } else {
            console.error("Failed to send audio chunk");
        }
    });
}

function convertFloat32ToInt16(buffer) {
    let length = buffer.length;
    let result = new Int16Array(length);
    for (let i = 0; i < length; i++) {
        result[i] = Math.max(-1, Math.min(1, buffer[i])) * 0x7FFF; // Scale float to int16
    }
    return result.buffer;
}

function mergeBuffers(buffers) {
    // Calculate total length of all buffers
    const totalLength = buffers.reduce((sum, buffer) => sum + buffer.byteLength, 0);

    // Create a new buffer to hold the combined data
    const combinedBuffer = new Uint8Array(totalLength);

    // Copy data from each buffer into the combined buffer
    let offset = 0;
    buffers.forEach(buffer => {
        combinedBuffer.set(new Uint8Array(buffer), offset);
        offset += buffer.byteLength;
    });

    return combinedBuffer.buffer;
}
