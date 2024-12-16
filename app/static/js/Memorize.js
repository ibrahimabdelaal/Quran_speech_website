// Global variable to cache verses
const versesData = {};
let currentVerses = [];
let currentVerseIndex = -1;

// Load verses for the selected Surah
function loadVerses(surahId) {
    const verseTextDisplay = document.getElementById("verse-text-display");
    verseTextDisplay.innerHTML = "<p>......جارى تحميل السورة</p>"; // Show loading message

    if (!surahId) {
        verseTextDisplay.innerHTML = "<p>Please select a Surah.</p>"; // Handle no selection
        return;
    }

    if (versesData[surahId]) {
        // Use cached data if available
        currentVerses = versesData[surahId];
        displayVerses(currentVerses);
    } else {
        // Fetch verses from the API
        fetch(`/api/verses/${surahId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                versesData[surahId] = data; // Cache the data
                currentVerses = data;
                displayVerses(data);
            })
            .catch(error => {
                console.error('Error fetching verses:', error);
                verseTextDisplay.innerHTML = "<p>Error loading verses. Please try again.</p>";
            });
    }
}

// Display the verses and add syllables with event listeners
function displayVerses(verses) {
    console.log('Displaying verses');
    const verseTextDisplay = document.getElementById("verse-text-display");
    verseTextDisplay.innerHTML = ""; // Clear previous content

    let syllableIndex = 0; // To keep track of syllable index across all verses

    // Iterate over each verse to create the required structure
    const concatenatedVerses = verses.map(verse => {
        const syllablesWithIndexes = verse.syllables.split('-').map(syllable => {
            const syllableHTML = `<span class="syllable" data-index="${syllableIndex}" data-text="${syllable}" data-verse="${verse.verse_number}">${syllable}</span>`;
            syllableIndex++; // Increment the index for each syllable
            return syllableHTML;
        }).join(' '); // Join syllables of a verse with spaces

        return `${syllablesWithIndexes} <span class="verse-number">﴿${verse.verse_number}﴾</span>`;
    }).join(' '); // Join verses with a space between them

    verseTextDisplay.innerHTML = concatenatedVerses; // Display the structured verses
    
    // Attach click event listeners to each syllable
    const syllables = document.querySelectorAll('.syllable');
    syllables.forEach(syllable => {
        
            const index = syllable.getAttribute('data-index');
            const text = syllable.getAttribute('data-text');
            const verse = syllable.getAttribute('data-verse');
            sendSyllableDataToServer(index, text, verse);
        ;
    });
}

// Function to send syllable data to the server
async function sendSyllableDataToServer(index, text, verse) {
    console.log('insidesend syllables ');
    try {
        const response = await fetch('/process_syllable', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                syllable_index: index,
                syllable_text: text,
                verse_number: verse,
            }),
        });

        if (!response.ok) {
            console.error('Failed to send syllable data:', response.statusText);
            return;
        }

        const result = await response.json();
        console.log('Server response:', result);
    } catch (error) {
        console.error('Error sending syllable data to server:', error);
    }
}


// Function to update the syllable highlight based on server feedback
function highlightSyllables(syllableIndex, resultType,maxIndex,end) {
    const syllable = document.querySelector(`.syllable[data-index='${syllableIndex}']`);
    if (end) {    maxIndex+=1;     }
        
    if (syllableIndex !== null && syllableIndex > maxIndex-1) {
        console.log(`Skipping syllable with index ${syllableIndex}`);
        return; // Stop further processing for this syllable
    }
    if (syllable) {
        if (resultType === 'correct') {
            syllable.classList.add('highlightRight');
        } else if (resultType === 'wrong') {
            syllable.classList.add('highlightWrong');
        } 
    }
}

// Handle audio chunk and send to server
let myvad;

const startButton = document.getElementById('start-recognition');

startButton.addEventListener('click', async () => {
    if (startButton.textContent === 'ابدأ التسجيل') {
        startButton.classList.add('recording');
        startButton.textContent = 'إيقاف التسجيل';
        startButton.style.backgroundColor = 'rgb(59, 9, 20)'; // Change the background color
        Send_start_cliked(1)
        // Initialize VAD and start listening
        myvad = await vad.MicVAD.new({
            positiveSpeechThreshold: 0.5, // Adjust as needed
            negativeSpeechThreshold: 0.4, // Adjust as needed
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
        startButton.style.backgroundColor = ''; // Reset the background color
        Send_start_cliked(0)
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
async function Send_start_cliked( value) {
    try {
        const response = await fetch('/submit_value', {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain'
            },
            body: value.toString() // Send the value as plain text
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
        }

        const result = await response.text(); // Assuming server responds with plain text
        console.log('Server Response:', result);
        return result;
    } catch (error) {
        console.error('Error sending value to server:', error);
        throw error; // Re-throw error for further handling
    }
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
            const data = await response.json(); // Expect JSON response for highlighting
            console.log('Server Response:', data);

            // Iterate over aligned_text array from server response
            max_index=data.last_index
            end=data.end
            data.aligned_text.forEach(item => {
                if (item.index !== null) {
                    // Highlight the syllable with the corresponding index and status
                    highlightSyllables(item.index, item.status,max_index,end); // 'correct', 'missed', 'wrong', or 'inserted'
                } else {
                    console.warn('Inserted syllable detected, but no corresponding index.');
                }
            });

            // Optionally log metrics like WER and alignment stats
            console.log('WER:', data.wer);
            console.log('Substitutions:', data.substitutions);
            console.log('Insertions:', data.insertions);
            console.log('Deletions:', data.deletions);
            console.log('index:', data.last_index);

        } else {
            console.error('Failed to upload audio chunk:', response.statusText);
        }
    } catch (error) {
        console.error('Error uploading audio chunk:', error);
    }
}

