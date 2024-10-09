from abc import ABCMeta
from typing_extensions import Buffer
from Classes.Vector3 import Vector3



class usesMarlinGcode(metaclass=ABCMeta):
    home: Buffer = "G28\n".encode("utf-8")
    pause: Buffer = "M601\n".encode("utf-8") + "M113 S1\n".encode("utf-8")
    resume: Buffer = "M602\n".encode("utf-8")
    cancel: Buffer = "M112\n".encode("utf-8")
    status: Buffer = "M115\n".encode("utf-8")
    disconnect: Buffer = "M155 S0\n".encode("utf-8") + "M84\n".encode("utf-8")
    connect: Buffer = "M155 S5 C7\n".encode("utf-8")

    @staticmethod
    def goTo(loc: Vector3) -> Buffer:
        return f"G1 X{loc.x} Y{loc.y} Z{loc.z}\n".encode("utf-8")