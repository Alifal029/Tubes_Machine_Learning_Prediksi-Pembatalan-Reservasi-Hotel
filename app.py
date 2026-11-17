from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "model_kelompok_6.joblib"

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"File model tidak ditemukan di {MODEL_PATH}. Pastikan model_kelompok_6.joblib tersedia di folder model/."
    )

# Model dimuat satu kali saat aplikasi dimulai
model = joblib.load(MODEL_PATH)

app = FastAPI(
    title="Hotel Booking Cancellation Prediction",
    description="API Machine Learning untuk prediksi status pembatalan reservasi hotel - Kelompok 6.",
    version="1.0.0",
)

# Mount folder static untuk melayani file CSS, JavaScript, dan aset web
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


class HotelBookingInput(BaseModel):
    hotel: Literal["City Hotel", "Resort Hotel"] = Field(
        ..., description="Tipe hotel yang dipesan"
    )
    lead_time: int = Field(
        default=30, ge=0, description="Jumlah hari antara tanggal pemesanan dan kedatangan (lead time)"
    )
    arrival_date_month: Literal[
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ] = Field(..., description="Bulan rencana kedatangan")
    stays_in_weekend_nights: int = Field(
        default=1, ge=0, description="Jumlah malam menginap di akhir pekan (Sabtu/Minggu)"
    )
    stays_in_week_nights: int = Field(
        default=2, ge=0, description="Jumlah malam menginap di hari kerja (Senin-Jumat)"
    )
    adults: int = Field(
        default=2, ge=0, description="Jumlah tamu dewasa"
    )
    children: float = Field(
        default=0.0, ge=0.0, description="Jumlah anak-anak"
    )
    meal: Literal["BB", "FB", "HB", "SC", "Undefined"] = Field(
        ..., description="Paket makanan yang dipesan (BB: Bed & Breakfast, FB: Full Board, HB: Half Board, SC: Self Catering, Undefined: Lainnya)"
    )
    market_segment: Literal[
        "Aviation",
        "Complementary",
        "Corporate",
        "Direct",
        "Groups",
        "Offline TA/TO",
        "Online TA",
        "Undefined",
    ] = Field(..., description="Segmen pasar pemesanan")
    distribution_channel: Literal[
        "Corporate", "Direct", "GDS", "TA/TO", "Undefined"
    ] = Field(..., description="Saluran distribusi pemesanan")
    deposit_type: Literal["No Deposit", "Non Refund", "Refundable"] = Field(
        ..., description="Tipe deposit jaminan pemesanan"
    )
    customer_type: Literal[
        "Contract", "Group", "Transient", "Transient-Party"
    ] = Field(..., description="Kategori/tipe pelanggan")


@app.get("/", include_in_schema=False)
def home():
    index_file = BASE_DIR / "static" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Selamat datang di API Prediksi Pembatalan Reservasi Hotel - Kelompok 6.",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "features": list(getattr(model, "feature_names_in_", [])),
    }


@app.post("/predict")
def predict(payload: HotelBookingInput):
    try:
        # Konversi payload menjadi DataFrame dengan mempertahankan nama fitur training
        row = pd.DataFrame([payload.model_dump()])

        # Prediksi kelas: 0 = Tidak Dibatalkan, 1 = Dibatalkan
        class_id = int(model.predict(row)[0])

        probability_cancel = None
        probability_not_cancel = None
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(row)[0]
            probability_not_cancel = float(probs[0])
            probability_cancel = float(probs[1])

        is_canceled = class_id == 1
        status_text = "Dibatalkan" if is_canceled else "Tidak Dibatalkan"

        return {
            "class_id": class_id,
            "prediction": status_text,
            "is_canceled": is_canceled,
            "probability_cancel": (
                round(probability_cancel, 4) if probability_cancel is not None else None
            ),
            "probability_not_cancel": (
                round(probability_not_cancel, 4) if probability_not_cancel is not None else None
            ),
            "disclaimer": (
                "Prototipe akademik Machine Learning Kelompok 6 untuk analisis "
                "dan prediksi risiko pembatalan reservasi hotel."
            ),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan saat memproses prediksi: {str(exc)}",
        )
