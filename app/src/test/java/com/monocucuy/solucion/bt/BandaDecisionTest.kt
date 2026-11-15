package com.monocucuy.solucion.bt

import org.junit.Assert.assertEquals
import org.junit.Test

class BandaDecisionTest {
    @Test fun puntajeBajoVaARevision() = assertEquals('R', letraParaBanda(79))
    @Test fun puntajeJustoEnElUmbralSigueDerecho() = assertEquals('A', letraParaBanda(80))
    @Test fun puntajeAltoSigueDerecho() = assertEquals('A', letraParaBanda(100))
    @Test fun puntajeCeroVaARevision() = assertEquals('R', letraParaBanda(0))
}
