// Gestion de la cinématique intro
document.addEventListener('DOMContentLoaded', () => {
    const introOverlay = document.getElementById('intro-overlay');
    const introVideo = document.getElementById('intro-video');
    const skipButton = document.getElementById('skip-intro');
    const header = document.querySelector('header');
    const main = document.querySelector('main');
    const footer = document.querySelector('footer');

    if (introOverlay && introVideo) {
        // Fonction pour cacher l'overlay et afficher le contenu
        const showContent = () => {
            introOverlay.style.display = 'none';
            if (header) header.classList.remove('hidden');
            if (main) main.classList.remove('hidden');
            if (footer) footer.classList.remove('hidden');
        };

        // À la fin de la vidéo
        introVideo.addEventListener('ended', showContent);

        // Bouton skip
        if (skipButton) {
            skipButton.addEventListener('click', () => {
                introVideo.pause();
                showContent();
            });
        }

        // Pour forcer le play si besoin (sur certains navigateurs)
        introVideo.play().catch(error => {
            console.log('Autoplay bloqué:', error);
            // Optionnel: Afficher un bouton play si autoplay échoue
        });
    }

    // Menu hamburger
    const menuToggle = document.getElementById("menu-toggle")
    const navMenu = document.getElementById("nav-menu")

    if (menuToggle && navMenu) {
        menuToggle.addEventListener("click", () => {
            navMenu.classList.toggle("active")
        })
    }

    // Validation du formulaire de contact
    const form = document.getElementById("contact-form")
    if (form) {
        form.addEventListener("submit", (e) => {
            const name = document.getElementById("name").value.trim()
            const email = document.getElementById("email").value.trim()
            const message = document.getElementById("message")?.value.trim()

            if (!name || !email) {
                alert("Veuillez remplir tous les champs obligatoires.")
                e.preventDefault()
                return
            }

            // Validation basique de l'email
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
            if (!emailRegex.test(email)) {
                alert("Veuillez entrer une adresse email valide.")
                e.preventDefault()
                return
            }
        })
    }
});