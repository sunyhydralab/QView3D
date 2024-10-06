import math

class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    # String representation for printing
    def __repr__(self):
        return f"Vector3({self.x}, {self.y}, {self.z})"

    # Adding two vectors
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    # Subtracting two vectors
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    # Scalar multiplication (dot product)
    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):  # scalar multiplication
            return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
        raise TypeError(f"Multiplication with type {type(scalar)} not supported")

    # Vector multiplication (cross product)
    def cross(self, other):
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    # Dot product of two vectors
    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    # Magnitude (length) of the vector
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    # Normalized vector (unit vector)
    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize a zero vector")
        return Vector3(self.x / mag, self.y / mag, self.z / mag)

    # Comparison of vectors
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z
