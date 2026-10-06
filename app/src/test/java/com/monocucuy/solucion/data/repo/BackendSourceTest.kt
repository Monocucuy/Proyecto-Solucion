package com.monocucuy.solucion.data.repo

import com.monocucuy.solucion.data.local.HashCacheEntity
import com.monocucuy.solucion.data.local.HashDao
import com.monocucuy.solucion.data.remote.BackendApi
import com.monocucuy.solucion.data.remote.BackendResult
import com.monocucuy.solucion.data.remote.BatchRequest
import com.monocucuy.solucion.data.remote.BatchResponse
import com.monocucuy.solucion.data.remote.VirusTotalApi
import com.monocucuy.solucion.data.remote.VtResponse
import com.monocucuy.solucion.domain.Rep
import com.monocucuy.solucion.domain.Verdict
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.SerializationException
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import retrofit2.Response
import java.io.IOException

private fun h(c: Char) = c.toString().repeat(64)
private const val EICAR = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"

private class FakeDao(val rows: MutableMap<String, HashCacheEntity> = mutableMapOf()) : HashDao {
    override suspend fun get(sha: String) = rows[sha]
    override suspend fun upsert(e: HashCacheEntity) { rows[e.sha256] = e }
}

private val clean = BackendResult("done", "CLEAN", found = true)
private val pending = BackendResult("pending")
private fun malicious(n: Int) = BackendResult("done", "MALICIOUS", found = true, malicious = n)
private fun ok(vararg r: Pair<String, BackendResult>) =
    Response.success(BatchResponse(r.toMap(), r.count { it.second.status == "pending" }))
private fun httpError(code: Int) = Response.error<BatchResponse>(code, "".toResponseBody())

