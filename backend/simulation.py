from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List
import random


# -------------------------
# Configuración del modelo
# -------------------------
@dataclass(frozen=True)
class SimConfig:
    # Distribuciones (Uniforme)
    ensamble_min: float = 25.0
    ensamble_max: float = 35.0
    horno_min: float = 6.0
    horno_max: float = 10.0

    # Regla para empates entre FinHorneado y FinEnsamble en el mismo reloj
    # "ensamble" mantiene tu comportamiento actual
    prioridad_empate: str = "ensamble"  # "ensamble" | "horno"


class EstadoEnsamblador(str, Enum):
    ENSAMBLANDO = "Ensamblando"
    ESPERANDO_HORNO = "EsperandoHorno"
    ESPERANDO_PIEZA_HORNEADA = "EsperandoPiezaHorneada"


class EstadoHorno(str, Enum):
    LIBRE = "Libre"
    HORNEANDO = "Horneando"


class TipoEvento(str, Enum):
    INICIO = "inicio"
    FIN_ENSAMBLE = "FinEnsamble"
    FIN_HORNEADO = "FinHorneado"
    FIN = "Fin"


def estado_componente_label(estado: EstadoEnsamblador) -> str:
    if estado == EstadoEnsamblador.ENSAMBLANDO:
        return "Siendo Ensamblada"
    if estado == EstadoEnsamblador.ESPERANDO_HORNO:
        return "Esperando Horno"
    if estado == EstadoEnsamblador.ESPERANDO_PIEZA_HORNEADA:
        return "En Horno"
    return str(estado)


def estado_horno_label(estado: EstadoHorno) -> str:
    if estado == EstadoHorno.LIBRE:
        return "Libre"
    if estado == EstadoHorno.HORNEANDO:
        return "Ocupado"
    return str(estado)


@dataclass
class Ensamblador:
    config: SimConfig
    hora_inicio: float = 0.0
    rnd_ensamble_real: float | None = None
    duracion: float = 0.0
    hora_fin: float = 0.0
    estado: EstadoEnsamblador = EstadoEnsamblador.ENSAMBLANDO

    def __post_init__(self) -> None:
        self.comenzar_ensamble(0.0)

    def calcular_duracion_ensamble(self) -> float:
        # Uniforme [ensamble_min, ensamble_max]
        self.rnd_ensamble_real = random.random()
        a = self.config.ensamble_min
        b = self.config.ensamble_max
        return round(a + (b - a) * self.rnd_ensamble_real, 2)

    def comenzar_ensamble(self, clock: float) -> None:
        self.hora_inicio = round(clock, 2)
        self.duracion = self.calcular_duracion_ensamble()
        self.hora_fin = round(clock + self.duracion, 2)
        self.estado = EstadoEnsamblador.ENSAMBLANDO

    def rnd_ensamble_mostrar(self) -> str:
        if self.rnd_ensamble_real is None:
            return "-"
        return f"{self.rnd_ensamble_real:.2f}"


@dataclass
class Horno:
    config: SimConfig
    hora_inicio: float = 0.0
    rnd_horno_real: float | None = None
    hora_fin: float = 0.0
    duracion: float = 0.0
    estado: EstadoHorno = EstadoHorno.LIBRE

    def calcular_duracion_horneado(self) -> float:
        # Uniforme [horno_min, horno_max]
        self.rnd_horno_real = random.random()
        a = self.config.horno_min
        b = self.config.horno_max
        return round(a + (b - a) * self.rnd_horno_real, 2)

    def comenzar_horneado(self, clock: float) -> None:
        self.hora_inicio = round(clock, 2)
        self.duracion = self.calcular_duracion_horneado()
        self.hora_fin = round(clock + self.duracion, 2)
        self.estado = EstadoHorno.HORNEANDO

    def rnd_horno_mostrar(self) -> str:
        if self.rnd_horno_real is None:
            return "-"
        return f"{self.rnd_horno_real:.2f}"


