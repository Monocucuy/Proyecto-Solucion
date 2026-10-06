package com.monocucuy.solucion.data.local

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query

@Entity(tableName = "hash_cache")
data class HashCacheEntity(
    @PrimaryKey val sha256: String,
    val found: Boolean,
    val malicious: Int,
    val suspicious: Int,
    val checkedAt: Long
)

@Dao
interface HashDao {
    @Query("SELECT * FROM hash_cache WHERE sha256 = :sha LIMIT 1")
    suspend fun get(sha: String): HashCacheEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(e: HashCacheEntity)
}
