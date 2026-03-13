document.addEventListener('DOMContentLoaded', () => {
    const gallery = document.getElementById('gallery');
    const loader = document.getElementById('loader');
    const emptyState = document.getElementById('empty-state');
    const errorState = document.getElementById('error-state');
    const refreshBtn = document.getElementById('refreshBtn');

    // Modal elements
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImg');
    const modalCaption = document.getElementById('modalCaption');
    const closeBtn = document.querySelector('.close-btn');

    // Fetch and display drawings
    const fetchDrawings = async () => {
        try {
            // UI States
            refreshBtn.classList.add('spinning');
            gallery.classList.remove('loaded');
            
            if (gallery.children.length === 0) {
                loader.classList.remove('hidden');
                emptyState.classList.add('hidden');
                errorState.classList.add('hidden');
            }

            const response = await fetch('/api/dibujos');
            
            if (!response.ok) {
                throw new Error('Failed to fetch drawings');
            }

            const data = await response.json();
            
            loader.classList.add('hidden');
            refreshBtn.classList.remove('spinning');

            if (data.length === 0) {
                emptyState.classList.remove('hidden');
                gallery.innerHTML = '';
                return;
            }

            // Clear current gallery
            gallery.innerHTML = '';
            
            // Build gallery items
            data.forEach((item, index) => {
                const card = document.createElement('div');
                card.className = 'card';
                card.style.animationDelay = `${index * 0.1}s`;

                // Formatear la fecha
                const date = new Date(item.created_at);
                const formattedDate = new Intl.DateTimeFormat('es-ES', {
                    dateStyle: 'medium',
                    timeStyle: 'short'
                }).format(date);

                // Nombre legible (remueve la extension y los guiones bajos)
                const legibleName = item.name
                    .replace(/\.[^/.]+$/, "") // quita extension
                    .replace(/_/g, " ");      // reemplaza guiones bajos

                card.innerHTML = `
                    <div class="card-img-wrapper">
                        <img src="${item.url}" alt="${legibleName}" loading="lazy">
                    </div>
                    <div class="card-info">
                        <h3 class="card-title">${legibleName}</h3>
                        <p class="card-date">${formattedDate}</p>
                    </div>
                `;

                // Add click event to open modal
                card.addEventListener('click', () => {
                    openModal(item.url, legibleName);
                });

                gallery.appendChild(card);
            });

            // Pequeño delay para el efecto de entrada
            setTimeout(() => {
                gallery.classList.add('loaded');
            }, 50);

        } catch (error) {
            console.error('Error fetching data:', error);
            loader.classList.add('hidden');
            refreshBtn.classList.remove('spinning');
            
            if (gallery.children.length === 0) {
                errorState.classList.remove('hidden');
            }
        }
    };

    // Modal logic
    const openModal = (url, caption) => {
        modalImg.src = url;
        modalCaption.textContent = caption;
        modal.classList.remove('hidden');
        // Pequeño delay para la transición
        setTimeout(() => modal.classList.add('show'), 10);
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    };

    const closeModal = () => {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.classList.add('hidden');
            modalImg.src = '';
        }, 300); // Wait for transition
        document.body.style.overflow = 'auto'; // Restore scrolling
    };

    // Event Listeners
    refreshBtn.addEventListener('click', fetchDrawings);
    
    closeBtn.addEventListener('click', closeModal);
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });

    // Initial fetch
    fetchDrawings();
});
