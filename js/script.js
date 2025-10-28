document.addEventListener('DOMContentLoaded', () => {
    // 1. --- Gestion de la cinématique intro ---
    // Déclaration des variables nécessaires en début de scope pour éviter les ReferenceError
    const introOverlay = document.getElementById('intro-overlay');
    const header = document.querySelector('header');
    const main = document.querySelector('main');
    const footer = document.querySelector('footer');
    const introVideo = document.getElementById('intro-video');
    const skipButton = document.getElementById('skip-intro');

    // Fonction d'utilitaire pour cacher l'overlay et afficher le contenu principal,
    // définie une seule fois et à un scope accessible pour toute la logique d'intro.
    const showContent = () => {
        if (introOverlay) { // Vérification défensive avant manipulation de style
            introOverlay.style.display = 'none';
        }
        // Utilisation de l'optional chaining pour manipuler les classes, robuste même si les éléments sont absents
        header?.classList.remove('hidden');
        main?.classList.remove('hidden');
        footer?.classList.remove('hidden');
        // Marquer comme joué pour cette session une fois le contenu affiché
        sessionStorage.setItem('introPlayed', 'true');
    };

    // Vérifier si les éléments clés de l'intro sont présents avant d'exécuter la logique complexe
    if (introOverlay && introVideo) {
        // Vérifier si l'intro a déjà été jouée dans cette session
        if (sessionStorage.getItem('introPlayed') === 'true') {
            showContent(); // Appelle la fonction utilitaire si l'intro a déjà été jouée
        } else {
            // Associer l'écouteur d'événement à la fin de la vidéo
            introVideo.addEventListener('ended', showContent);

            // Gérer le bouton skip s'il existe
            if (skipButton) {
                skipButton.addEventListener('click', () => {
                    introVideo.pause(); // Arrête la vidéo
                    showContent();      // Affiche le contenu
                });
            }

            // Tenter la lecture automatique et gérer les erreurs (bloquage par le navigateur)
            introVideo.play().catch(error => {
                console.log('Autoplay bloqué par le navigateur:', error);
                // Optionnel : rendre le bouton 'skip' ou un bouton 'play' plus visible ici.
            });
        }
    } else {
        // Fallback: Si les éléments d'intro ne sont pas présents, afficher directement le contenu
        console.warn("Éléments d'introduction ('intro-overlay' ou 'intro-video') manquants. Affichage direct du contenu.");
        showContent();
    }


    // 2. --- Menu hamburger ---
    const menuToggle = document.getElementById("menu-toggle");
    const navMenu = document.getElementById("nav-menu");

    if (menuToggle && navMenu) {
        menuToggle.addEventListener("click", () => {
            navMenu.classList.toggle("active");
            menuToggle.classList.toggle("active"); // Correction: Ré-ajout du toggle pour l'icône du bouton
        });
    }

    // 3. --- Validation du formulaire de contact ---
    const form = document.getElementById("contact-form");

    if (form) {
        form.addEventListener("submit", (e) => {
            // Correction: Utilisation d'un accès robuste aux valeurs des inputs
            const nameInput = document.getElementById("name");
            const emailInput = document.getElementById("email");
            const messageInput = document.getElementById("message"); // L'input message est optional ici

            const name = nameInput ? nameInput.value.trim() : '';
            const email = emailInput ? emailInput.value.trim() : '';
            const message = messageInput ? messageInput.value.trim() : ''; // La valeur du message peut être vide

            if (!name || !email) {
                alert("Veuillez remplir tous les champs obligatoires (Nom et Email)."); // Message plus spécifique
                e.preventDefault();
                return;
            }

            // Correction: Utilisation de la regex plus robuste de la version précédente ou choix délibéré
            // Exemple avec la regex plus robuste :
            const emailRegex = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
            // Si la regex simplifiée était intentionnelle, vous pouvez utiliser :
            // const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;


            if (!emailRegex.test(email)) {
                alert("Veuillez entrer une adresse email valide.");
                e.preventDefault();
                return;
            }

            
        });
    }
});