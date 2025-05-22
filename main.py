from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from rembg import remove, new_session
from PIL import Image
import io

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = new_session(model_name="u2netp")

@app.post("/remove")
async def remove_background(file: UploadFile = File(...)):
    input_data = await file.read()
    image = Image.open(io.BytesIO(input_data)).convert("RGBA")
    image.thumbnail((600, 600))

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    output_bytes = remove(img_bytes, session=session)
    output_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

    bbox = output_image.getbbox()
    if bbox:
        output_image = output_image.crop(bbox)

    result_buffer = io.BytesIO()
    output_image.save(result_buffer, format="PNG")
    result_buffer.seek(0)

    return StreamingResponse(result_buffer, media_type="image/png")
