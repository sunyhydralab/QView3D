import re
class LocationResponse:
    def __init__(self, response: str):
        loc = [item for item in re.split(r'X:| Y:| Z:| E:| Count X:|\n', response) if item and item.strip()]
        self.x = float(loc[0])
        self.y = float(loc[1])
        self.z = float(loc[2])
        self.e = float(loc[3])
        self.count_x = int(loc[4])
        self.count_y = int(loc[5])
        self.count_z = int(loc[6])