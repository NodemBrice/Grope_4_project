// Gestion de la cinématique intro
document.addEventListener('DOMContentLoaded', () => {
    // S'assurer que ces variables sont correctement définies à partir des éléments HTML
    const introOverlay = document.getElementById('intro-overlay');
    const introVideo = document.getElementById('intro-video');
    const skipButton = document.getElementById('skip-intro');
    const header = document.querySelector('header');
    const main = document.querySelector('main');
    const footer = document.querySelector('footer');

    // Fonction pour cacher l'overlay et afficher le contenu.
    // Cette fonction est maintenant définie dans la portée du DOMContentLoaded
    // pour être accessible quel que soit le chemin (intro jouée ou non).
    const showContent = () => {
        if (introOverlay) { // Ajout d'une vérification de nullité par bonne pratique
            introOverlay.style.display = 'none';
        }
        if (header) header.classList.remove('hidden');
        if (main) main.classList.remove('hidden');
        if (footer) footer.classList.remove('hidden');
        
        // Marquer comme joué pour cette session une fois le contenu affiché
        sessionStorage.setItem('introPlayed', 'true');
    };

    // Vérifier si l'intro a déjà été jouée dans cette session
    if (sessionStorage.getItem('introPlayed') === 'true') {
        // Si l'intro a déjà été jouée, afficher le contenu immédiatement
        showContent();
    } else {
        // Si l'intro n'a PAS été jouée, alors on procède à l'affichage de la vidéo
        
        // À la fin de la vidéo, appeler showContent
        if (introVideo) { // Ajout d'une vérification de nullité par bonne pratique
            introVideo.addEventListener('ended', showContent);
        }

        // Bouton skip
        if (skipButton) {
            skipButton.addEventListener('click', () => {
                if (introVideo) introVideo.pause(); // Mettre en pause la vidéo si elle existe
                showContent(); // Appeler showContent pour masquer l'overlay et marquer comme joué
            });
        }

        // Pour forcer le play si besoin (sur certains navigateurs)
        if (introVideo) { // Ajout d'une vérification de nullité par bonne pratique
            introVideo.play().catch(error => {
                console.log('Autoplay bloqué:', error);
                // Optionnel: Afficher un bouton play si l'autoplay échoue
                // ou appeler showContent() ici pour ne pas bloquer l'utilisateur
            });
        }
    }
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