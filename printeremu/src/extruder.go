package src

import (
	"fmt"
)

type Vector3 struct {
	X float64
	Y float64
	Z float64
}

type Extruder struct {
	Position      Vector3  
	ExtruderTemp  float64
	BedTemp       float64
	FanSpeed      float64
}

func NewExtruder(position Vector3, extruderTemp, bedTemp, fanSpeed float64) *Extruder {
	return &Extruder{
		Position:      position,
		ExtruderTemp:  extruderTemp,
		BedTemp:       bedTemp,
		FanSpeed:      fanSpeed,
	}
}

func (extruder *Extruder) SetExtruderTemp(temp float64) {
	extruder.ExtruderTemp = temp
}

func (extruder *Extruder) SetBedTemp(temp float64) {
	extruder.BedTemp = temp
}

func (extruder *Extruder) SetFanSpeed(speed float64) {
	extruder.FanSpeed = speed
}

func (extruder *Extruder) String() string {
	return fmt.Sprintf("{Position: %v, ExtruderTemp: %vc, BedTemp: %vc, FanSpeed: %v}", extruder.Position, extruder.ExtruderTemp, extruder.BedTemp, extruder.FanSpeed)
}