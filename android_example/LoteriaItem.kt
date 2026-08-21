package com.example.app.model

import com.google.gson.annotations.SerializedName

/**
 * Modelo de datos Kotlin para consumir la API de Loterías RD.
 * Endpoint recomendado para Android: GET https://tu-app.onrender.com/api/loterias
 */
data class LoteriaItem(
    @SerializedName("id")
    val id: String?,

    @SerializedName("sorteo_slug")
    val sorteoSlug: String,

    @SerializedName("sorteo_nombre")
    val sorteoNombre: String,

    @SerializedName("compania")
    val compania: String,

    @SerializedName("fecha")
    val fecha: String,

    @SerializedName("hora")
    val hora: String,

    @SerializedName("numeros")
    val numeros: List<Int>,

    @SerializedName("primero")
    val primero: String,

    @SerializedName("segundo")
    val segundo: String,

    @SerializedName("tercero")
    val tercero: String
)

/**
 * Interfaz Retrofit 2 para Android
 */
/*
interface LoteriaApiService {

    @GET("api/loterias")
    suspend fun getLoterias(): List<LoteriaItem>

    @GET("api/sorteo/{slug}")
    suspend fun getHistorialSorteo(
        @Path("slug") slug: String,
        @Query("raw") raw: Boolean = true
    ): List<LoteriaItem>
}
*/
