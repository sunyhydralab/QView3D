package src

import (
	"fmt"
	"time"
)

// Printer struct with associated components as pointers for easy modification
type Printer struct {
	id             int
	device         string
	description    string
	hwid           string
	name           string
	status         string
	date           string
	extruder       *Extruder   // Pointer to Extruder
	heatbed        *Heatbed    // Pointer to Heatbed
	paused         bool
	units          string      // Track units (e.g., "mm" or "inches")
	keepAliveTime  time.Time   // Timestamp to track keepalive signals
	acceleration   float64     // Acceleration setting for movement
	progress       int         // Progress indicator (percentage) for print jobs
}

// NewPrinter initializes a Printer with given specifications
func NewPrinter(id int, device, description, hwid, name, status, date string, extruder *Extruder, heatbed *Heatbed) *Printer {
	return &Printer{
		id:             id,
		device:         device,
		description:    description,
		hwid:           hwid,
		name:           name,
		status:         status,
		date:           date,
		extruder:       extruder,
		heatbed:        heatbed,
		paused:         false,
		units:          "mm",         // Default units
		keepAliveTime:  time.Now(),   // Initialize with current time
		acceleration:   0.0,          // Default acceleration
		progress:       0,            // Default progress percentage
	}
}

// SetExtruderTemp sets the extruder temperature
func (printer *Printer) SetExtruderTemp(temp float64) {
	printer.extruder.SetExtruderTemp(temp)
}

// GetExtruderTemp gets the extruder temperature
func (printer *Printer) GetExtruderTemp() float64 {
	return printer.extruder.ExtruderTemp
}

// SetBedTemp sets the target bed temperature and begins heating
func (printer *Printer) SetBedTemp(temp float64) {
	printer.heatbed.SetBedTemp(temp)
}

// GetBedTemp gets the current bed temperature
func (printer *Printer) GetBedTemp() float64 {
	return printer.heatbed.Temp
}

// UpdateBedTemperature updates the current temperature of the bed
func (printer *Printer) UpdateBedTemperature(currentTemp float64) {
	printer.heatbed.Temp = currentTemp
	if printer.heatbed.Temp >= printer.heatbed.TargetTemp {
		printer.heatbed.Heating = false
	}
}

// SetFanSpeed sets the fan speed on the extruder
func (printer *Printer) SetFanSpeed(speed float64) {
	printer.extruder.SetFanSpeed(speed)
}

// GetFanSpeed gets the current fan speed on the extruder
func (printer *Printer) GetFanSpeed() float64 {
	return printer.extruder.FanSpeed
}

// Pause pauses the printer
func (printer *Printer) Pause() {
	printer.paused = true
}

// Resume resumes the printer operation
func (printer *Printer) Resume() {
	printer.paused = false
}

// String provides a formatted string representation of the Printer state
func (printer *Printer) String() string {
	return fmt.Sprintf("Printer{Id: %d, Device: %s, Description: %s, Hwid: %s, Name: %s, Status: %s, Date: %s, Extruder: %v, Heatbed: %v, Acceleration: %.2f, Progress: %d%%, KeepAliveTime: %v}",
		printer.id, printer.device, printer.description, printer.hwid, printer.name, printer.status, printer.date, printer.extruder.String(), printer.heatbed.String(), printer.acceleration, printer.progress, printer.keepAliveTime)
}