class Simulacion:
    def __init__(
        self,
        cantidad_ensambladores: int,
        fin_dia_laboral: float,
        seed: int | None = None,
        config: SimConfig | None = None,
    ) -> None:
        if seed is not None:
            random.seed(seed)

        self.config = config or SimConfig()

        self.reloj: float = 0.0
        self.cantidad_ensambladores = cantidad_ensambladores
        self.cantidad_piezas: int = 0
        self.fin_dia_laboral: float = fin_dia_laboral

        self.horno = Horno(config=self.config)
        self.ensambladores: List[Ensamblador] = []
        self.cola: int = 0
        self.tipo_evento: TipoEvento = TipoEvento.INICIO
        self.tabla: List[Dict[str, Any]] = []

        # Flags visuales del evento actual (para no arrastrar RND/Tiempo)
        self._ensambladores_con_nuevo_ensamble: set[int] = set()
        self._horno_con_nuevo_horneado: bool = False

        self.iniciar_simulacion()

    def generar_ensambladores(self) -> None:
        self.ensambladores = [Ensamblador(config=self.config) for _ in range(self.cantidad_ensambladores)]

    def iniciar_simulacion(self) -> None:
        self.tipo_evento = TipoEvento.INICIO
        self.reloj = 0.0
        self.cola = 0
        self.cantidad_piezas = 0
        self.horno = Horno(config=self.config, hora_inicio=0.0, hora_fin=0.0, duracion=0.0, estado=EstadoHorno.LIBRE)
        self.generar_ensambladores()

        # En la fila inicial, todos arrancan un ensamble
        self._ensambladores_con_nuevo_ensamble = set(range(len(self.ensambladores)))
        self._horno_con_nuevo_horneado = False
        self.cargar_tabla()

        while self.reloj < self.fin_dia_laboral:
            if not self.simular_paso_a_paso():
                break

    def simular_paso_a_paso(self) -> bool:
        hora_prox = self.hora_proximo_evento()
        if hora_prox is None:
            self.tipo_evento = TipoEvento.FIN
            return False

        self.tipo_evento = self.proximo_evento(hora_prox)
        self.reloj = hora_prox

        if self.tipo_evento == TipoEvento.FIN_ENSAMBLE:
            self.fin_ensamble()
        elif self.tipo_evento == TipoEvento.FIN_HORNEADO:
            self.fin_horneado()

        return True

    def hora_proximo_evento(self) -> float | None:
        candidatos: List[float] = []

        if self.horno.estado == EstadoHorno.HORNEANDO and self.horno.hora_fin > self.reloj:
            candidatos.append(self.horno.hora_fin)

        for e in self.ensambladores:
            if e.estado == EstadoEnsamblador.ENSAMBLANDO and e.hora_fin > self.reloj:
                candidatos.append(e.hora_fin)

        if not candidatos:
            return None

        return min(candidatos)

    def proximo_evento(self, hora: float) -> TipoEvento:
        hay_horno = (self.horno.estado == EstadoHorno.HORNEANDO and self.horno.hora_fin == hora)
        hay_ensamble = any(
            e.estado == EstadoEnsamblador.ENSAMBLANDO and e.hora_fin == hora for e in self.ensambladores
        )

        if hay_horno and hay_ensamble:
            return TipoEvento.FIN_ENSAMBLE if self.config.prioridad_empate == "ensamble" else TipoEvento.FIN_HORNEADO
        if hay_ensamble:
            return TipoEvento.FIN_ENSAMBLE
        if hay_horno:
            return TipoEvento.FIN_HORNEADO
        return TipoEvento.FIN

    def fin_ensamble(self) -> None:
        # Reseteo flags visuales del evento actual
        self._ensambladores_con_nuevo_ensamble.clear()
        self._horno_con_nuevo_horneado = False

        ensamblador_que_termino = None
        for e in self.ensambladores:
            if e.estado == EstadoEnsamblador.ENSAMBLANDO and e.hora_fin == self.reloj:
                ensamblador_que_termino = e
                break

        if ensamblador_que_termino is None:
            self.cargar_tabla()
            return

        if self.cola == 0:
            if self.horno.estado == EstadoHorno.LIBRE:
                # Entra directo al horno
                self.horno.comenzar_horneado(self.reloj)
                self._horno_con_nuevo_horneado = True
                ensamblador_que_termino.estado = EstadoEnsamblador.ESPERANDO_PIEZA_HORNEADA
            else:
                # Horno ocupado -> cola
                self.cola += 1
                ensamblador_que_termino.estado = EstadoEnsamblador.ESPERANDO_HORNO
        else:
            # Ya había cola -> cola
            self.cola += 1
            ensamblador_que_termino.estado = EstadoEnsamblador.ESPERANDO_HORNO

        self.cargar_tabla()

    def fin_horneado(self) -> None:
        # Reseteo flags visuales del evento actual
        self._ensambladores_con_nuevo_ensamble.clear()
        self._horno_con_nuevo_horneado = False

        # Se termina una pieza
        self.cantidad_piezas += 1

        # Libero al ensamblador cuya pieza estaba en horno -> comienza nuevo ensamble
        for idx, e in enumerate(self.ensambladores):
            if e.estado == EstadoEnsamblador.ESPERANDO_PIEZA_HORNEADA:
                e.comenzar_ensamble(self.reloj)
                self._ensambladores_con_nuevo_ensamble.add(idx)
                break

        # ¿Hay cola para el horno?
        if self.cola == 0:
            self.horno.estado = EstadoHorno.LIBRE
        else:
            esperando = [e for e in self.ensambladores if e.estado == EstadoEnsamblador.ESPERANDO_HORNO]
            if esperando:
                # "FIFO" aproximado: el que está esperando hace más tiempo -> menor hora_fin de ensamble
                e_siguiente = min(esperando, key=lambda x: x.hora_fin)
                e_siguiente.estado = EstadoEnsamblador.ESPERANDO_PIEZA_HORNEADA
                self.cola -= 1
                self.horno.comenzar_horneado(self.reloj)
                self._horno_con_nuevo_horneado = True
            else:
                self.horno.estado = EstadoHorno.LIBRE

        self.cargar_tabla()

    def cargar_tabla(self) -> None:
        row: Dict[str, Any] = {
            "fila": len(self.tabla),  # 0 = inicialización
            "evento": self.tipo_evento.value,
            "reloj": round(self.reloj, 2),
        }

        # Bloque por componente (uno por ensamblador)
        for i, e in enumerate(self.ensambladores, start=1):
            idx = i - 1

            # RND y tiempo de ensamble: SOLO cuando se generan en ESTE evento
            if idx in self._ensambladores_con_nuevo_ensamble:
                row[f"rndEnsamble{i}"] = e.rnd_ensamble_mostrar()
                row[f"tiempoEnsamble{i}"] = round(e.duracion, 2)
            else:
                row[f"rndEnsamble{i}"] = "-"
                row[f"tiempoEnsamble{i}"] = "-"

            # Fin de ensamble: se mantiene si el componente está siendo ensamblado
            if e.estado == EstadoEnsamblador.ENSAMBLANDO:
                row[f"finEnsamble{i}"] = round(e.hora_fin, 2)
            else:
                row[f"finEnsamble{i}"] = "-"

            # Estado visual del componente (al final del bloque)
            row[f"estadoComp{i}"] = estado_componente_label(e.estado)

        # Bloque horno
        row["estadoHorno"] = estado_horno_label(self.horno.estado)

        # RND y tiempo de horno: SOLO cuando arranca horneado en ESTE evento
        if self._horno_con_nuevo_horneado:
            row["rndHorno"] = self.horno.rnd_horno_mostrar()
            row["tiempoHorno"] = round(self.horno.duracion, 2)
        else:
            row["rndHorno"] = "-"
            row["tiempoHorno"] = "-"

        # Fin de horno: se mantiene si está ocupado
        if self.horno.estado == EstadoHorno.HORNEANDO:
            row["finHorno"] = round(self.horno.hora_fin, 2)
        else:
            row["finHorno"] = "-"

        row["cola"] = self.cola
        row["cantPiezas"] = self.cantidad_piezas

        self.tabla.append(row)

    def get_tabla(self) -> List[Dict[str, Any]]:
        return self.tabla

    def get_cant_piezas(self) -> int:
        return self.cantidad_piezas


