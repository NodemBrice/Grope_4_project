/**
 * Fonction utilitaire pour cacher l'overlay d'introduction et afficher le contenu principal.
 * Cette fonction est déplacée à l'extérieur du DOMContentLoaded pour une meilleure organisation.
 */
const showContent = () => {
    const introOverlay = document.getElementById('intro-overlay');
    const header = document.querySelector('header');
    const main = document.querySelector('main');
    const footer = document.querySelector('footer');
    
    // Utilisation de l'Optional Chaining (?) pour plus de concision lors de la suppression de classes.
    // L'overlay est caché de manière définitive.
    if (introOverlay) {
        // Définir display: none est plus fiable que la classe 'hidden' pour un élément destiné à disparaître.
        introOverlay.style.display = 'none'; 
    }
    
    header?.classList.remove('hidden');
    main?.classList.remove('hidden');
    footer?.classList.remove('hidden');
};

/**
 * Fonction isolée pour gérer la logique de validation du formulaire de contact.
 * Retourne false et empêche l'envoi si la validation échoue.
 */
const validateContactForm = (e) => {
    // Récupération des valeurs en s'assurant qu'elles sont trimées
    const name = document.getElementById("name")?.value.trim();
    const email = document.getElementById("email")?.value.trim();
    // Le champ message n'est pas obligatoire dans cette validation
    // const message = document.getElementById("message")?.value.trim(); 

    // Vérification des champs obligatoires
    if (!name || !email) {
        alert("Veuillez remplir tous les champs obligatoires (Nom et Email).");
        e.preventDefault();
        return false;
    }

    // Validation basique de l'email
    // Utilisation d'une regex un peu plus robuste que la version très simple
    const emailRegex = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
    if (!emailRegex.test(email)) {
        alert("Veuillez entrer une adresse email valide.");
        e.preventDefault();
        return false;
    }

    // Si toutes les validations passent, le formulaire est envoyé
    return true;
};


// -------------------------------------------------------------------------
// Point d'entrée principal : s'assure que le DOM est complètement chargé
// -------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. Gestion de la cinématique intro ---
    const introVideo = document.getElementById('intro-video');
    const skipButton = document.getElementById('skip-intro');

    if (introVideo) {
        // Exécute showContent à la fin de la vidéo
        introVideo.addEventListener('ended', showContent);

        // Bouton skip
        if (skipButton) {
            skipButton.addEventListener('click', () => {
                introVideo.pause(); // Arrête la vidéo immédiatement
                showContent();      // Affiche le contenu
            });
        }

        // Pour gérer l'autoplay bloqué
        introVideo.play().catch(error => {
            console.warn('Autoplay bloqué par le navigateur:', error);
            // Ici, vous pourriez rendre le bouton 'skip' ou 'play' visible si la vidéo ne démarre pas
        });
    }

    // --- 2. Menu hamburger ---
    const menuToggle = document.getElementById("menu-toggle");
    const navMenu = document.getElementById("nav-menu");

    if (menuToggle && navMenu) {
        menuToggle.addEventListener("click", () => {
            // Bascule la classe 'active' pour afficher/cacher le menu via CSS
            navMenu.classList.toggle("active");
            menuToggle.classList.toggle("active"); // Optionnel : pour changer l'icône du toggle
        });
    }

    // --- 3. Validation du formulaire de contact ---
    const form = document.getElementById("contact-form");
    if (form) {
        // Utilise la fonction de validation isolée comme gestionnaire d'événement
        form.addEventListener("submit", validateContactForm);
    }
});