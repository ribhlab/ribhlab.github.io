package com.ribhlab.rivomx

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import java.text.DateFormat
import java.util.Date
import java.util.Locale

private val teal=Color(0xFF55EBD3)
private val dark=Color(0xFF081722)
private val glass=Color(0xE6102834)

@Composable
fun RivoScreen(
    view:ArCameraView, status:String, readout:Readout, points:List<Projected>,mode:MeasureMode,
    unit:UnitOfLength,history:List<SavedMeasurement>,onMode:(MeasureMode)->Unit,onUnit:(UnitOfLength)->Unit,
    onClear:()->Unit,onSave:()->Unit,onPdf:()->Unit,onRetry:()->Unit
){
    var showHistory by remember { mutableStateOf(false) }
    MaterialTheme {
        Box(Modifier.fillMaxSize().background(dark)){
            AndroidView(factory={view},modifier=Modifier.fillMaxSize())
            Canvas(Modifier.fillMaxSize().pointerInput(view) {
                detectTapGestures { pos -> view.tap(pos.x,pos.y) }
            }){
                val visible=points.map { Offset(it.x,it.y) }
                visible.chunked(2).forEach { pair ->
                    if(pair.size==2) drawLine(teal,pair[0],pair[1],5.dp.toPx(),cap=StrokeCap.Round)
                }
                visible.forEach { point ->
                    drawCircle(Color(0xFF001A22),10.dp.toPx(),point)
                    drawCircle(teal,6.dp.toPx(),point)
                }
                if(visible.isEmpty()) {
                    drawCircle(teal.copy(alpha=.6f),16.dp.toPx(),
                        Offset(size.width/2,size.height/2),style=Stroke(2.dp.toPx()))
                }
            }
            Column(Modifier.fillMaxSize().padding(14.dp),verticalArrangement=Arrangement.SpaceBetween){
                Column {
                    Column(Modifier.fillMaxWidth().background(glass,RoundedCornerShape(18.dp)).padding(15.dp)){
                        Text("RivoMx",fontWeight=FontWeight.Black,fontSize=27.sp,color=Color.White)
                        Text("PRECISION AR MEASUREMENT",fontSize=10.sp,letterSpacing=1.2.sp,color=teal)
                    }
                    Spacer(Modifier.height(8.dp))
                    Text(status,color=Color.White,fontSize=12.sp,
                        modifier=Modifier.background(glass,RoundedCornerShape(10.dp)).padding(10.dp))
                }
                Column(Modifier.fillMaxWidth().background(
                    Brush.verticalGradient(listOf(Color(0xF0102E3C),Color(0xF5081721))),
                    RoundedCornerShape(20.dp)).padding(14.dp)){
                    Text(if(mode==MeasureMode.DISTANCE)"Tap 2 endpoints"
                        else "Tap length endpoints, then width endpoints",color=Color.LightGray,fontSize=12.sp)
                    Row(horizontalArrangement=Arrangement.spacedBy(7.dp)){
                        MeasureMode.entries.forEach { option ->
                            Button(onClick={onMode(option)},modifier=Modifier.weight(1f),
                                colors=ButtonDefaults.buttonColors(
                                    containerColor=if(mode==option)teal else Color(0xFF2A4350),
                                    contentColor=if(mode==option)dark else Color.White)){
                                Text(option.label,fontSize=12.sp)
                            }
                        }
                    }
                    Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween) {
                        Column {
                            Text("LENGTH",color=Color.LightGray,fontSize=11.sp)
                            Text(unit.format(readout.length),color=teal,fontSize=26.sp,fontWeight=FontWeight.Bold)
                        }
                        if(mode==MeasureMode.RECTANGLE) Column {
                            Text("WIDTH",color=Color.LightGray,fontSize=11.sp)
                            Text(unit.format(readout.width),color=teal,fontSize=26.sp,fontWeight=FontWeight.Bold)
                        }
                    }
                    val area=MeasureMath.area(readout.length,readout.width)
                    if(mode==MeasureMode.RECTANGLE && area!=null)
                        Text(String.format(Locale.US,"Approx. area: %.3f m²",area),color=Color.White,fontSize=13.sp)
                    Text(readout.hits.toString()+"/"+mode.points+" points • "+
                        (readout.source.ifBlank{"Awaiting AR hits"}),color=Color.LightGray,fontSize=11.sp)
                    Row(horizontalArrangement=Arrangement.spacedBy(5.dp)){
                        UnitOfLength.entries.forEach { option ->
                            TextButton(onClick={onUnit(option)},modifier=Modifier.weight(1f)
                                .border(if(unit==option)1.dp else 0.dp,teal,RoundedCornerShape(8.dp))){
                                Text(option.label,color=if(unit==option)teal else Color.LightGray)
                            }
                        }
                    }
                    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
                        OutlinedButton(onClick=onClear,modifier=Modifier.weight(1f)){Text("Reset",color=Color.White)}
                        Button(onClick=onSave,modifier=Modifier.weight(1f),
                            colors=ButtonDefaults.buttonColors(containerColor=teal,contentColor=dark)){
                            Text("Save")
                        }
                    }
                    Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){
                        TextButton(onClick={showHistory=true}){Text("History ("+history.size+")",color=teal)}
                        TextButton(onClick=onPdf){Text("Export PDF",color=teal)}
                        TextButton(onClick=onRetry){Text("Camera",color=Color.White)}
                    }
                    Text("Estimated AR distances; not certified for precision work.",
                        color=Color.LightGray,fontSize=10.sp)
                }
            }
            if(showHistory) AlertDialog(onDismissRequest={showHistory=false},title={Text("Saved measurements")},
                text={
                    if(history.isEmpty())Text("No measurements yet")
                    else LazyColumn(Modifier.height(330.dp)){
                        items(history){ item ->
                            Column(Modifier.fillMaxWidth().padding(vertical=7.dp)){
                                Text(DateFormat.getDateTimeInstance().format(Date(item.id)),fontSize=11.sp)
                                Text(unit.format(item.length) +
                                    (item.width?.let{" × "+unit.format(it)}?:""),fontWeight=FontWeight.Bold)
                                Text(item.source,fontSize=11.sp)
                            }
                        }
                    }
                },
                confirmButton={TextButton(onClick={showHistory=false}){Text("Close")}})
        }
    }
}
