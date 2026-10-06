package com.monocucuy.solucion.data.local

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(entities = [HashCacheEntity::class], version = 1, exportSchema = false)
abstract class AppDb : RoomDatabase() {
    abstract fun hashDao(): HashDao
}
