document.addEventListener("DOMContentLoaded", function() {
    // Get the container where Pygame will render
    const pygameContainer = document.getElementById('pygame-container');

    // Create a Pygame canvas element
    const pygameCanvas = document.createElement('canvas');
    pygameCanvas.setAttribute('id', 'pygame-canvas');
    pygameCanvas.setAttribute('width', '750');
    pygameCanvas.setAttribute('height', '750');

    // Append the Pygame canvas to the container
    pygameContainer.appendChild(pygameCanvas);

    // Function to initialize and run Pygame
    function runPygame() {
        const pygameScript = document.createElement('script');
        pygameScript.src = '/static/game/js/pygame_bundle.js';  // Path to your bundled Pygame code
        document.body.appendChild(pygameScript);

        pygameScript.onload = function() {
            console.log('Pygame initialized');
            // Call a function to start the game here if necessary
        };
    }

    // Ensure Pygame runs when the page is loaded
    runPygame();
});
