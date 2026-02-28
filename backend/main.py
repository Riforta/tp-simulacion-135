from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

from simulation import run_single_simulation, run_sweep, SimConfig

app = FastAPI(title="TP Simulación - Ensambladores")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SingleSimRequest(BaseModel):
    cant_ensambladores: int = Field(..., ge=1, le=200)
    minutos: float = Field(480, gt=0)
    seed: int | None = None

    # Parámetros del modelo (distribuciones)
    ensamble_min: float = Field(25, gt=0)
    ensamble_max: float = Field(35, gt=0)
    horno_min: float = Field(6, gt=0)
    horno_max: float = Field(10, gt=0)

    # Regla del motor (empates)
    prioridad_empate: Literal["ensamble", "horno"] = "ensamble"


class SweepRequest(BaseModel):
    max_ensambladores: int = Field(10, ge=1, le=200)
    minutos: float = Field(480, gt=0)
    repeticiones: int = Field(100, ge=1, le=10000)
    seed_base: int | None = 123

    # Parámetros del modelo (distribuciones)
    ensamble_min: float = Field(25, gt=0)
    ensamble_max: float = Field(35, gt=0)
    horno_min: float = Field(6, gt=0)
    horno_max: float = Field(10, gt=0)

    # Regla del motor (empates)
    prioridad_empate: Literal["ensamble", "horno"] = "ensamble"


def _validar_rangos(req) -> None:
    if req.ensamble_min >= req.ensamble_max:
        raise HTTPException(status_code=422, detail="ensamble_min debe ser menor que ensamble_max")
    if req.horno_min >= req.horno_max:
        raise HTTPException(status_code=422, detail="horno_min debe ser menor que horno_max")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/simulate_once")
def simulate_once(req: SingleSimRequest):
    _validar_rangos(req)

    config = SimConfig(
        ensamble_min=req.ensamble_min,
        ensamble_max=req.ensamble_max,
        horno_min=req.horno_min,
        horno_max=req.horno_max,
        prioridad_empate=req.prioridad_empate,
    )

    return run_single_simulation(
        cant_ensambladores=req.cant_ensambladores,
        minutos=req.minutos,
        seed=req.seed,
        config=config,
    )


@app.post("/simulate_sweep")
def simulate_sweep(req: SweepRequest):
    _validar_rangos(req)

    config = SimConfig(
        ensamble_min=req.ensamble_min,
        ensamble_max=req.ensamble_max,
        horno_min=req.horno_min,
        horno_max=req.horno_max,
        prioridad_empate=req.prioridad_empate,
    )

    return run_sweep(
        max_ensambladores=req.max_ensambladores,
        minutos=req.minutos,
        repeticiones=req.repeticiones,
        seed_base=req.seed_base,
        config=config,
    )