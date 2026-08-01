# Catálogo Meta · Miles de Colores

## Activación
1. Sube todos los archivos de este proyecto al repositorio `catalogo-meta`.
2. Ve a **Settings → Pages**.
3. En **Build and deployment**, selecciona **Deploy from a branch**.
4. Elige `main` y `/docs`, y guarda.
5. Ve a **Actions → Actualizar catálogo Meta → Run workflow**.

El feed se publicará en:

`https://milesdecolores.github.io/catalogo-meta/catalogo-meta.csv`

Después añádelo en Meta Commerce Manager como feed mediante URL y programa una actualización diaria.

La automatización lee:
`https://www.milesdecolores.com/sitemap.products.xml`

Nota: el feed publica una referencia por página de producto. Las tallas o variantes se seleccionan en la web de SumUp.