/** Cada llamada a batch consume la siguiente respuesta del guion (la última se repite). */
private class ScriptedApi(private val script: List<(BatchRequest) -> Response<BatchResponse>>) : BackendApi {
    val requests = mutableListOf<BatchRequest>()
    override suspend fun batch(req: BatchRequest): Response<BatchResponse> {
        requests += req
        return script[minOf(requests.size - 1, script.lastIndex)](req)
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
class BackendSourceTest {

    private fun TestScope.source(api: BackendApi, dao: HashDao = FakeDao(), maxWaitMs: Long = 120_000) =
        BackendSource(api, dao, pollMs = 4_000, maxWaitMs = maxWaitMs, clock = { currentTime })

    @Test fun `resuelve en lote y cachea el resultado`() = runTest {
        val dao = FakeDao()
        val api = ScriptedApi(listOf({ _ -> ok(EICAR to malicious(62), h('a') to clean) }))
        val out = source(api, dao).lookupAll(listOf(EICAR, h('a'))) { _, _ -> }
        assertEquals(Verdict.MALICIOUS, out[EICAR]!!.verdict)
        assertEquals(62, out[EICAR]!!.malicious)
        assertEquals(Verdict.CLEAN, out[h('a')]!!.verdict)
        assertEquals(1, api.requests.size)
        assertEquals(setOf(EICAR, h('a')), dao.rows.keys)
    }

    @Test fun `solo viajan hashes en el body`() {
        assertEquals("""{"hashes":["${h('a')}"]}""", Json.encodeToString(BatchRequest(listOf(h('a')))))
    }

    @Test fun `lo ya cacheado no toca la red`() = runTest {
        val dao = FakeDao(mutableMapOf(h('a') to HashCacheEntity(h('a'), true, 5, 0, checkedAt = 0)))
        val api = ScriptedApi(listOf({ _ -> error("no deberia llamarse") }))
        val out = source(api, dao).lookupAll(listOf(h('a'))) { _, _ -> }
        assertEquals(Verdict.MALICIOUS, out[h('a')]!!.verdict)
        assertEquals(0, api.requests.size)
    }

    @Test fun `cache vencido se vuelve a consultar`() = runTest {
        val dao = FakeDao(mutableMapOf(h('a') to HashCacheEntity(h('a'), true, 0, 0, checkedAt = -8L * 86_400_000)))
        val api = ScriptedApi(listOf({ _ -> ok(h('a') to clean) }))
        source(api, dao).lookupAll(listOf(h('a'))) { _, _ -> }
        assertEquals(1, api.requests.size)
    }

    @Test fun `sondea hasta que no quedan pendientes y solo re-pregunta lo pendiente`() = runTest {
        val api = ScriptedApi(listOf(
            { _ -> ok(h('a') to clean, h('b') to pending) },
            { _ -> ok(h('b') to pending) },
            { _ -> ok(h('b') to malicious(7)) },
        ))
        val progress = mutableListOf<Int>()
        val out = source(api).lookupAll(listOf(h('a'), h('b'))) { done, _ -> progress += done }
        assertEquals(3, api.requests.size)
        assertEquals(listOf(h('b')), api.requests[1].hashes)
        assertEquals(Verdict.MALICIOUS, out[h('b')]!!.verdict)
        assertEquals(8_000, currentTime) // 2 esperas de 4 s en tiempo virtual
        assertEquals(2, progress.last())
    }

    @Test fun `no encontrado queda UNKNOWN con found false, nunca limpio`() = runTest {
        val dao = FakeDao()
        val api = ScriptedApi(listOf({ _ -> ok(h('a') to BackendResult("done", "UNKNOWN", found = false)) }))
        val out = source(api, dao).lookupAll(listOf(h('a'))) { _, _ -> }
        assertEquals(Verdict.UNKNOWN, out[h('a')]!!.verdict)
        assertNull(out[h('a')]!!.error)
        // y sigue siendo UNKNOWN al leerlo del cache local
        val again = source(ScriptedApi(listOf({ _ -> error("no") })), dao).lookupAll(listOf(h('a'))) { _, _ -> }
        assertEquals(Verdict.UNKNOWN, again[h('a')]!!.verdict)
    }

    @Test fun `si el servidor sigue pendiente se rinde en maxWait con error pending y no cuelga`() = runTest {
        val api = ScriptedApi(listOf({ _ -> ok(h('a') to clean, h('b') to pending) }))
        val out = source(api, maxWaitMs = 20_000).lookupAll(listOf(h('a'), h('b'))) { _, _ -> }
        assertEquals(Verdict.CLEAN, out[h('a')]!!.verdict)
        assertEquals("pending", out[h('b')]!!.error)
        assertTrue(currentTime in 20_000..24_000)
    }

    @Test fun `unavailable es definitivo, no se sondea mas`() = runTest {
        val api = ScriptedApi(listOf({ _ -> ok(h('a') to BackendResult("unavailable", error = "upstream_error")) }))
        val out = source(api).lookupAll(listOf(h('a'))) { _, _ -> }
        assertEquals("unavailable", out[h('a')]!!.error)
        assertEquals(1, api.requests.size)
    }

    @Test fun `hash ausente en la respuesta se trata como pendiente`() = runTest {
        val api = ScriptedApi(listOf({ _ -> ok() }, { _ -> ok(h('a') to clean) }))
        val out = source(api).lookupAll(listOf(h('a'))) { _, _ -> }
        assertEquals(Verdict.CLEAN, out[h('a')]!!.verdict)
        assertEquals(2, api.requests.size)
    }

    @Test fun `401 y 403 da token, se aborta sin reintentar`() = runTest {
        for (code in listOf(401, 403)) {
            val api = ScriptedApi(listOf({ _ -> httpError(code) }))
            val out = source(api).lookupAll(listOf(h('a'), h('b'))) { _, _ -> }
            assertEquals("token", out[h('a')]!!.error); assertEquals("token", out[h('b')]!!.error)
            assertEquals(1, api.requests.size)
        }
    }

    @Test fun `429 da limit`() = runTest {
        val out = source(ScriptedApi(listOf({ _ -> httpError(429) }))).lookupAll(listOf(h('a'))) { _, _ -> }
        assertEquals("limit", out[h('a')]!!.error)
    }

    @Test fun `500, body vacio y json roto da unavailable sin crashear`() = runTest {
        val casos = listOf<(BatchRequest) -> Response<BatchResponse>>(
            { _ -> httpError(500) },
            { _ -> Response.success<BatchResponse>(null) },
            { _ -> throw SerializationException("json roto") },
        )
        for (c in casos) {
            val out = source(ScriptedApi(listOf(c))).lookupAll(listOf(h('a'))) { _, _ -> }
            assertEquals("unavailable", out[h('a')]!!.error)
        }
    }

    @Test fun `sin red da net`() = runTest {
        val out = source(ScriptedApi(listOf({ _ -> throw IOException("sin red") }))).lookupAll(listOf(h('a'))) { _, _ -> }
        assertEquals("net", out[h('a')]!!.error)
    }

    @Test fun `la red cae a mitad del sondeo y lo resuelto se conserva, lo demas es net`() = runTest {
        var n = 0
        val api = ScriptedApi(listOf(
            { _ -> ok(h('a') to clean, h('b') to pending) },
            { _ -> n++; throw IOException("cae") },
        ))
        val out = source(api).lookupAll(listOf(h('a'), h('b'))) { _, _ -> }
        assertEquals(Verdict.CLEAN, out[h('a')]!!.verdict)
        assertEquals("net", out[h('b')]!!.error)
    }

    @Test fun `mas de 100 hashes se parten en lotes de 100`() = runTest {
        val hashes = (0 until 250).map { it.toString(16).padStart(64, '0') }
        val api = ScriptedApi(listOf({ req -> ok(*req.hashes.map { it to clean }.toTypedArray()) }))
        val out = source(api).lookupAll(hashes) { _, _ -> }
        assertEquals(listOf(100, 100, 50), api.requests.map { it.hashes.size })
        assertEquals(250, out.size)
    }

    @Test fun `hashes repetidos se consultan una vez`() = runTest {
        val api = ScriptedApi(listOf({ _ -> ok(h('a') to clean) }))
        source(api).lookupAll(listOf(h('a'), h('a'), h('a'))) { _, _ -> }
        assertEquals(listOf(h('a')), api.requests[0].hashes)
    }

    @Test fun `veredicto desconocido o nulo del servidor da UNKNOWN`() = runTest {
        val api = ScriptedApi(listOf({ _ -> ok(h('a') to BackendResult("done", "RARO", found = true), h('b') to BackendResult("done", null)) }))
        val out = source(api).lookupAll(listOf(h('a'), h('b'))) { _, _ -> }
        assertEquals(Verdict.UNKNOWN, out[h('a')]!!.verdict)
        assertEquals(Verdict.UNKNOWN, out[h('b')]!!.verdict)
    }

    // ---- DirectSource -------------------------------------------------------------------------
    private class FakeVt(val code: Int) : VirusTotalApi {
        var calls = 0
        override suspend fun fileReport(sha256: String, key: String): Response<VtResponse> {
            calls++
            return Response.error(code, "".toResponseBody())
        }
    }

    @Test fun `DirectSource clave invalida corta en la primera app`() = runTest {
        val vt = FakeVt(401)
        val out = DirectSource(ReputationRepository(FakeDao(), vt), "mala")
            .lookupAll(listOf(h('a'), h('b'), h('c'))) { _, _ -> }
        assertEquals(1, vt.calls)
        assertTrue(out.values.all { it.error == "key" })
        assertEquals(3, out.size)
    }

    @Test fun `DirectSource 404 es UNKNOWN`() = runTest {
        val out = DirectSource(ReputationRepository(FakeDao(), FakeVt(404)), "k")
            .lookupAll(listOf(h('a'))) { _, _ -> }
        assertEquals(Rep(Verdict.UNKNOWN), out[h('a')])
    }
}
