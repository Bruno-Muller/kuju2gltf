# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

from typing import overload
from typing_extensions import Self
import math

class Vec3f:
    def __init__(self, x:float, y:float, z:float):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self) -> str:
        return f"Vec3f({self.x}, {self.y}, {self.z})"

    def __pow__(self, right:Self) -> Self:
        a = self
        b = right
        return Vec3f(a.x*b.x, a.y*b.y, a.z*b.z)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z)

class Mat3x3f:
    def __init__(self, ax:float, ay:float, az:float, bx:float, by:float, bz:float, cx:float, cy:float, cz:float):
        self.ax = ax
        self.ay = ay
        self.az = az
        self.bx = bx
        self.by = by
        self.bz = bz
        self.cx = cx
        self.cy = cy
        self.cz = cz

    def __str__(self) -> str:
        return f"Mat3x3f({self.ax}, {self.ay}, {self.az}, {self.bx}, {self.by}, {self.bz}, {self.cx}, {self.cy}, {self.cz})"

    @staticmethod
    def diag(ax:float, by:float, cz:float) -> Self:
        return Mat3x3f(ax, 0.0, 0.0, 0.0, by, 0.0, 0.0, 0.0, cz)
    
    @staticmethod
    def zeroes() -> Self:
        return Mat3x3f(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
    @staticmethod
    def identity() -> Self:
        return Mat3x3f(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

    @overload
    def __mul__(self, right: Vec3f) -> Vec3f: ...
        
    @overload
    def __mul__(self, right: Self) -> Self: ...
        
    def __mul__(self, right: Vec3f | Self) -> Vec3f | Self:
        if isinstance(right, Vec3f):
            return Vec3f(self.ax * right.x + self.bx * right.y + self.cx * right.z, self.ay * right.x + self.by * right.y + self.cy * right.z, self.az * right.x + self.bz * right.y + self.cz * right.z)
        if isinstance(right, Mat3x3f):
            #          ax bx cx 
            #          ay by cy
            #          az bz cz
            # ax bx cx 
            # ay by cy
            # az bz cz
            return Mat3x3f(self.ax * right.ax + self.bx * right.ay + self.cx * right.az,
                           self.ay * right.ax + self.by * right.ay + self.cy * right.az,
                           self.az * right.ax + self.bz * right.ay + self.cz * right.az,

                           self.ax * right.bx + self.bx * right.by + self.cx * right.bz,
                           self.ay * right.bx + self.by * right.by + self.cy * right.bz,
                           self.az * right.bx + self.bz * right.by + self.cz * right.bz,

                           self.ax * right.cx + self.bx * right.cy + self.cx * right.cz,
                           self.ay * right.cx + self.by * right.cy + self.cy * right.cz,
                           self.az * right.cx + self.bz * right.cy + self.cz * right.cz

            )

    def transpose(self) -> Self:
        return Mat3x3f(self.ax, self.bx, self.cx, self.ay, self.by, self.cy, self.az, self.bz, self.cz)
    
    def get_trace(self) -> float:
        return self.ax + self.by + self.cz
    
class Transformation:
    def __init__(self, ax:float, ay:float, az:float, bx:float, by:float, bz:float, cx:float, cy:float, cz:float, dx:float, dy:float, dz:float) -> Self:
        self.ax = ax
        self.ay = ay
        self.az = az
        self.bx = bx
        self.by = by
        self.bz = bz
        self.cx = cx
        self.cy = cy
        self.cz = cz
        self.dx = dx
        self.dy = dy
        self.dz = dz
    
    def get_translation(self) -> Vec3f:
        return Vec3f(self.dx, self.dy, self.dz)
    
    def get_rotation(self) -> Mat3x3f:
        return Mat3x3f(self.ax, self.ay, self.az, self.bx, self.by, self.bz, self.cx, self.cy, self.cz)
    
    # def get_scale(self) -> Vec3f: ?????

class Quaternion:
    # https://d3cw3dd2w32x2b.cloudfront.net/wp-content/uploads/2015/01/matrix-to-quat.pdf

    def __init__(self, x:float, y:float, z:float, w:float):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __str__(self) -> str:
        return f"Quaternion({self.x}, {self.y}, {self.z}, {self.w})"
    
    def __add__(self, right: Self) -> Self:
        return Quaternion(self.x+right.x, self.y+right.y, self.z+right.z, self.w+right.w)
    
    def __sub__(self, right: Self) -> Self:
        return Quaternion(self.x-right.x, self.y-right.y, self.z-right.z, self.w-right.w)
    
    def __pow__(self, right: Self) -> Self:
        a = self
        b = right
        return Quaternion(a.x*b.x, a.y*b.y, a.z*b.z, a.w*b.w)

    def __mul__(self, right: Self) -> Self:
        
        # i*i = -1 ; j*j = -1 ; k*k = -1
        # i*j =  k ; j*k =  i ; k*i =  j
        # j*i = -k ; k*j = -i ; i*k = -j
        
        a = self
        b = right
        return Quaternion(a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,  # i
            a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,  # j
            a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,   # k
            a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z  # 1
        )
        
        
        raise Exception("Not Implemented!")

    def __eq__(self, right: Self) -> bool:
        epsilon = 1e-6

        # q_left == q_right
        qe = self - right
        if (abs(qe.x) < epsilon and abs(qe.y) < epsilon and abs(qe.z) < epsilon and abs(qe.w) < epsilon): return True

        # q_left == -q_right
        qe = self + right
        if (abs(qe.x) < epsilon and abs(qe.y) < epsilon and abs(qe.z) < epsilon and abs(qe.w) < epsilon): return True

        return False
        

    def to_matrix(self) -> Mat3x3f:
        # ax = 1 - 2 * (qy * qy + qz * qz)
        # ay = 2 * (qx * qy + qw * qz)
        # az = 2 * (qx * qz - qw * qy)

        # bx = 2 * (qx * qy - qw * qz)
        # by = 1 - 2 * (qx * qx + qz * qz)
        # bz = 2 * (qy * qz + qw * qx)

        # cx = 2 * (qx * qz + qw * qy)
        # cy = 2 * (qy * qz - qw * qx)
        # cz = 1 - 2 * (qx * qx + qy * qy)

        # return (ax, ay, az, bx, by, bz, cx, cy, cz)

        x2 = self.x + self.x
        y2 = self.y + self.y
        z2 = self.z + self.z
        xx = self.x * x2
        xy = self.x * y2
        xz = self.x * z2
        yy = self.y * y2
        yz = self.y * z2
        zz = self.z * z2
        wx = self.w * x2
        wy = self.w * y2
        wz = self.w * z2

        sx = 1 #scale.x
        sy = 1 #scale.y
        sz = 1 #scale.z;

        ax = ( 1 - ( yy + zz ) ) * sx
        ay = ( xy + wz ) * sx
        az = ( xz - wy ) * sx
        # = 0;

        bx = ( xy - wz ) * sy
        by = ( 1 - ( xx + zz ) ) * sy
        bz = ( yz + wx ) * sy
        # = 0;

        cx = ( xz + wy ) * sz
        cy = ( yz - wx ) * sz
        cz = ( 1 - ( xx + yy ) ) * sz
        # = 0

        # = position.x;
        # = position.y;
        # = position.z;
        # = 1;

        return Mat3x3f(ax, ay, az, bx, by, bz, cx, cy, cz)
    
    @staticmethod
    def FromMatrix(matrix: Mat3x3f) -> Self:
        #(ax, ay, az, bx, by, bz, cx, cy, cz) =_transpose(ax, ay, az, bx, by, bz, cx, cy, cz)

        m11 = matrix.ax
        m12 = matrix.bx
        m13 = matrix.cx
        
        m21 = matrix.ay
        m22 = matrix.by
        m23 = matrix.cy
        
        m31 = matrix.az
        m32 = matrix.bz
        m33 = matrix.cz

        trace = m11 + m22 + m33

        if (trace > 0):
            s = 0.5 / math.sqrt(trace + 1.0)

            qw = 0.25 / s
            qx = ( m32 - m23 ) * s
            qy = ( m13 - m31 ) * s
            qz = ( m21 - m12 ) * s

            return Quaternion(qx, qy, qz, qw)

        elif (m11 > m22) and (m11 > m33):

            s = 2.0 * math.sqrt( 1.0 + m11 - m22 - m33 )

            qw = ( m32 - m23 ) / s
            qx = 0.25 * s
            qy = ( m12 + m21 ) / s
            qz = ( m13 + m31 ) / s

            return Quaternion(qx, qy, qz, qw)

        elif ( m22 > m33 ):

            s = 2.0 * math.sqrt( 1.0 + m22 - m11 - m33 )

            qw = ( m13 - m31 ) / s
            qx = ( m12 + m21 ) / s
            qy = 0.25 * s
            qz = ( m23 + m32 ) / s

            return Quaternion(qx, qy, qz, qw)

        else:
            s = 2.0 * math.sqrt( 1.0 + m33 - m11 - m22 )

            qw = ( m21 - m12 ) / s
            qx = ( m13 + m31 ) / s
            qy = ( m23 + m32 ) / s
            qz = 0.25 * s

            return Quaternion(qx, qy, qz, qw)