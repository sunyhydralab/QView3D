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

func (e *Extruder) SetExtruderTemp(temp float64) {
	e.ExtruderTemp = temp
}

func (e *Extruder) SetBedTemp(temp float64) {
	e.BedTemp = temp
}

func (e *Extruder) SetFanSpeed(speed float64) {
	e.FanSpeed = speed
}

func (e *Extruder) String() string {
	return fmt.Sprintf("{Position: %v, ExtruderTemp: %vc, BedTemp: %vc, FanSpeed: %v}", e.Position, e.ExtruderTemp, e.BedTemp, e.FanSpeed)
}