package com.ribhlab.rivomx

import android.graphics.Color
import android.graphics.Paint
import android.graphics.pdf.PdfDocument
import java.io.OutputStream
import java.text.DateFormat
import java.util.Date
import java.util.Locale

object PdfExport {
    fun write(output:OutputStream, records:List<SavedMeasurement>){
        val document=PdfDocument()
        try {
            val paint=Paint(Paint.ANTI_ALIAS_FLAG)
            val pages=records.chunked(25).ifEmpty { listOf(emptyList()) }
            pages.forEachIndexed { n, group ->
                val page=document.startPage(PdfDocument.PageInfo.Builder(595,842,n+1).create())
                val canvas=page.canvas
                canvas.drawColor(Color.WHITE)
                paint.color=Color.rgb(11,45,57)
                paint.textSize=24f
                paint.isFakeBoldText=true
                canvas.drawText("RivoMx measurements",32f,52f,paint)
                paint.isFakeBoldText=false
                paint.textSize=11f
                canvas.drawText("Estimated AR results; verify with a physical ruler.",32f,76f,paint)
                paint.textSize=12f
                group.forEachIndexed { i,item ->
                    val date=DateFormat.getDateTimeInstance().format(Date(item.id))
                    val value=String.format(Locale.US,"L %.3f m",item.length) +
                        (item.width?.let { String.format(Locale.US,"  W %.3f m",it) }?:"")
                    canvas.drawText(date+"   "+value,32f,113f+26*i,paint)
                }
                document.finishPage(page)
            }
            document.writeTo(output)
        } finally { document.close() }
    }
}
