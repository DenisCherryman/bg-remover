from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove, new_session
from PIL import Image
import io

app = FastAPI()

# Дозволити CORS-запити
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware для обробки "дивних" preflight-запитів
@app.middleware("http")
async def catch_all_requests(request: Request, call_next):
    if request.method == "OPTIONS":
        return PlainTextResponse("ok", status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        })
    return await call_next(request)

# Відповідь на корінь для health-check Cloud Run
@app.get("/")
def root():
    return {"status": "ok"}

# Обробка preflight вручну (не обов'язково, але залишимо)
@app.options("/remove")
async def preflight_handler():
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# Створення сесії з полегшеною моделлю
session = new_session(model_name="u2netp")

@app.post("/remove")
async def remove_background(file: UploadFile = File(...)):
    try:
        input_data = await file.read()
        image = Image.open(io.BytesIO(input_data)).convert("RGBA")

        # Оптимізація розміру
        MAX_SIZE = (600, 600)
        image.thumbnail(MAX_SIZE)

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

        return StreamingResponse(result_buffer, media_type="image/png", headers={
            "Content-Disposition": "attachment; filename=no_background.png"
        })

    except Exception as e:
        return {"error": str(e)}
