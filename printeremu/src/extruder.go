package src

import (
	"fmt"
)

// Vector3 struct to represent a 3D position
type Vector3 struct {
	X float64
	Y float64
	Z float64
}

// Extruder struct to handle extruder settings, including temperature and fan speed.
type Extruder struct {
	Position            Vector3
	FanSpeed            float64
	ExtruderTemp        float64
	TargetTemp          float64 // Desired temperature for the extruder.
	AbsolutePositioning bool
	MaxZHeight          float64 // Maximum height of the extruder
}

// Heatbed struct to handle heatbed temperature.
type Heatbed struct {
	Temp       float64
	TargetTemp float64 // Desired temperature for the heatbed.
	Heating    bool    // Indicates if the bed is currently heating.
	Width      float64
	Length     float64
}

// NewExtruder creates a new Extruder with specified initial values.
func NewExtruder(position Vector3, extruderTemp, targetTemp, fanSpeed float64) *Extruder {
	return &Extruder{
		Position:            position,
		ExtruderTemp:        extruderTemp,
		TargetTemp:          targetTemp,
		FanSpeed:            fanSpeed,
		AbsolutePositioning: true, // Default positioning mode
	}
}

// NewHeatbed creates a new Heatbed with specified initial values.
func NewHeatbed(temp, targetTemp float64) *Heatbed {
	return &Heatbed{
		Temp:       temp,
		TargetTemp: targetTemp,
		Heating:    false, // Default heating state
	}
}

// Extruder methods to set temperature and fan speed
func (extruder *Extruder) SetExtruderTemp(temp float64) {
	extruder.ExtruderTemp = temp
}

// SetFanSpeed sets the fan speed for Extruder
func (extruder *Extruder) SetFanSpeed(speed float64) {
	extruder.FanSpeed = speed
}

// SetBedTemp sets the target temperature for the heatbed and starts heating
func (heatbed *Heatbed) SetBedTemp(temp float64) {
	heatbed.TargetTemp = temp
	heatbed.Heating = true // Start heating when a target temp is set
}

// String method to display Extruder details in a formatted way
func (extruder *Extruder) String() string {
	return fmt.Sprintf("{Position: %v, ExtruderTemp: %.2f°C, TargetTemp: %.2f°C, FanSpeed: %.2f}", extruder.Position, extruder.ExtruderTemp, extruder.TargetTemp, extruder.FanSpeed)
}

// String method to display Heatbed details in a formatted way
func (heatbed *Heatbed) String() string {
	return fmt.Sprintf("{Temp: %.2f°C, TargetTemp: %.2f°C, Heating: %t}", heatbed.Temp, heatbed.TargetTemp, heatbed.Heating)
}
