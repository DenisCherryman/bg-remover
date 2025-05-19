from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove
from PIL import Image
import uuid
import os
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.post("/remove")
async def remove_background(file: UploadFile = File(...)):
    try:
        # Зчитування байтів
        input_data = await file.read()
        image = Image.open(io.BytesIO(input_data)).convert("RGBA")

        # Обмеження розміру зображення для економії RAM
        MAX_SIZE = (800, 800)
        image.thumbnail(MAX_SIZE)

        # Конвертуємо у PNG-байти для rembg
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        output_data = remove(buffered.getvalue())

        # Збереження результату
        filename = f"no_bg_{uuid.uuid4().hex}.png"
        with open(filename, "wb") as out_file:
            out_file.write(output_data)

        return FileResponse(filename, media_type="image/png", filename="no_background.png")

    except Exception as e:
        return {"error": str(e)}
