import express from 'express';
import { createClient } from '@supabase/supabase-js';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Reemplaza con tus credenciales de la consola de Supabase (Settings -> API)
const SUPABASE_URL = "https://bfnarvhyskmsotmoncqy.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJmbmFydmh5c2ttc290bW9uY3F5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMxOTk3NjYsImV4cCI6MjA4ODc3NTc2Nn0.D58bwiR7_-zBmICD4zSHPO554tq4RrI4g_-qHCX2keE";

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

app.use(cors());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/dibujos', async (req, res) => {
    try {
        const { data, error } = await supabase.storage
            .from('dibujos')
            .list('', {
                limit: 100,
                offset: 0,
                sortBy: { column: 'created_at', order: 'desc' },
            });
        
        if (error) {
            console.error('Error fetching drawings:', error);
            return res.status(500).json({ error: 'Error fetching drawings' });
        }

        if (!data || data.length === 0) {
            return res.json([]);
        }

        // Filtramos para solo devolver imágenes, ignorando carpetas o archivos vacíos
        const imageFiles = data.filter(item => item.name && (item.name.endsWith('.png') || item.name.endsWith('.jpg') || item.name.endsWith('.jpeg')));

        // Obtener la URL pública para cada imagen
        const dibujos = imageFiles.map(file => {
            const { data: publicUrlData } = supabase.storage.from('dibujos').getPublicUrl(file.name);
            return {
                id: file.id,
                name: file.name,
                url: publicUrlData.publicUrl,
                created_at: file.created_at
            };
        });

        res.json(dibujos);

    } catch (err) {
        console.error('Unexpected error:', err);
        res.status(500).json({ error: 'Unexpected error getting drawings' });
    }
});

app.listen(PORT, () => {
    console.log(`Servidor iniciado en http://localhost:${PORT}`);
});
