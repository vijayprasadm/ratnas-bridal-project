document.addEventListener('DOMContentLoaded', function() {
    const cardsContainer = document.querySelector('.testimonials-cards');
    const cards = document.querySelectorAll('.testimonial-card');
    const nextBtn = document.getElementById('nextCardBtn');
    let currentIndex = 0;
    const totalCards = cards.length;

    // Function to update the active card
    function updateCards() {
        cards.forEach((card, index) => {
            // Remove 'active' class from all cards
            card.classList.remove('active');

            // Position the cards in the stack
            if (index >= currentIndex) {
                card.style.transform = `translateY(${(index - currentIndex) * 20}px) scale(${1 - (index - currentIndex) * 0.05})`;
                card.style.opacity = 1;
                card.style.zIndex = totalCards - (index - currentIndex);
            } else {
                // Animate "removed" cards off-screen
                card.style.transform = `translateY(100%) scale(0.8)`;
                card.style.opacity = 0;
                card.style.zIndex = 0;
            }
        });

        // Add 'active' class to the top card
        cards[currentIndex].classList.add('active');
    }

    // Next card functionality
    function nextCard() {
        // Hide the current card
        cards[currentIndex].style.transform = 'translateY(-100%) scale(0.8)';
        cards[currentIndex].style.opacity = '0';
        cards[currentIndex].style.zIndex = '0';
        
        // Move to the next card, looping back to the start
        currentIndex = (currentIndex + 1) % totalCards;

        // Animate the next card into view
        cards[currentIndex].style.transform = 'translateY(0) scale(1)';
        cards[currentIndex].style.opacity = '1';
        cards[currentIndex].style.zIndex = '2';
    }

    nextBtn.addEventListener('click', nextCard);

    // Initial setup
    updateCards();

    // Auto-slide functionality (optional)
    let autoSlideInterval = setInterval(nextCard, 5000); // Change card every 5 seconds

    // Pause auto-slide on hover
    const stackedContainer = document.querySelector('.testimonials-stacked-container');
    stackedContainer.addEventListener('mouseover', () => {
        clearInterval(autoSlideInterval);
    });

    stackedContainer.addEventListener('mouseleave', () => {
        autoSlideInterval = setInterval(nextCard, 5000);
    });
});
