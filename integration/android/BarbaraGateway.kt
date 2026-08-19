package barbara.integration

import com.chaquo.python.PyObject
import com.chaquo.python.Python
import org.json.JSONObject

/** Thin Kotlin boundary for the Barbara engine embedded in the APK/AAB. */
class BarbaraGateway(private val python: Python = Python.getInstance()) {
    private val module: PyObject by lazy { python.getModule("barbara.android") }

    fun configure(
        apiKey: String?,
        model: String = "gemini-3.5-flash-lite",
        ragDbPath: String?,
        useGemini: Boolean = true,
    ): JSONObject {
        val raw = module.callAttr(
            "configure_json",
            PyObject.fromJava(apiKey),
            PyObject.fromJava(model),
            PyObject.fromJava(ragDbPath),
            PyObject.fromJava(useGemini),
        ).toString()
        return JSONObject(raw)
    }

    fun newCampaign(campaignId: String, systemId: String): String =
        module.callAttr("new_campaign", campaignId, systemId).toString()

    fun turn(stateJson: String, request: JSONObject): BarbaraTurnEnvelope {
        val raw = module.callAttr("turn", stateJson, request.toString()).toString()
        val envelope = JSONObject(raw)
        return BarbaraTurnEnvelope(
            stateJson = envelope.getString("state"),
            result = envelope.getJSONObject("result"),
        )
    }
}

data class BarbaraTurnEnvelope(
    val stateJson: String,
    val result: JSONObject,
)
