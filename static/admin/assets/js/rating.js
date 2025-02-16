document.addEventListener('DOMContentLoaded', function() {
    // Rating functionality
    const ratingStars = document.getElementById('ratingStars');
    const stars = document.querySelectorAll('.star');
    const ratingInput = document.getElementById('ratingInput');
    
    function updateStars(rating) {
        stars.forEach(star => {
            const value = parseInt(star.dataset.value);
            if (value <= rating) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        });
        ratingInput.value = rating;
    }

    // Initialize stars with existing rating
    const initialRating = parseInt(ratingInput.value) || 0;
    if (initialRating > 0) {
        updateStars(initialRating);
    }

    // Add click event listeners to stars
    stars.forEach(star => {
        star.addEventListener('click', function() {
            const rating = parseInt(this.dataset.value);
            updateStars(rating);
        });
    });

    // Character count functionality
    const messageInput = document.getElementById('messageInput');
    const charCount = document.getElementById('charCount');

    function updateCharCount() {
        const currentLength = messageInput.value.length;
        charCount.textContent = `${currentLength} / 133`;
    }

    // Add input event listener for character count
    messageInput.addEventListener('input', updateCharCount);

    // Initialize character count on page load
    updateCharCount();
});