def run_single_simulation(
    cant_ensambladores: int,
    minutos: float = 480,
    seed: int | None = None,
    config: SimConfig | None = None,
) -> Dict[str, Any]:
    sim = Simulacion(cant_ensambladores, minutos, seed=seed, config=config)
    rows = sim.get_tabla()

    columns = list(rows[0].keys()) if rows else []
    if "fila" in columns:
        columns = ["fila"] + [c for c in columns if c != "fila"]

    return {
        "cant_ensambladores": cant_ensambladores,
        "minutos": minutos,
        "cant_piezas": sim.get_cant_piezas(),
        "columns": columns,
        "rows": rows,
    }


def run_sweep(
    max_ensambladores: int,
    minutos: float = 480,
    repeticiones: int = 100,
    seed_base: int | None = 123,
    config: SimConfig | None = None,
) -> Dict[str, Any]:
    summary_rows: List[Dict[str, Any]] = []
    mejor_n = 0
    mejor_prom = -1.0

    for n in range(1, max_ensambladores + 1):
        resultados: List[int] = []

        for r in range(repeticiones):
            seed = None if seed_base is None else (seed_base + n * 100000 + r)
            sim = Simulacion(n, minutos, seed=seed, config=config)
            resultados.append(sim.get_cant_piezas())

        promedio = round(sum(resultados) / len(resultados), 4)
        minimo = min(resultados)
        maximo = max(resultados)

        row = {
            "cantEnsambladores": n,
            "promedioPiezas": promedio,
            "minPiezas": minimo,
            "maxPiezas": maximo,
            "repeticiones": repeticiones,
        }
        summary_rows.append(row)

        if promedio > mejor_prom:
            mejor_prom = promedio
            mejor_n = n

    return {
        "optimo": mejor_n,
        "criterio": "Mayor promedio de piezas en las replicaciones",
        "columns": list(summary_rows[0].keys()) if summary_rows else [],
        "rows": summary_rows,
    }