
    // Wait for the DOM to load
    document.addEventListener("DOMContentLoaded", function() {
        const surahDropdown = document.getElementById("surah-dropdown");
        const surahTextContainer = document.getElementById("surah-text");
        const surahDisplayContainer = document.getElementById("surah-display");
        const startReadingButton = document.getElementById("start-reading-button");

        // Event listener for the dropdown
        surahDropdown.addEventListener("change", function() {
            const selectedSurah = surahDropdown.value;

            // Show a loading indicator while fetching data
            const loadingIndicator = document.getElementById("loading-indicator");
            loadingIndicator.style.display = "block";
            surahDisplayContainer.innerHTML = ""; // Clear previous surah content

            // Make an AJAX request to fetch the verses for the selected surah
            fetch(`/get_surah_verses/${selectedSurah}`)
                .then(response => response.json())
                .then(data => {
                    loadingIndicator.style.display = "none"; // Hide the loading indicator

                    if (Array.isArray(data)) {
                        // Append the verses to the surah display container
                        data.forEach(verse => {
                            const verseElement = document.createElement("p");
                            verseElement.textContent = verse;
                            surahDisplayContainer.appendChild(verseElement);
                        });
                    } else {
                        // Handle error if surah not found
                        const errorMessage = document.getElementById("error-message");
                        errorMessage.style.display = "block";
                        errorMessage.textContent = "Error loading verses!";
                    }
                })
                .catch(error => {
                    loadingIndicator.style.display = "none"; // Hide the loading indicator
                    const errorMessage = document.getElementById("error-message");
                    errorMessage.style.display = "block";
                    errorMessage.textContent = "An error occurred while fetching verses.";
                });
        });

        // Start reading button functionality (if necessary for audio transcription)
        startReadingButton.addEventListener("click", function() {
            // Handle start reading functionality here
            console.log("Start reading button clicked");
        });
    });

