from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove, new_session
from PIL import Image
import io

app = FastAPI()

# Дозволити CORS-запити
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Створення сесії з полегшеною моделлю u2netp
session = new_session(model_name="u2netp")

@app.post("/remove")
async def remove_background(file: UploadFile = File(...)):
    try:
        # Читання байтів з файлу
        input_data = await file.read()
        image = Image.open(io.BytesIO(input_data)).convert("RGBA")

        # Зменшення розміру для оптимізації RAM
        MAX_SIZE = (600, 600)
        image.thumbnail(MAX_SIZE)

        # Перетворення у PNG-байти
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()

        # Видалення фону через rembg
        output_bytes = remove(img_bytes, session=session)

        # Відкриття обробленого зображення
        output_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

        # Обрізання прозорих пікселів по краях
        bbox = output_image.getbbox()
        if bbox:
            output_image = output_image.crop(bbox)

        # Підготовка відповіді
        result_buffer = io.BytesIO()
        output_image.save(result_buffer, format="PNG")
        result_buffer.seek(0)

        return StreamingResponse(result_buffer, media_type="image/png", headers={
            "Content-Disposition": "attachment; filename=no_background.png"
        })

    except Exception as e:
        return {"error": str(e)}
