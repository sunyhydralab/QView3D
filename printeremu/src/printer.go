package src

import (
	"fmt"
)

// Printer struct with associated components as pointers for easy modification
type Printer struct {
	id          int
	device      string
	description string
	hwid        string
	name        string
	status      string
	date        string
	extruder    *Extruder // Pointer to Extruder
	heatbed     *Heatbed  // Pointer to Heatbed
	paused      bool
	units       string // Track units (e.g., "mm" or "inches").
}

// NewPrinter initializes a Printer with given specifications
func NewPrinter(id int, device, description, hwid, name, status, date string, extruder *Extruder, heatbed *Heatbed) *Printer {
	return &Printer{
		id:          id,
		device:      device,
		description: description,
		hwid:        hwid,
		name:        name,
		status:      status,
		date:        date,
		extruder:    extruder,
		heatbed:     heatbed,
		paused:      false,
		units:       "mm", // Default units
	}
}

// Printer methods for managing extruder and heatbed states
func (printer *Printer) SetExtruderTemp(temp float64) {
	printer.extruder.SetExtruderTemp(temp)
}

func (printer *Printer) GetExtruderTemp() float64 {
	return printer.extruder.ExtruderTemp
}

func (printer *Printer) GetExtruder() *Extruder {
	return printer.extruder
}

func (printer *Printer) SetBedTemp(temp float64) {
	printer.heatbed.SetBedTemp(temp)
}

func (printer *Printer) GetBedTemp() float64 {
	return printer.heatbed.Temp
}

func (printer *Printer) SetFanSpeed(speed float64) {
	printer.extruder.SetFanSpeed(speed)
}

func (printer *Printer) GetFanSpeed() float64 {
	return printer.extruder.FanSpeed
}

func (printer *Printer) Pause() {
	printer.paused = true
}

func (printer *Printer) Resume() {
	printer.paused = false
}

func (printer *Printer) String() string {
	return fmt.Sprintf("Printer{Id: %d, Device: %s, Description: %s, Hwid: %s, Name: %s, Status: %s, Date: %s, Extruder: %v, Heatbed: %v}",
		printer.id, printer.device, printer.description, printer.hwid, printer.name, printer.status, printer.date, printer.extruder.String(), printer.heatbed)
}
