package com.ribhlab.rivomx

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MeasureMathTest {
    @Test fun distance3d() {
        assertEquals(13.0,MeasureMath.distance(Point3(0.0,0.0,0.0),Point3(3.0,4.0,12.0)),0.0000001)
    }
    @Test fun area() {
        assertEquals(6.0,MeasureMath.area(2.0,3.0)!!,0.0000001)
        assertNull(MeasureMath.area(2.0,null))
    }
    @Test fun unit() {
        assertEquals("100.0 cm",UnitOfLength.CM.format(1.0))
    }
}
